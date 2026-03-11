from crewai.tools import tool
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

@tool("Search Internet for Leads")
def search_internet(query: str) -> str:
    """
    Search the internet using multiple providers (Google, DuckDuckGo, etc.) for a specific Google Dork query.
    Return a comprehensive JSON string of search results (title, link, snippet). This is crucial for finding links to scrape.
    """
    from lead_engine.agents.search_providers import SerperDevProvider, TavilyProvider, DuckDuckGoProvider, SerpApiProvider
    
    async def _run_search():
        providers = [SerperDevProvider(), TavilyProvider(), SerpApiProvider(), DuckDuckGoProvider()]
        for provider in providers:
            try:
                results = await provider.search(query)
                if results:
                    return json.dumps(results[:10])
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
        return json.dumps([])
        
    # Handle running async in a sync wrapper context which CrewAI defaults to calling
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_search())
    
    return asyncio.run_coroutine_threadsafe(_run_search(), loop).result()

@tool("Scrape Website Content")
def scrape_website(url: str) -> str:
    """
    Deep scrape a given website URL (like a company About page, or a LinkedIn URL) and return its content in Markdown format.
    Use this to extract detailed information about a lead's tech stack or hiring signals.
    """
    from lead_engine.agents.scraper_pool import FirecrawlScraper
    
    async def _run_scrape():
        scraper = FirecrawlScraper()
        result = await scraper.run(url)
        return result.get('markdown', '')

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_scrape())
        
    return asyncio.run_coroutine_threadsafe(_run_scrape(), loop).result()
