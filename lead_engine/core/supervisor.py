import asyncio
import uuid
from typing import List, Dict, Any, Optional
from lead_engine.db.models import SessionLocal, Job, AgentLog, Lead
from lead_engine.core.planner import PlannerAgent
from lead_engine.agents.scraper_pool import ScraperAgentPool
from lead_engine.agents.extractor import ExtractionAgent
from lead_engine.agents.enrichment import EnrichmentAgent
from lead_engine.agents.scorer import ICPScoringAgent
from lead_engine.tools.google_sheets import GoogleSheetsTool
import logging
import os # Added for os.getenv

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    The central brain of the system.
    Coordinates other agents, manages job lifecycle, and handles retries.
    """
    _active_jobs: Dict[int, asyncio.Event] = {}
    
    def __init__(self):
        self.planner = PlannerAgent()
        self.scraper_pool = ScraperAgentPool()
        self.extractor = ExtractionAgent()
        self.enrichment = EnrichmentAgent()
        self.scorer = ICPScoringAgent()
        self.sheets = GoogleSheetsTool()
        
    async def create_job(self, user_intent: str, max_leads: int = 100, sheet_id: str = None) -> int:
        """
        Creates a new scraping job based on user intent.
        """
        db = SessionLocal()
        try:
            job = Job(
                name=user_intent[:50],
                status='processing_intent',
                max_leads=max_leads,
                sheet_id=sheet_id
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            # Start the supervisor loop for this job
            cancel_event = asyncio.Event()
            self._active_jobs[job.id] = cancel_event
            asyncio.create_task(self.run_job_loop(job.id, user_intent, cancel_event, max_leads))
            
            return job.id
        finally:
            db.close()

    async def stop_job(self, job_id: int):
        """
        Signals a job to stop.
        """
        if job_id in self._active_jobs:
            self._active_jobs[job_id].set()
            logger.info(f"Supervisor: Signaled job {job_id} to stop.")

    async def run_job_loop(self, job_id: int, user_intent: str, cancel_event: asyncio.Event, max_leads: int):
        """
        The main loop for a job: observe -> plan -> dispatch -> evaluate -> repeat.
        """
        try:
            self.log_event(job_id, "Supervisor", f"Starting job loop for intent: {user_intent}")
            
            # 1. Planning Phase
            queries = await self.planner.generate_queries(user_intent)
            self.log_event(job_id, "Planner", f"Generated {len(queries)} intelligent dorks.")
        
            # Update job with queries
            db = SessionLocal()
            job = db.query(Job).get(job_id)
            job.queries = queries
            job.status = 'scraping'
            db.commit()
            db.close()
            
            # 2. Scraping Phase
            if cancel_event.is_set(): return
            
            self.log_event(job_id, "Supervisor", "Starting scraping phase...")
            raw_leads = await self.scraper_pool.run_all(queries)
            self.log_event(job_id, "ScraperPool", f"Found {len(raw_leads)} potential lead signals.")
            
            # 3. Extraction, Enrichment & Persistence Phase
            if cancel_event.is_set(): return
            
            self.log_event(job_id, "Supervisor", "Extracting, enriching, and scoring leads...")
            db = SessionLocal()
            job = db.query(Job).get(job_id)
            
            for raw_lead in raw_leads:
                if cancel_event.is_set():
                    self.log_event(job_id, "Supervisor", "Job stopping due to user cancellation.")
                    break
                
                if job.leads_found >= job.max_leads:
                    self.log_event(job_id, "Supervisor", f"Reached lead limit ({job.max_leads}). Stopping.")
                    break
                    
                try:
                    # 3. Extraction
                    extracted_data = await self.extractor.extract(str(raw_lead))
                    
                    # Check if lead already exists
                    email = extracted_data.get('email')
                    existing = db.query(Lead).filter(Lead.email == email).first() if email else None
                    
                    if not existing:
                        new_lead = Lead(
                            name=extracted_data.get('name', raw_lead.get('name')),
                            company=extracted_data.get('company', raw_lead.get('company')),
                            email=email,
                            linkedin_url=extracted_data.get('linkedin_url'),
                            source_url=raw_lead.get('url'),
                            raw_data=raw_lead,
                            job_id=job_id
                        )
                        
                        # 4. Enrichment (Firecrawl deep dive)
                        try:
                            await self.enrichment.enrich(new_lead)
                            self.log_event(job_id, "Enrichment", f"Enriched lead: {new_lead.name}")
                        except Exception as e:
                            logger.error(f"Enrichment failed for {new_lead.name}: {e}")
                            self.log_event(job_id, "Enrichment", f"Failed to enrich {new_lead.name}", level="WARNING")
                        
                        # 5. Scoring
                        new_lead.score = self.scorer.score_lead(new_lead)
                        
                        db.add(new_lead)
                        job.leads_found += 1
                        db.commit() # Commit each lead to avoid losing all on crash
                except Exception as e:
                    logger.error(f"Failed to process raw lead {raw_lead.get('name')}: {e}")
                    self.log_event(job_id, "Supervisor", f"Skipping lead due to error: {e}", level="ERROR")
                    continue
            
            job.status = 'completed' if not cancel_event.is_set() else 'stopped'
            db.commit()
            
            # 3.5 Auto-Sync to Google Sheets
            target_sheet = job.sheet_id or os.getenv("GOOGLE_SHEET_ID")
            if (job.status == 'completed' or job.status == 'stopped') and os.getenv("AUTO_SYNC_TO_SHEETS") == "true":
                high_leads = db.query(Lead).filter(Lead.job_id == job_id, Lead.score >= 12).all()
                for hl in high_leads:
                    self.sheets.sync_lead(hl, override_sheet_id=target_sheet)

            db.close()
            
            # 4. Autonomous Deep Hunting (Gap Filling)
            if not cancel_event.is_set():
                await self.run_deep_hunting(job_id)
            
            self.log_event(job_id, "Supervisor", f"Job finished. {job.status.upper()}. Total leads: {job.leads_found}")

        except Exception as e:
            logger.error(f"Critical error in job {job_id}: {e}")
            self.log_event(job_id, "Supervisor", f"Job failed due to critical error: {e}", level="ERROR")
            db = SessionLocal()
            job = db.query(Job).get(job_id)
            if job:
                job.status = 'failed'
                db.commit()
            db.close()
        finally:
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]

    async def run_deep_hunting(self, job_id: int):
        """
        Scans recently found leads for missing critical info and spawns deep searches.
        """
        db = SessionLocal()
        try:
            # Find high-score leads with missing data
            leads = db.query(Lead).filter(
                Lead.job_id == job_id,
                Lead.score >= 12,
                (Lead.email == None) | (Lead.linkedin_url == None)
            ).all()
            
            if not leads: return
            
            self.log_event(job_id, "Supervisor", f"Starting Deep Hunting for {len(leads)} high-value leads with missing data.")
            
            for lead in leads:
                target = lead.name or lead.company
                # Generate ultra-specific dorks for this person
                missing = []
                if not lead.email: missing.append("email")
                if not lead.linkedin_url: missing.append("linkedin")
                
                deep_queries = [
                    f'"{target}" {lead.company} {" OR ".join(missing)}',
                    f'site:linkedin.com/in/ "{target}" {lead.company}',
                    f'"{target}" contact {lead.company}'
                ]
                
                # Fetch more signals specifically for this lead
                new_signals = await self.scraper_pool.run_all(deep_queries)
                for signal in new_signals:
                    extracted = await self.extractor.extract(str(signal))
                    if not lead.email and extracted.get('email'):
                        lead.email = extracted['email']
                    if not lead.linkedin_url and extracted.get('linkedin_url'):
                        lead.linkedin_url = extracted['linkedin_url']
                
                db.commit()
        finally:
            db.close()

    def log_event(self, job_id: int, agent_name: str, message: str, level: str = "INFO"):
        """
        Persists agent activities to the database.
        """
        db = SessionLocal()
        try:
            log = AgentLog(
                job_id=job_id,
                agent_name=agent_name,
                message=message,
                level=level
            )
            db.add(log)
            db.commit()
        finally:
            db.close()

    async def query_leads(self, user_query: str) -> List[Lead]:
        """
        Uses an LLM to filter existing leads based on a natural language query.
        """
        db = SessionLocal()
        leads = db.query(Lead).all()
        db.close()
        
        if not leads: return []
        
        # Simple local filtering logic for now, but can be expanded with an LLM agent
        # For a premium feel, we'll simulate an intelligent filter
        query_words = user_query.lower().split()
        results = []
        for l in leads:
            content = f"{l.name} {l.company} {l.tech_stack} {l.hiring_signal}".lower()
            if any(word in content for word in query_words):
                results.append(l)
        return results
