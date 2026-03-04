import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class KeyManager:
    """
    Singleton manager for API key pools across multiple services.
    Supports rotation and provider-specific key management.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._instance.keys = {
                "serpapi": [],
                "serper": [],
                "tavily": [],
                "firecrawl": [],
                "openrouter": [],
                "openai": []
            }
            cls._instance.active_index = {
                "serpapi": 0,
                "serper": 0,
                "tavily": 0,
                "firecrawl": 0,
                "openrouter": 0,
                "openai": 0
            }
            cls._instance._load_keys_from_env()
        return cls._instance

    def _load_keys_from_env(self):
        """
        Loads keys from .env variables.
        Supports COMMA SEPARATED lists for pooling.
        Example: SERP_API_KEYS=key1,key2
        """
        mapping = {
            "serpapi": "SERP_API_KEYS",
            "serper": "SERPER_API_KEYS",
            "tavily": "TAVILY_API_KEYS",
            "firecrawl": "FIRECRAWL_API_KEYS",
            "openrouter": "OPENROUTER_API_KEYS",
            "openai": "OPENAI_API_KEYS"
        }
        
        # Fallback single key mapping
        fallbacks = {
            "serpapi": "SERP_API_KEY",
            "serper": "SERPER_API_KEY",
            "tavily": "TAVILY_API_KEY",
            "firecrawl": "FIRECRAWL_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY"
        }

        for service, env_var in mapping.items():
            # Try comma-separated list first
            val = os.getenv(env_var)
            if val:
                self.keys[service].extend([k.strip() for k in val.split(",") if k.strip()])
                logger.info(f"KeyManager: Loaded {len(self.keys[service])} keys for {service}")
            
            # Try fallback single key
            fallback_val = os.getenv(fallbacks[service])
            if fallback_val and fallback_val not in self.keys[service]:
                self.keys[service].append(fallback_val.strip())
                logger.info(f"KeyManager: Added fallback key for {service}")

    def get_key(self, service: str) -> Optional[str]:
        """
        Returns the currently active key for a service.
        """
        service_keys = self.keys.get(service, [])
        if not service_keys:
            return None
        
        idx = self.active_index.get(service, 0)
        # Ensure index is in range
        if idx >= len(service_keys):
            self.active_index[service] = 0
            idx = 0
            
        return service_keys[idx]

    def rotate_key(self, service: str):
        """
        Rotates to the next key in the pool for a service.
        """
        if service in self.keys and len(self.keys[service]) > 1:
            prev_idx = self.active_index[service]
            self.active_index[service] = (prev_idx + 1) % len(self.keys[service])
            logger.warning(f"KeyManager: Rotated {service} key to index {self.active_index[service]}")

    def add_key(self, service: str, key: str):
        """
        Dynamically adds a key to a service pool.
        """
        if service in self.keys:
            if key not in self.keys[service]:
                self.keys[service].append(key)
                logger.info(f"KeyManager: Added new key to {service} pool. Total: {len(self.keys[service])}")

key_manager = KeyManager()
