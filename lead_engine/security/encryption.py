"""
Encryption utilities for sensitive data.
Handles encryption/decryption of API keys, credentials, and PII.
"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class SecretManager:
    """
    Manages encryption/decryption of sensitive data using Fernet (AES-128).
    
    Usage:
        from lead_engine.security.encryption import SecretManager
        encrypted = SecretManager.encrypt("my-api-key")
        decrypted = SecretManager.decrypt(encrypted)
    """
    _cipher = None
    
    @classmethod
    def _get_cipher(cls):
        """Get or initialize Fernet cipher from ENCRYPTION_KEY env var"""
        if cls._cipher is not None:
            return cls._cipher
        
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise EncryptionError(
                "ENCRYPTION_KEY not set. Generate one with:\n"
                "python -c \"from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())\"\n"
                "Then add to .env: ENCRYPTION_KEY=<generated_key>"
            )
        
        try:
            cls._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            raise EncryptionError(f"Invalid ENCRYPTION_KEY format: {e}")
        
        return cls._cipher
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (safe to store in .env or database)
        """
        if not plaintext:
            return ""
        
        try:
            cipher = cls._get_cipher()
            encrypted = cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")
    
    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            ciphertext: Encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        
        try:
            cipher = cls._get_cipher()
            decrypted = cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token (wrong key?)")
            raise EncryptionError("Failed to decrypt data: Invalid encryption key")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")
    
    @classmethod
    def is_encrypted(cls, text: str) -> bool:
        """Check if a string appears to be encrypted (starts with 'gAAAAAB')"""
        return text.startswith("gAAAAAB") if text else False


# Utility function for decorator use
def encrypt_env_keys(env_var: str) -> list[str]:
    """
    Helper to load and decrypt comma-separated keys from env var.
    
    Usage:
        api_keys = encrypt_env_keys("SERP_API_KEYS")
    """
    raw_value = os.getenv(env_var, "")
    if not raw_value:
        return []
    
    keys = []
    for item in raw_value.split(","):
        item = item.strip()
        if not item:
            continue
        
        # If starts with 'encrypted:', decrypt it
        if item.startswith("encrypted:"):
            try:
                encrypted_part = item[10:]  # Remove 'encrypted:' prefix
                decrypted = SecretManager.decrypt(encrypted_part)
                keys.append(decrypted)
            except Exception as e:
                logger.warning(f"Failed to decrypt key from {env_var}: {e}")
                continue
        else:
            # Plain key (backward compatibility, but warn)
            logger.warning(f"⚠️  Plain-text key detected in {env_var}. Encrypt it!")
            keys.append(item)
    
    return keys
