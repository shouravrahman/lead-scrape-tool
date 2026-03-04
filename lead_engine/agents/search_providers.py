import logging
import httpx
from typing import List, Dict, Any, Optional
from lead_engine.core.key_manager import key_manager
from lead_engine.core.limiter import limiter
from duckduckgo_search import DDGS
import serpapi
import asyncio

logger = logging.getLogger(__name__)

class SearchProvider:
    """Base class for search providers."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class SerperDevProvider(SearchProvider):
    """Google search via Serper.dev API (2,500 free)."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        api_key = key_manager.get_key("serper")
        if not api_key:
            return []
            
        await limiter.check_and_wait("serper")
        url = "https://google.serper.dev/search"
        payload = {"q": query, "num": 20}
        headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
        
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                results = response.json()
                return results.get("organic", [])
        except Exception as e:
            logger.warning(f"SerperDev error: {e}. Rotating key...")
            key_manager.rotate_key("serper")
            return []

class TavilyProvider(SearchProvider):
    """AI-centric search via Tavily API (1,000 free/mo)."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        api_key = key_manager.get_key("tavily")
        if not api_key:
            return []
            
        await limiter.check_and_wait("tavily")
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 10
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                results = response.json()
                # Format to match organic result style
                return [{"title": r["title"], "link": r["url"], "snippet": r["content"]} for r in results.get("results", [])]
        except Exception as e:
            logger.warning(f"Tavily error: {e}. Rotating key...")
            key_manager.rotate_key("tavily")
            return []

class DuckDuckGoProvider(SearchProvider):
    """Free search via DuckDuckGo scraping (unlimited)."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=20))
                # Format to match organic result style
                return [{"title": r["title"], "link": r["href"], "snippet": r["body"]} for r in results]
        except Exception as e:
            logger.warning(f"DuckDuckGo error: {e}")
            return []

class SerpApiProvider(SearchProvider):
    """Google search via SerpAPI (250 free)."""
    async def search(self, query: str) -> List[Dict[str, Any]]:
        api_key = key_manager.get_key("serpapi")
        if not api_key:
            return []
            
        await limiter.check_and_wait("serpapi")
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": 20 
        }
        try:
            # Using loop.run_in_executor if serpapi is synchronous
            loop = asyncio.get_event_loop()
            search = await loop.run_in_executor(None, lambda: serpapi.search(params))
            return search.get("organic_results", [])
        except Exception as e:
            logger.warning(f"SerpAPI error: {e}. Rotating key...")
            key_manager.rotate_key("serpapi")
            return []
