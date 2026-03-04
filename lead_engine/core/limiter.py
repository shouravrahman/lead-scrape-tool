import asyncio
import time
import logging
from typing import Dict
from lead_engine.db.models import SessionLocal, ICPSettings
import json

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Manages API quotas and request timing (leaky bucket/token based).
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance.quotas = {
                "serper": {"daily_limit": 2500, "used": 0},
                "tavily": {"daily_limit": 1000, "used": 0},
                "serpapi": {"daily_limit": 100, "used": 0},
                "firecrawl": {"daily_limit": 500, "used": 0}
            }
            cls._instance.last_request_time = {}
        return cls._instance

    async def check_and_wait(self, service: str, weight: int = 1):
        """
        Enforces a delay between requests and checks if quota is remaining.
        """
        # 1. Enforce delay (e.g., 2 seconds between same-service calls)
        now = time.time()
        last_time = self.last_request_time.get(service, 0)
        delay = 2.0  # Default delay
        
        if now - last_time < delay:
            wait_time = delay - (now - last_time)
            logger.debug(f"RateLimiter: Sleeping {wait_time:.2f}s for {service}")
            await asyncio.sleep(wait_time)
            
        # 2. Update usage (mocked persistent storage for now)
        self.quotas[service]["used"] += weight
        self.last_request_time[service] = time.time()
        
        # 3. Warning if over quota
        if self.quotas[service]["used"] > self.quotas[service]["daily_limit"]:
            logger.warning(f"RateLimiter: Service {service} exceeded daily limit!")

    def get_quota_status(self) -> Dict[str, Dict[str, int]]:
        return self.quotas

limiter = RateLimiter()
