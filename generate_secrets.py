import os
import sys
from dotenv import load_dotenv

# Ensure we can import the project modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from lead_engine.security.encryption import SecretManager
except ImportError:
    print("❌ Error: Could not import lead_engine. Run this from the project root.")
    sys.exit(1)

def main():
    # Load .env file
    load_dotenv()
    
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        print("❌ Error: ENCRYPTION_KEY not found in .env file.")
        print("Run: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
        return

    print("# .streamlit/secrets.toml")
    print("# -------------------------------------------------------")
    print("# COPY EVERYTHING BELOW THIS LINE INTO STREAMLIT CLOUD SECRETS")
    print("# -------------------------------------------------------")
    print("")
    
    # 1. Encryption Key
    print(f'ENCRYPTION_KEY = "{encryption_key}"')
    
    # 2. Database
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f'DATABASE_URL = "{db_url}"')
    
    # 3. Encrypt API Keys
    api_keys = [
        "OPENROUTER_API_KEYS",
        "SERP_API_KEYS",
        "SERPER_API_KEYS",
        "TAVILY_API_KEYS",
        "FIRECRAWL_API_KEYS"
    ]
    
    for key_name in api_keys:
        raw_value = os.getenv(key_name)
        if raw_value:
            # Split by comma, encrypt each, join back
            parts = [p.strip() for p in raw_value.split(",") if p.strip()]
            encrypted_parts = []
            for part in parts:
                if part.startswith("encrypted:"):
                    encrypted_parts.append(part)
                else:
                    encrypted = SecretManager.encrypt(part)
                    encrypted_parts.append(f"encrypted:{encrypted}")
            
            final_value = ",".join(encrypted_parts)
            print(f'{key_name} = "{final_value}"')

    # 4. Standard Configs
    configs = [
        "PLANNER_MODEL",
        "EXTRACTOR_MODEL",
        "GOOGLE_SHEET_ID",
        "AUTO_SYNC_TO_SHEETS",
        "LOG_LEVEL"
    ]
    
    for key in configs:
        val = os.getenv(key)
        if val:
            print(f'{key} = "{val}"')

    # 5. Google Credentials (TOML Multi-line)
    creds = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds:
        # Use triple quotes for multi-line JSON strings in TOML
        print(f"GOOGLE_CREDENTIALS_JSON = '''{creds}'''")

if __name__ == "__main__":
    main()