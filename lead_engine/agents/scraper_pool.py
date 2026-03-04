import os
import random
import asyncio
import logging
from typing import List, Dict, Any
from lead_engine.core.key_manager import key_manager
from lead_engine.agents.search_providers import SerperDevProvider, TavilyProvider, DuckDuckGoProvider, SerpApiProvider
import firecrawl

logger = logging.getLogger(__name__)

class SERPScraper:
    """
    Search-based lead discovery agent.
    Now cycles through multiple providers (Serper, Tavily, SerpAPI, DDG) to maximize free tiers.
    """
    def __init__(self):
        self.providers = [
            SerperDevProvider(),
            TavilyProvider(),
            SerpApiProvider(),
            DuckDuckGoProvider()
        ]

    async def run(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes search with multi-provider fallback.
        """
        for provider in self.providers:
            try:
                results = await provider.search(query)
                if results:
                    logger.info(f"SERPScraper: Found {len(results)} results using {provider.__class__.__name__}")
                    return results
            except Exception as e:
                logger.warning(f"SERPScraper: Provider {provider.__class__.__name__} failed: {e}")
                continue
        
        logger.error(f"SERPScraper: All search providers failed for query: {query}")
        return []

class FirecrawlScraper:
    """
    Deep web scraping agent.
    """
    def __init__(self):
        pass

    async def run(self, url: str) -> Dict[str, Any]:
        api_key = key_manager.get_key("firecrawl")
        if not api_key:
            return {"markdown": ""}
            
        app = firecrawl.FirecrawlApp(api_key=api_key)
        try:
            # Using run_in_executor for synchronous firecrawl-py calls if needed
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: app.scrape_url(url, params={'formats': ['markdown']}))
            return result
        except Exception as e:
            if "limit" in str(e).lower() or "active" in str(e).lower():
                key_manager.rotate_key("firecrawl")
            logger.warning(f"Firecrawl scrape failed: {url} -> {e}")
            return {"markdown": ""}

class LinkedInScraper(SERPScraper):
    """
    Specialized LinkedIn search signals.
    """
    async def run(self, query: str) -> List[Dict[str, Any]]:
        # Prepend site:linkedin.com if not present
        if "site:linkedin.com" not in query:
            query = f"site:linkedin.com/in/ {query}"
        return await super().run(query)

class ScraperAgentPool:
    """
    Managed pool of scrapers with concurrency control and jitter.
    """
    def __init__(self):
        self.serp = SERPScraper()
        self.linkedin = LinkedInScraper()
        self.firecrawl = FirecrawlScraper()
        self.semaphore = asyncio.Semaphore(3) # Limit concurrent scrapers

    async def run_all(self, queries: List[str]) -> List[Dict[str, Any]]:
        all_results = []
        tasks = []
        for q in queries:
            tasks.append(self._guarded_run(q))
        
        results = await asyncio.gather(*tasks)
        for r in results:
            all_results.extend(r)
            
        return all_results

    async def _guarded_run(self, query: str):
        async with self.semaphore:
            # Mimic human behavior with jitter
            await asyncio.sleep(random.uniform(1.0, 3.0))
            return await self.serp.run(query)
