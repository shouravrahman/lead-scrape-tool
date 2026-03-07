import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict
from lead_engine.db.models import SessionLocal, ICPSettings
import json

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when API quota is exceeded"""
    pass


class RateLimiter:
    """
    Manages API quotas and request timing with persistent storage.
    Enforces hard limits and prevents quota overages.
    """
    _instance = None
    
    # Default quotas (can be overridden in database)
    DEFAULT_QUOTAS = {
        "serper": 2500,
        "tavily": 1000,
        "serpapi": 100,
        "firecrawl": 500
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance.last_request_time = {}
        return cls._instance

    def _get_quota_record(self, db, service: str):
        """Get or create quota record from database"""
        quota_key = f"quota_{service}_daily"
        record = db.query(ICPSettings).filter_by(key=quota_key).first()
        
        if not record:
            # Initialize quota
            record = ICPSettings(
                key=quota_key,
                value={
                    "limit": self.DEFAULT_QUOTAS.get(service, 100),
                    "used": 0,
                    "reset_at": datetime.utcnow().isoformat()
                },
                description=f"Daily quota for {service}"
            )
            db.add(record)
            db.commit()
        
        return record
    
    async def check_and_wait(self, service: str, weight: int = 1):
        """
        Enforces rate limits. BLOCKS if quota exceeded.
        
        Args:
            service: API service name
            weight: Number of quota units this call uses (default 1)
            
        Raises:
            RateLimitExceeded: If quota exceeded
        """
        with SessionLocal() as db:
            quota_record = self._get_quota_record(db, service)
            quota_data = quota_record.value or {}
            
            # Check if 24h has passed, reset if needed
            reset_at = datetime.fromisoformat(quota_data.get("reset_at", datetime.utcnow().isoformat()))
            if datetime.utcnow() > reset_at + timedelta(hours=24):
                quota_data["used"] = 0
                quota_data["reset_at"] = datetime.utcnow().isoformat()
                quota_record.value = quota_data
                db.commit()
            
            # Check if we have remaining quota
            limit = quota_data.get("limit", self.DEFAULT_QUOTAS.get(service, 100))
            used = quota_data.get("used", 0)
            
            if used + weight > limit:
                remaining_time = (
                    reset_at + timedelta(hours=24) - datetime.utcnow()
                ).total_seconds() / 3600
                
                error_msg = (
                    f"{service} quota exceeded. {used}/{limit} used. "
                    f"Resets in {remaining_time:.1f} hours."
                )
                logger.error(f"RateLimiter: {error_msg}")
                raise RateLimitExceeded(error_msg)
            
            # Update usage
            quota_data["used"] = used + weight
            quota_record.value = quota_data
            db.commit()
        
        # Enforce request delay (rate limiting)
        now = time.time()
        last_time = self.last_request_time.get(service, 0)
        delay = 2.0  # Minimum 2 seconds between requests to same service
        
        if now - last_time < delay:
            wait_time = delay - (now - last_time)
            logger.debug(f"RateLimiter: Sleeping {wait_time:.2f}s for {service}")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[service] = time.time()

    def get_quota_status(self) -> Dict[str, Dict[str, int]]:
        """Get current quota status for all services"""
        result = {}
        with SessionLocal() as db:
            for service in self.DEFAULT_QUOTAS.keys():
                record = self._get_quota_record(db, service)
                data = record.value or {}
                
                result[service] = {
                    "used": data.get("used", 0),
                    "limit": data.get("limit", self.DEFAULT_QUOTAS[service]),
                    "daily_limit": data.get("limit", self.DEFAULT_QUOTAS[service]),
                    "reset_at": data.get("reset_at", datetime.utcnow().isoformat())
                }
        
        return result
    
    def reset_quota(self, service: str):
        """Manually reset a service's quota (admin only)"""
        with SessionLocal() as db:
            record = self._get_quota_record(db, service)
            record.value = {
                "limit": self.DEFAULT_QUOTAS.get(service, 100),
                "used": 0,
                "reset_at": datetime.utcnow().isoformat()
            }
            db.commit()
            logger.info(f"RateLimiter: Reset quota for {service}")


limiter = RateLimiter()
