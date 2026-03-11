"""
Secure error handling with message sanitization.
Prevents information disclosure while maintaining detailed internal logging.
"""
import logging
import traceback
from typing import Optional, Type
from datetime import datetime

logger = logging.getLogger(__name__)


class SecureError(Exception):
    """
    Base exception class that supports both user-facing and detailed internal messages.
    User-facing messages are generic. Internal messages are logged with full details.
    """
    
    def __init__(self, user_message: str, internal_message: str = None):
        """
        Args:
            user_message: Generic message shown to user
            internal_message: Detailed message logged internally
        """
        self.user_message = user_message
        self.internal_message = internal_message or user_message
        super().__init__(self.user_message)
    
    def __str__(self):
        return self.user_message
    
    def get_internal_message(self) -> str:
        """Get detailed message for internal logging"""
        return self.internal_message


class APIError(SecureError):
    """API call failed"""
    def __init__(self, service: str, internal_detail: str = None):
        user_msg = f"Unable to communicate with {service}. Please try again."
        internal_msg = internal_detail or f"{service} API error"
        super().__init__(user_msg, internal_msg)


class AuthenticationError(SecureError):
    """Authentication/authorization failed"""
    def __init__(self, reason: str = None):
        user_msg = "Authentication failed. Please check your credentials."
        internal_msg = f"Auth failed: {reason}" if reason else user_msg
        super().__init__(user_msg, internal_msg)


class ValidationError(SecureError):
    """Input validation failed"""
    def __init__(self, field: str, reason: str):
        user_msg = f"Invalid input: {reason}"
        internal_msg = f"Validation failed on field '{field}': {reason}"
        super().__init__(user_msg, internal_msg)


class RateLimitError(SecureError):
    """Rate limit exceeded"""
    def __init__(self, service: str, reset_time: str = None):
        user_msg = f"{service.upper()} quota exceeded. Please try again later."
        internal_msg = f"Quota exceeded for {service}. Resets at {reset_time}" if reset_time else user_msg
        super().__init__(user_msg, internal_msg)


class DatabaseError(SecureError):
    """Database operation failed"""
    def __init__(self, operation: str, internal_detail: str = None):
        user_msg = "Database operation failed. Please try again."
        internal_msg = f"DB {operation} failed: {internal_detail}" if internal_detail else user_msg
        super().__init__(user_msg, internal_msg)


class EncryptionError(SecureError):
    """Encryption/decryption operation failed"""
    def __init__(self, operation: str, internal_detail: str = None):
        user_msg = "Secure operation failed. Please contact support."
        internal_msg = f"Encryption {operation} failed: {internal_detail}" if internal_detail else user_msg
        super().__init__(user_msg, internal_msg)


class ErrorHandler:
    """
    Central error handling utility.
    Ensures consistent error logging and generic user-facing messages.
    """
    
    @staticmethod
    def log_and_sanitize(
        exception: Exception,
        context: str = None,
        log_level: int = logging.ERROR
    ) -> str:
        """
        Log detailed error internally, return sanitized user message.
        
        Args:
            exception: The exception to handle
            context: Additional context (user action, operation, etc.)
            log_level: Logging level (INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            User-friendly error message (safe to show in UI)
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Extract internal and user messages
        if isinstance(exception, SecureError):
            user_msg = exception.user_message
            internal_msg = exception.get_internal_message()
        else:
            user_msg = "An error occurred. Please try again."
            internal_msg = str(exception)
        
        # Log detailed internal message with full traceback
        log_msg = f"[{timestamp}] {context or 'Error occurred'}\n"
        log_msg += f"Exception: {type(exception).__name__}\n"
        log_msg += f"Message: {internal_msg}\n"
        log_msg += f"Traceback:\n{traceback.format_exc()}"
        
        logger.log(log_level, log_msg)
        
        return user_msg
    
    @staticmethod
    def sanitize_exception(exception: Exception) -> str:
        """
        Convert any exception to a user-safe message.
        """
        if isinstance(exception, SecureError):
            return exception.user_message
        
        # Generic fallback
        error_type = type(exception).__name__
        return f"An error occurred ({error_type}). Please try again."
    
    @staticmethod
    def log_success(action: str, details: str = None, level: int = logging.INFO):
        """Log successful operations"""
        msg = f"[{datetime.utcnow().isoformat()}] {action}"
        if details:
            msg += f": {details}"
        logger.log(level, msg)
    
    @staticmethod
    def create_error_context(operation: str, user_id: str = None, resource_id: str = None) -> str:
        """Create context string for error logging"""
        parts = [operation]
        if user_id:
            parts.append(f"user={user_id}")
        if resource_id:
            parts.append(f"resource={resource_id}")
        return " | ".join(parts)

    @staticmethod
    def get_base64_image(image_path: str) -> str:
        """Read image and return base64 string"""
        import base64
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()


# Decorator for automatic error handling
def handle_errors(operation_name: str = "Operation"):
    """
    Decorator for automatic error handling and sanitization.
    
    Usage:
        @handle_errors("User login")
        async def login(username):
            # ... do work ...
    """
    def decorator(func):
        import asyncio
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = ErrorHandler.create_error_context(operation_name)
                error_msg = ErrorHandler.log_and_sanitize(e, context)
                raise SecureError(error_msg, str(e)) from e
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorHandler.create_error_context(operation_name)
                error_msg = ErrorHandler.log_and_sanitize(e, context)
                raise SecureError(error_msg, str(e)) from e
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
