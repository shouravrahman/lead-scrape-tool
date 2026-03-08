# 🌐 Streamlit Cloud Deployment Guide

**Complete production deployment for the hardened Lead Intelligence System on Streamlit Cloud.**

---

## ✅ Pre-Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `.env` is in `.gitignore`
- [ ] `credentials.json` is in `.gitignore`
- [ ] All dependencies in `requirements.txt`
- [ ] Neon PostgreSQL database ready
- [ ] API keys encrypted
- [ ] Streamlit Cloud account created

---

## 1️⃣ Prepare Repository

### .gitignore
```
.env
.env.local
credentials.json
.streamlit/secrets.toml
__pycache__/
*.pyc
```

### Push to GitHub
```bash
git push origin main
```

---

## 2️⃣ Deploy to Streamlit Cloud

### 1. Go to [share.streamlit.io](https://share.streamlit.io)

### 2. Click "New app"
- Select repository
- Branch: `main`
- Main file: `streamlit_app.py`

### 3. Click "Deploy" (wait 60-90 seconds)

---

## 3️⃣ Configure Secrets

In your app URL bar:
1. Click **Settings** (gear icon)
2. Click **Secrets**
3. Paste below and fill in YOUR values

### Secrets.toml Template

```toml
# DATABASE (REQUIRED)
DATABASE_URL = "postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require"

# ENCRYPTION KEY (REQUIRED)
ENCRYPTION_KEY = "your_fernet_key_here"

# API KEYS (Encrypted format)
SERP_API_KEYS = "encrypted:gAAAAAB...,encrypted:gAAAAAB..."
SERPER_API_KEYS = "encrypted:gAAAAAB..."
TAVILY_API_KEYS = "encrypted:gAAAAAB..."
FIRECRAWL_API_KEYS = "encrypted:gAAAAAB..."
OPENROUTER_API_KEYS = "encrypted:gAAAAAB..."


# LLM MODELS
PLANNER_MODEL = "google/gemini-flash-1.5-free"
EXTRACTOR_MODEL = "google/gemini-flash-1.5-free"

# GOOGLE SHEETS (Optional) - Paste the content of your credentials.json file as a single-line string.
GOOGLE_SHEET_ID = "your_44_char_id"
GOOGLE_CREDENTIALS_JSON = '{"type": "service_account", ...}'
AUTO_SYNC_TO_SHEETS = "true"

# LOGGING
LOG_LEVEL = "INFO"
```

---

## 4️⃣ Generate Encrypted Keys

Before pasting into Secrets, encrypt your API keys:

```bash
python << 'EOF'
from lead_engine.security.encryption import SecretManager

# Example
serp_keys = ["key1", "key2"]
encrypted = ",".join([f"encrypted:{SecretManager.encrypt(k)}" for k in serp_keys])
print(f"SERP_API_KEYS = \"{encrypted}\"")
EOF
```

Copy output → paste into Streamlit Secrets

---

## 5️⃣ Test Deployment

1. Visit app URL
2. Go to **🔍 Search** tab
3. Search for: "Python developers"
4. Check **📊 Dashboard** for progress

✅ If you see leads, you're live!

---

## 🔗 Google Sheets (Optional)

For automatic lead export:

1. Create Google Service Account
2. Get JSON key
3. Share Sheet with service account email
4. In Secrets, add:
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_CREDENTIALS_JSON` (with the content of your key file)

See [DEPLOYMENT.md](./DEPLOYMENT.md#google-sheets-integration-setup) for details.

---

## 🔐 Security Checklist

- [ ] Database URL in Secrets
- [ ] Encryption key set
- [ ] API keys encrypted
- [ ] No credentials in repo
- [ ] Audit logging enabled
- [ ] Rate limiting active
- [ ] Error messages generic

---

## 📊 Monitor

### Sidebar shows:
- ✅ API key pool status
- ✅ Daily quotas
- ✅ System health

### Check logs:
Settings → View logs

---

## 🚀 You're Live!

Your system runs 24/7 on Streamlit Cloud. No maintenance needed.

[← Back to DEPLOYMENT.md](./DEPLOYMENT.md)
