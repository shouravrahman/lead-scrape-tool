"""
Request signing and verification utilities.
Prevents tampering and ensures request authenticity.
"""
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class RequestSigner:
    """
    Signs requests with HMAC to prevent tampering.
    Useful for verifying API requests came from your system.
    """
    
    def __init__(self, secret_key: str = None):
        """
        Initialize with a signing secret.
        
        Args:
            secret_key: Secret key for HMAC signing (from env or config)
        """
        import os
        self.secret_key = secret_key or os.getenv("REQUEST_SIGNING_KEY", "")
        
        if not self.secret_key:
            logger.warning("⚠️  REQUEST_SIGNING_KEY not set. Request signing disabled.")
    
    def sign_request(self, method: str, url: str, body: Dict[str, Any] = None) -> str:
        """
        Create an HMAC signature for a request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            body: Request body (will be JSON-serialized)
            
        Returns:
            HMAC signature string
        """
        if not self.secret_key:
            return ""
        
        # Create canonical request string
        canonical = f"{method}\n{url}"
        
        if body:
            body_str = json.dumps(body, sort_keys=True)
            canonical += f"\n{body_str}"
        
        # Add timestamp
        canonical += f"\n{datetime.utcnow().isoformat()}"
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, signature: str, method: str, url: str, body: Dict[str, Any] = None) -> bool:
        """
        Verify a request signature.
        
        Args:
            signature: Signature to verify
            method: HTTP method
            url: Request URL
            body: Request body
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.secret_key:
            return True  # Signing disabled
        
        expected_signature = self.sign_request(method, url, body)
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)


class RequestValidator:
    """
    Validates HTTP requests for authenticity and safety.
    """
    
    @staticmethod
    def validate_content_type(content_type: str, expected: str = "application/json") -> bool:
        """Validate content type"""
        if not content_type:
            return expected is None
        
        # Extract media type from content-type header (remove charset, etc)
        media_type = content_type.split(";")[0].strip()
        return media_type == expected
    
    @staticmethod
    def validate_content_length(headers: Dict[str, str], max_bytes: int = 1024 * 100) -> bool:
        """Validate request size"""
        try:
            content_length = int(headers.get("content-length", 0))
            return content_length <= max_bytes
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_headers(headers: Dict[str, str]) -> bool:
        """Validate request headers for suspicious patterns"""
        suspicious_patterns = [
            "shell", "bash", "cmd", "powershell",
            "eval", "exec", "system", "__import__"
        ]
        
        for key, value in headers.items():
            if not isinstance(value, str):
                continue
            
            value_lower = value.lower()
            for pattern in suspicious_patterns:
                if pattern in value_lower:
                    logger.warning(f"Suspicious header detected: {key}")
                    return False
        
        return True


# Global request signer instance
request_signer = RequestSigner()
