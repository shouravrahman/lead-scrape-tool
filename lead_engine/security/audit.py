"""
Audit logging for security compliance and monitoring.
Logs sensitive operations with data masking.
"""
from datetime import datetime
from lead_engine.db.models import SessionLocal, AuditLog
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Centralized audit logging for all sensitive operations.
    Masks sensitive data before logging.
    """
    
    @staticmethod
    def _mask_sensitive_data(details: dict) -> dict:
        """
        Masks sensitive information in log details.
        Prevents logging full PII.
        """
        if not details:
            return {}
        
        masked = details.copy()
        
        # Mask emails
        if 'email' in masked and masked['email']:
            email = masked['email']
            masked['email'] = email[:2] + '***@***' if len(email) > 4 else '***'
        
        # Mask API keys
        if 'key' in masked and masked['key']:
            key = masked['key']
            masked['key'] = '***' + key[-4:] if len(key) > 8 else '***'
        
        # Mask phone numbers
        if 'phone' in masked and masked['phone']:
            phone = masked['phone']
            masked['phone'] = phone[:2] + '***' if len(phone) > 2 else '***'
        
        # Mask credit card info
        if 'card' in masked:
            masked['card'] = '****-****-****-' + (masked['card'][-4:] if len(masked['card']) > 4 else '****')
        
        return masked
    
    @staticmethod
    def log(action: str, resource_type: str = None, resource_id: str = None,
            details: dict = None, user: str = "system", ip_address: str = None):
        """
        Log an action to the immutable audit trail.
        
        Args:
            action: Action name (CREATE_JOB, EXPORT_LEAD, ROTATE_KEY, etc.)
            resource_type: Type of resource (lead, job, key, etc.)
            resource_id: ID of the resource
            details: Additional details (dict, will be JSON-serialized)
            user: Username/identifier of who took the action
            ip_address: Optional IP address (for cloud deployments)
        
        Example:
            AuditLogger.log(
                'CREATE_JOB',
                resource_type='job',
                resource_id='123',
                details={'intent': 'SaaS founders', 'max_leads': 100},
                user='john@example.com'
            )
        """
        with SessionLocal() as db:
            try:
                # Mask sensitive data
                masked_details = AuditLogger._mask_sensitive_data(details or {})
                
                audit = AuditLog(
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    details=masked_details,
                    user=user,
                    timestamp=datetime.utcnow(),
                    ip_address=ip_address
                )
                db.add(audit)
                db.commit()
                
                logger.info(
                    f"[AUDIT] {action} on {resource_type}#{resource_id} "
                    f"by {user} at {audit.timestamp.isoformat()}"
                )
            except Exception as e:
                logger.error(f"Failed to log audit event: {e}")
                # Don't raise - audit failure shouldn't break app
    
    @staticmethod
    def log_api_call(service: str, endpoint: str, user: str = "system", success: bool = True):
        """Log API calls for tracking usage"""
        AuditLogger.log(
            action='API_CALL',
            resource_type='api',
            resource_id=service,
            details={'endpoint': endpoint, 'success': success},
            user=user
        )
    
    @staticmethod
    def log_key_rotation(service: str, key_index: int, user: str = "system"):
        """Log API key rotations"""
        AuditLogger.log(
            action='ROTATE_KEY',
            resource_type='key',
            resource_id=service,
            details={'key_index': key_index},
            user=user
        )
    
    @staticmethod
    def log_lead_action(action: str, lead_id: int, details: dict = None, user: str = "system"):
        """Log lead-related actions (create, export, vetting, etc.)"""
        AuditLogger.log(
            action=action,
            resource_type='lead',
            resource_id=str(lead_id),
            details=details,
            user=user
        )
    
    @staticmethod
    def log_auth_event(event: str, user: str, success: bool = True, ip_address: str = None):
        """Log authentication events"""
        AuditLogger.log(
            action='AUTH_' + event.upper(),
            resource_type='user',
            resource_id=user,
            details={'success': success},
            user=user,
            ip_address=ip_address
        )


# Convenience function for decorators
def audit_action(action_name: str):
    """
    Decorator to automatically log function calls.
    
    Example:
        @audit_action('EXPORT_LEAD')
        def export_lead(lead_id):
            # ... do work ...
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                AuditLogger.log(action_name)
                return result
            except Exception as e:
                AuditLogger.log(action_name, details={'error': str(e)})
                raise
        
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                AuditLogger.log(action_name)
                return result
            except Exception as e:
                AuditLogger.log(action_name, details={'error': str(e)})
                raise
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
