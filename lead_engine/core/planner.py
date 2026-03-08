import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from lead_engine.core.key_manager import key_manager

load_dotenv()
logger = logging.getLogger(__name__)

# List of free/low-cost models to rotate through on OpenRouter
# Ordered from best/most capable to least.
FREE_MODELS = [
    "google/gemini-2.0-pro-exp-02-05:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free"
]

class PlannerAgent:
    """
    LLM-powered agent that translates user intent into elite search strategies.
    Targets "Goldmine" sources like Product Hunt, Indie Hackers, and Hiring Boards.
    """
    
    def __init__(self):
        pass

    def _get_client(self):
        api_key = key_manager.get_key("openrouter") or "ollama"
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
        
        # Define model preference order: ENV var first, then the free models list.
        model_preference = [os.getenv("PLANNER_MODEL")] + FREE_MODELS
        model_preference = [m for m in model_preference if m] # Remove None if PLANNER_MODEL is not set
        model_preference = list(dict.fromkeys(model_preference)) # Remove duplicates

        for model in model_preference:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Intent: {intent}. Generate a mix of launch discovery and hiring signals."}
                    ],
                    response_format={"type": "json_object"},
                    timeout=60 # Add a timeout
                )
                data = json.loads(response.choices[0].message.content)
                queries = data.get("queries", [])
                logger.info(f"Planner generated {len(queries)} elite dorks using {model}.")
                return queries # Success, return immediately
            except Exception as e:
                logger.warning(f"LLM Planning attempt failed with model '{model}': {e}")
                
                # Rotate key if it looks like a limit/auth issue
                err_str = str(e).lower()
                if any(x in err_str for x in ["limit", "unauthorized", "credit", "quota"]):
                    logger.info("Rotating OpenRouter key due to limit/auth error.")
                    key_manager.rotate_key("openrouter")
                    # Re-initialize client with new key
                    client = self._get_client()
        
        logger.error("All LLM Planning attempts failed. Falling back to basic queries.")
        return [
            f'site:producthunt.com "Maker" "{intent}"',
            f'site:indiehackers.com "launched" "{intent}"',
            f'site:wellfound.com/jobs "hiring" "{intent}"',
            f'site:clutch.co "owner" "{intent}"',
            f'site:linkedin.com/in/ "founder" "{intent}" active'
        ]

    async def get_strategy(self, intent: str) -> Dict[str, Any]:
        return {
            "queries": await self.generate_queries(intent),
            "priority_sources": ["Product Hunt", "Indie Hackers", "Wellfound", "Clutch"]
        }
