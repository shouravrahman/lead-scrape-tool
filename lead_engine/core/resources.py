"""
Resource management utilities to prevent memory/connection leaks.
Ensures proper cleanup in async operations and long-running daemons.
"""
import asyncio
import logging
import psutil
import gc
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from lead_engine.db.models import SessionLocal

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors resource usage and alerts on leaks"""
    
    _instance = None
    _memory_baseline = None
    _start_time = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.process = psutil.Process()
            cls._instance._memory_baseline = cls._instance.process.memory_info().rss
            cls._instance._start_time = datetime.utcnow()
        return cls._instance
    
    def check_memory(self, threshold_mb: int = 500) -> bool:
        """
        Check if memory usage exceeds threshold.
        
        Args:
            threshold_mb: Warning threshold in MB
            
        Returns:
            True if memory is above threshold
        """
        current = self.process.memory_info().rss / (1024 * 1024)  # MB
        baseline = self._memory_baseline / (1024 * 1024)
        growth = current - baseline
        
        if growth > threshold_mb:
            logger.warning(
                f"⚠️  High memory usage detected: {current:.0f}MB "
                f"(growth: {growth:.0f}MB)"
            )
            return True
        
        return False
    
    def check_file_descriptors(self, threshold: int = 900) -> bool:
        """
        Check if open file descriptors exceed threshold.
        Default threshold is 900 (typical limit is 1024).
        
        Returns:
            True if FDs are above threshold
        """
        open_fds = self.process.num_fds()
        
        if open_fds > threshold:
            logger.warning(f"⚠️  High FD count: {open_fds} (threshold: {threshold})")
            return True
        
        return False
    
    def get_status(self) -> dict:
        """Get current resource status"""
        info = self.process.memory_info()
        return {
            "memory_rss_mb": info.rss / (1024 * 1024),
            "memory_vms_mb": info.vms / (1024 * 1024),
            "open_fds": self.process.num_fds(),
            "uptime_hours": (datetime.utcnow() - self._start_time).total_seconds() / 3600,
        }
    
    async def periodic_cleanup(self, interval_seconds: int = 3600):
        """
        Run periodic cleanup tasks.
        Call this once at startup: asyncio.create_task(monitor.periodic_cleanup())
        
        Args:
            interval_seconds: Cleanup interval (default: 1 hour)
        """
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                
                # Force garbage collection
                gc.collect()
                
                # Check resources
                self.check_memory()
                self.check_file_descriptors()
                
                # Log status
                status = self.get_status()
                logger.info(f"Resource status: {status}")
                
            except Exception as e:
                logger.error(f"Cleanup task failed: {e}")


@asynccontextmanager
async def managed_db_session() -> AsyncIterator:
    """
    Context manager for database sessions.
    Ensures proper cleanup even if exception occurs.
    
    Usage:
        async with managed_db_session() as db:
            result = db.query(Lead).first()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def timed_operation(operation_name: str, timeout_seconds: Optional[int] = None):
    """
    Context manager for timing and monitoring operations.
    
    Usage:
        async with timed_operation("sync_leads", timeout_seconds=300):
            await sync_operation()
    """
    start_time = datetime.utcnow()
    
    try:
        if timeout_seconds:
            yield timeout_seconds
        else:
            yield None
    except asyncio.TimeoutError:
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Operation '{operation_name}' timed out after {elapsed:.1f}s")
        raise
    except Exception as e:
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Operation '{operation_name}' failed after {elapsed:.1f}s: {e}")
        raise
    finally:
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Operation '{operation_name}' completed in {elapsed:.1f}s")


async def cleanup_old_logs(days: int = 30):
    """
    Delete old log entries from database.
    Call periodically to prevent log bloat.
    """
    from lead_engine.db.models import AgentLog
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    with SessionLocal() as db:
        try:
            deleted = db.query(AgentLog).filter(
                AgentLog.timestamp < cutoff_date
            ).delete()
            db.commit()
            
            logger.info(f"Cleaned up {deleted} old log entries (older than {days} days)")
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
            db.rollback()


async def cleanup_old_audit_logs(days: int = 90):
    """
    Delete very old audit logs (keep longer than regular logs for compliance).
    """
    from lead_engine.db.models import AuditLog
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    with SessionLocal() as db:
        try:
            deleted = db.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            ).delete()
            db.commit()
            
            logger.info(f"Cleaned up {deleted} old audit logs (older than {days} days)")
        except Exception as e:
            logger.error(f"Audit log cleanup failed: {e}")
            db.rollback()


# Global resource monitor instance
resource_monitor = ResourceMonitor()
