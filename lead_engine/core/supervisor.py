import asyncio
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from lead_engine.db.models import SessionLocal, Job, AgentLog, Lead
from lead_engine.tools.google_sheets import GoogleSheetsTool
import logging, os

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """
    The central brain of the system.
    Coordinates other agents, manages job lifecycle, and handles retries.
    """
    _active_jobs: Dict[int, asyncio.Event] = {}
    
    def __init__(self):
        self.sheets = GoogleSheetsTool()

    async def create_job(self, user_intent: str, campaign_id: Optional[int] = None, max_leads: int = 100, sheet_id: str = None, user: str = "system") -> int:
        """
        Creates a new scraping job based on user intent.
        """
        db = SessionLocal() # Keep this session short
        try:
            from lead_engine.db.models import Campaign
            campaign = db.query(Campaign).get(campaign_id) if campaign_id else None
            
            job_name = f"{campaign.name if campaign else ''} - {user_intent[:30]}"
            job = Job(
                name=job_name,
                status='processing_intent',
                max_leads=max_leads,
                sheet_id=sheet_id,
                campaign_id=campaign_id
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            # Start the supervisor loop for this job
            cancel_event = asyncio.Event()
            self._active_jobs[job.id] = cancel_event
            asyncio.create_task(self.run_job_loop(job.id, user_intent, cancel_event, max_leads, user, campaign_id))
            
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
    
    async def run_job_loop(self, job_id: int, user_intent: str, cancel_event: asyncio.Event, max_leads: int, user: str, campaign_id: Optional[int] = None):
        """
        The main loop for a job. Replaced procedural logic with CrewAI orchestration.
        """
        db = SessionLocal()
        try:
            from lead_engine.core.crew import LeadGenerationCrew
            self.log_event(job_id, "Supervisor", f"Starting CrewAI job loop for intent: {user_intent}", db=db)
            
            job = db.query(Job).get(job_id)
            job.status = 'scraping'
            db.commit()
            
            # 1. Orchestration Phase via CrewAI
            if cancel_event.is_set(): return
            
            # Load campaign config if any
            from lead_engine.db.models import Campaign
            campaign_config = {}
            if campaign_id:
                campaign = db.query(Campaign).get(campaign_id)
                if campaign and campaign.config:
                    campaign_config = campaign.config
                    self.log_event(job_id, "Supervisor", f"Using custom config for campaign: {campaign.name}", db=db)
            
            # Initialize Crew with overrides
            crew_instance = LeadGenerationCrew(config_overrides=campaign_config).crew()
            
            # Kickoff is synchronous. Run in thread to not block the main async loop
            result = await asyncio.to_thread(crew_instance.kickoff, inputs={'user_intent': user_intent})
            
            self.log_event(job_id, "Supervisor", "CrewAI execution finished. Extracting leads...", db=db)
            
            if cancel_event.is_set(): return
            
            # 2. Persistence Phase
            # result.pydantic contains the FinalLeadList since the final task specified output_pydantic
            final_output = result.pydantic
            
            if final_output and hasattr(final_output, 'leads'):
                for sc_lead in final_output.leads:
                    if cancel_event.is_set():
                        self.log_event(job_id, "Supervisor", "Job stopping due to user cancellation.", db=db)
                        break
                    
                    if job.leads_found >= job.max_leads:
                        self.log_event(job_id, "Supervisor", f"Reached lead limit ({job.max_leads}). Stopping.", db=db)
                        break
                        
                    # Check for duplicates
                    existing = db.query(Lead).filter(Lead.email == sc_lead.email).first() if sc_lead.email else None
                    if not existing:
                        new_lead = Lead(
                            name=sc_lead.name,
                            company=sc_lead.company,
                            email=sc_lead.email,
                            linkedin_url=sc_lead.linkedin_url,
                            source_url=sc_lead.source_url,
                            score=sc_lead.score,
                            vetting_status=sc_lead.vetting_status,
                            job_id=job_id,
                            campaign_id=campaign_id,
                            tech_stack=sc_lead.tech_stack,
                            hiring_signal=str(sc_lead.hiring_signal) if sc_lead.hiring_signal else None
                        )
                        db.add(new_lead)
                        job.leads_found += 1
                        db.commit()
            
            job.status = 'completed' if not cancel_event.is_set() else 'stopped'
            db.commit()
            
            # 3. Auto-Sync to Google Sheets
            target_sheet = job.sheet_id or os.getenv("GOOGLE_SHEET_ID")
            if job.status in ['completed', 'stopped'] and os.getenv("AUTO_SYNC_TO_SHEETS") == "true" and target_sheet:
                self.log_event(job_id, "Supervisor", "Starting auto-sync to Google Sheets.", db=db)
                high_leads = db.query(Lead).filter(Lead.job_id == job_id, Lead.vetting_status == 'good').all()
                for hl in high_leads:
                    try:
                        await asyncio.to_thread(self.sheets.sync_lead, hl, override_sheet_id=target_sheet, user=f"system_job_{job_id}")
                    except Exception as e:
                        self.log_event(job_id, "GoogleSheets", f"Failed to auto-sync lead {hl.id}: {e}", level="WARNING", db=db)
            
            self.log_event(job_id, "Supervisor", f"Job finished. {job.status.upper()}. Total leads: {job.leads_found}", db=db)

        except Exception as e:
            logger.error(f"Critical error in job {job_id}: {e}")
            self.log_event(job_id, "Supervisor", f"Job failed due to critical error: {e}", level="ERROR", db=db)
            job = db.query(Job).get(job_id)
            if job:
                job.status = 'failed'
                db.commit()
        finally:
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]
            db.close()


    def log_event(self, job_id: int, agent_name: str, message: str, level: str = "INFO", db: Optional[Session] = None):
        """
        Persists agent activities to the database.
        Can use an existing session or create a new one.
        """
        close_db_after = False
        if db is None:
            db = SessionLocal()
            close_db_after = True
        
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
            if close_db_after:
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
