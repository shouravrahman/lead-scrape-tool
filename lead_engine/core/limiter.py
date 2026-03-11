import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from lead_engine.db.models import SessionLocal, ICPSettings
from lead_engine.core.key_manager import key_manager
import json

logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Raised when API quota is exceeded"""
    pass

class RateLimiter:
    """
    Manages API quotas and request timing with persistent storage.
    Enforces hard limits and prevents quota overages.
    Dynamically scales limits based on the number of active keys.
    """
    _instance = None
    
    # Base limits PER KEY (Monthly)
    # The user noted that showing these as 'daily' was incorrect for these services' free tiers
    BASE_QUOTA_CONFIG = {
        "serper": {"limit": 2500, "frequency": "monthly"},
        "tavily": {"limit": 1000, "frequency": "monthly"},
        "serpapi": {"limit": 100, "frequency": "monthly"},
        "firecrawl": {"limit": 500, "frequency": "monthly"}
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance.last_request_time = {}
        return cls._instance

    def _get_api_key_count(self, service: str) -> int:
        """Get number of active keys for a service"""
        keys = key_manager.get_keys(service)
        return max(1, len(keys)) # Assume at least 1 key capacity even if config is missing (for safety)

    def _get_quota_record(self, db, service: str):
        """Get or create quota record from database"""
        quota_key = f"quota_{service}_v2"
        record = db.query(ICPSettings).filter_by(key=quota_key).first()
        
        config = self.BASE_QUOTA_CONFIG.get(service, {"limit": 100, "frequency": "monthly"})
        key_count = self._get_api_key_count(service)
        effective_limit = config["limit"] * key_count

        if not record:
            # Initialize quota
            record = ICPSettings(
                key=quota_key,
                value={
                    "base_limit": config["limit"],
                    "key_count": key_count,
                    "limit": effective_limit,
                    "used": 0,
                    "frequency": config["frequency"],
                    "reset_at": datetime.utcnow().isoformat()
                },
                description=f"{config['frequency'].capitalize()} quota for {service} ({key_count} keys)"
            )
            db.add(record)
            db.commit()
        else:
            # Update limit if key count changed
            data = record.value or {}
            if data.get("key_count") != key_count or data.get("base_limit") != config["limit"]:
                data["key_count"] = key_count
                data["base_limit"] = config["limit"]
                data["limit"] = effective_limit
                record.value = data
                db.commit()
        
        return record
    
    async def check_and_wait(self, service: str, weight: int = 1):
        """
        Enforces rate limits. BLOCKS if quota exceeded.
        """
        with SessionLocal() as db:
            quota_record = self._get_quota_record(db, service)
            quota_data = quota_record.value or {}
            
            # Check reset period (24h for daily, 30 days for monthly)
            reset_at = datetime.fromisoformat(quota_data.get("reset_at", datetime.utcnow().isoformat()))
            frequency = quota_data.get("frequency", "monthly")
            days_to_reset = 30 if frequency == "monthly" else 1
            
            if datetime.utcnow() > reset_at + timedelta(days=days_to_reset):
                quota_data["used"] = 0
                quota_data["reset_at"] = datetime.utcnow().isoformat()
                quota_record.value = quota_data
                db.commit()
            
            # Check if we have remaining quota
            limit = quota_data.get("limit", 100)
            used = quota_data.get("used", 0)
            
            if used + weight > limit:
                reset_delta = reset_at + timedelta(days=days_to_reset) - datetime.utcnow()
                days = reset_delta.days
                hours = reset_delta.seconds // 3600
                
                error_msg = (
                    f"{service} {frequency} quota exceeded. {used}/{limit} used. "
                    f"Resets in {days}d {hours}h."
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
        delay = 1.0  # Reduced delay since we are spreading across multiple keys potentially
        
        if now - last_time < delay:
            wait_time = delay - (now - last_time)
            await asyncio.sleep(wait_time)
        
        self.last_request_time[service] = time.time()

    def get_quota_status(self) -> Dict[str, Dict]:
        """Get current quota status for all services"""
        result = {}
        with SessionLocal() as db:
            for service in self.BASE_QUOTA_CONFIG.keys():
                record = self._get_quota_record(db, service)
                data = record.value or {}
                
                result[service] = {
                    "used": data.get("used", 0),
                    "limit": data.get("limit", 0),
                    "frequency": data.get("frequency", "monthly"),
                    "key_count": data.get("key_count", 1),
                    "reset_at": data.get("reset_at", datetime.utcnow().isoformat())
                }
        return result

limiter = RateLimiter()
