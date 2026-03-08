import os
import re
import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from lead_engine.core.key_manager import key_manager

load_dotenv()

logger = logging.getLogger(__name__)

# List of free/low-cost models to rotate through on OpenRouter, from best to worst
FREE_MODELS = [
    "google/gemini-2.0-pro-exp-02-05:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

class ExtractionAgent:
    """
    Converts messy data into structured JSON using LLMs with robust fallbacks.
    """
    def __init__(self):
        # Client is initialized per-request to use rotated keys
        pass

    def _get_client(self):
        api_key = key_manager.get_key("openrouter") or "ollama"
        base_url = os.getenv("OLLAMA_BASE_URL")
        
        if not base_url and key_manager.get_key("openrouter"):
            base_url = "https://openrouter.ai/api/v1"
            
        if api_key:
            return OpenAI(api_key=api_key, base_url=base_url)
        return None

    async def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return None

        model_preference = [os.getenv("EXTRACTOR_MODEL")] + FREE_MODELS
        model_preference = [m for m in model_preference if m]
        model_preference = list(dict.fromkeys(model_preference))

        for model in model_preference:
            try:
                response = client.chat.completions.create(
                    model=model, 
                    messages=[
                        {"role": "system", "content": """You are a professional lead extraction agent. 
                        Target the following fields: 
                        - name, company, email, linkedin_url
                        - hiring_status (is the company hiring? true/false)
                        - launch_status (did they just launch? true/false)
                        - team_size (hint of team size)
                        Return ONLY valid JSON."""},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                logger.warning(f"LLM extraction attempt failed with model '{model}': {e}")
                err_str = str(e).lower()
                if any(x in err_str for x in ["limit", "active", "unauthorized", "credit", "quota"]):
                    logger.info("Rotating OpenRouter key due to limit/auth error.")
                    key_manager.rotate_key("openrouter")
                    client = self._get_client()
        
        # If all models fail, raise an exception to trigger the fallback in the `extract` method.
        raise Exception("All LLM extraction models failed.")

    async def extract(self, raw_text: str) -> Dict[str, Any]:
        """
        Main entry point for extraction.
        """
        prompt = f"""
        Extract lead information from the following text. 
        Focus on: Name, Email, LinkedIn URL, Company Name, and Tech Stack mentioned.
        
        Text:
        {raw_text[:2000]}
        
        Return JSON format:
        {{
            "name": "...",
            "email": "...",
            "linkedin_url": "...",
            "company": "...",
            "tech_stack": ["...", "..."],
            "description": "..."
        }}
        """
        
        try:
            data = await self._call_llm(prompt)
            if data:
                logger.info(f"LLM successfully extracted data for {data.get('name')}")
                if not data.get('hiring_status'):
                    data['hiring_status'] = 'hiring' in str(raw_text).lower() or 'looking for' in str(raw_text).lower() or 'join us' in str(raw_text).lower()
                if not data.get('launch_status'):
                    data['launch_status'] = 'launch' in str(raw_text).lower() or 'beta' in str(raw_text).lower()
                return data
        except Exception:
            logger.warning("LLM extraction failed after retries. Falling back to regex.")
            
        return self.regex_fallback(raw_text)

    def regex_fallback(self, text: str) -> Dict[str, Any]:
        """
        Dumb but reliable regex-based extraction.
        """
        emails = re.findall(r'[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+', text.lower())
        linkedin = re.findall(r'linkedin\.com/in/[a-z0-9-]+', text.lower())
        
        # Simple name heuristic: first line if short
        lines = text.split('\n')
        name = lines[0].strip() if len(lines[0]) < 50 else "Unknown Lead"
        
        return {
            "name": name,
            "email": emails[0] if emails else None,
            "linkedin_url": f"https://{linkedin[0]}" if linkedin else None,
            "company": None,
            "tech_stack": [],
            "description": "Extracted via regex fallback"
        }
