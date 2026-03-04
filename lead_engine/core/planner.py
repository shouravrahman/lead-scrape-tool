import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from lead_engine.core.key_manager import key_manager

load_dotenv()
logger = logging.getLogger(__name__)

class PlannerAgent:
    """
    LLM-powered agent that translates user intent into elite search strategies.
    Targets "Goldmine" sources like Product Hunt, Indie Hackers, and Hiring Boards.
    """
    
    def __init__(self):
        pass

    def _get_client(self):
        api_key = key_manager.get_key("openrouter") or key_manager.get_key("openai") or "ollama"
        base_url = os.getenv("OLLAMA_BASE_URL")
        
        if not base_url and key_manager.get_key("openrouter"):
            base_url = "https://openrouter.ai/api/v1"
            
        if api_key:
            return OpenAI(api_key=api_key, base_url=base_url)
        return None

    async def generate_queries(self, intent: str) -> List[str]:
        """
        Generates advanced search queries (Google Dorks) categorized by signal strength.
        """
        client = self._get_client()
        if not client:
            # High-yield fallback dorks
            return [
                f'site:producthunt.com "Maker" "{intent}"',
                f'site:indiehackers.com "launched" "{intent}"',
                f'site:wellfound.com/jobs "hiring" "{intent}"',
                f'site:clutch.co "owner" "{intent}"',
                f'site:linkedin.com/in/ "founder" "{intent}" active'
            ]
            
        system_prompt = """
        You are an Elite Lead Generation Strategist. 
        Your goal is to generate 8-10 highly effective Google Dorks to find SaaS founders, high-level executives, or hiring managers.
        
        Target these categories:
        1. LAUNCH DISCOVERY: Product Hunt, Indie Hackers, BetaList, Hacker News (Show HN).
        2. HIRING SIGNALS: Wellfound (AngelList), Indeed, Glassdoor.
        3. AGENCY DISCOVERY: Clutch, GoodFirms.
        4. SOCIAL INTELLIGENCE: LinkedIn (Public), Twitter/X bios, GitHub Orgs.
        
        Operators to use: site:, intitle:, inurl:, "exact match".
        
        Return ONLY a JSON object with:
        {
          "queries": ["query1", "query2", ...],
          "strategy": "brief explanation of the mix"
        }
        """
        
        try:
            model = os.getenv("PLANNER_MODEL", "google/gemini-flash-1.5-free")
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Intent: {intent}. Generate a mix of launch discovery and hiring signals."}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            queries = data.get("queries", [])
            logger.info(f"Planner generated {len(queries)} elite dorks across categories.")
            return queries
        except Exception as e:
            logger.error(f"LLM Planning failed: {e}")
            return [intent]

    async def get_strategy(self, intent: str) -> Dict[str, Any]:
        return {
            "queries": await self.generate_queries(intent),
            "priority_sources": ["Product Hunt", "Indie Hackers", "Wellfound", "Clutch"]
        }
