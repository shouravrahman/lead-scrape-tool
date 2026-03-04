import asyncio
import logging
import concurrent.futures
from typing import Dict, Any, List
from lead_engine.agents.scraper_pool import FirecrawlScraper
from lead_engine.db.models import Lead

logger = logging.getLogger(__name__)

class EnrichmentAgent:
    """
    Deep enrichment agent. 
    Detects tech stacks, hiring signals, and generates lead contact patterns.
    """
    
    def __init__(self):
        self.firecrawl = FirecrawlScraper()

    async def enrich(self, lead: Lead):
        """
        Dives deep into the company website to extract tech and hiring signals.
        """
        if not lead.source_url:
            return
            
        try:
            # 1. Scrape the URL
            raw_content = await self.firecrawl.run(lead.source_url)
            markdown = raw_content.get('markdown', '')
            
            # 2. Extract Tech Stack
            lead.tech_stack = self._detect_tech_stack(markdown)
            
            # 3. Detect Hiring Signal
            lead.hiring_signal = self._detect_hiring_signals(markdown)
            
            # 4. Generate Email Patterns if missing
            if not lead.email:
                lead.email = self._generate_email_pattern(lead)
                
            logger.info(f"Enriched {lead.name}: Tech={lead.tech_stack}, Hiring={lead.hiring_signal is not None}")
        except Exception as e:
            logger.error(f"Enrichment error for {lead.name}: {e}")

    def _detect_tech_stack(self, text: str) -> List[str]:
        stack = []
        keywords = {
            "Next.js": ["next.js", "nextjs"],
            "React": ["react"],
            "HubSpot": ["hubspot"],
            "Salesforce": ["salesforce"],
            "TypeScript": ["typescript"],
            "Tailwind": ["tailwind"],
            "Supabase": ["supabase"]
        }
        text_lower = text.lower()
        for tech, keys in keywords.items():
            if any(k in text_lower for k in keys):
                stack.append(tech)
        return list(set(stack))

    def _detect_hiring_signals(self, text: str) -> str:
        hiring_keywords = ["hiring", "careers", "join the team", "open roles", "we are looking for"]
        text_lower = text.lower()
        for k in hiring_keywords:
            if k in text_lower:
                # Find the context
                idx = text_lower.find(k)
                return text[max(0, idx-50):min(len(text), idx+100)].strip()
        return None

    def _generate_email_pattern(self, lead: Lead) -> str:
        """
        Skeleton for email pattern generator.
        Gathers domain and name to guess common patterns.
        """
        if not lead.name or not lead.company or " " not in lead.name:
            return None
            
        domain = lead.source_url.split("//")[-1].split("/")[0].replace("www.", "")
        first, last = lead.name.split(" ", 1)
        first, last = first.lower(), last.lower()
        
        # Priority pattern: first@domain
        # Note: In production, we'd use a validator here
        return f"{first}@{domain} (Estimated)"
