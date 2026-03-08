# 🚀 Deployment & Scaling Guide

This guide covers local and production deployment for the Autonomous Lead Intelligence System.

---

## 📋 Quick Links

- **🌐 [Streamlit Cloud Deployment](./STREAMLIT_CLOUD_GUIDE.md)** ← Start here for cloud
- **💻 Local Deployment** (see below)
- **🔐 [Security](./SECURITY.md)**

---

## 💻 Local Deployment (Recommended for Development)

### Prerequisites
- Python 3.10+
- Virtual environment (`venv`)
- A [Neon](https://neon.tech) account (free) for the database

### Steps
1. **Setup Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

3. **Key Pooling**:
   For high-volume (500+ leads/day), add multiple API keys separated by commas:
   ```env
   SERP_API_KEYS=key1,key2,key3
   FIRECRAWL_API_KEYS=key1,key2
   ```

4. **Initialize DB & Run**:
   ```bash
   python -c "from lead_engine.db.models import init_db; init_db()"
   streamlit run streamlit_app.py
   ```

---

## 🗄️ Database Setup (Neon PostgreSQL — Free)

This system uses [Neon](https://neon.tech) as its persistent cloud database.
Neon is a serverless PostgreSQL provider with a generous free tier.

### 1. Create a Neon Project
1. Sign up at [neon.tech](https://neon.tech) (free, no credit card required).
2. Create a new **Project** — pick the region closest to you.
3. A default `neondb` database and `main` branch are created automatically.

### 2. Get the Connection String
1. Open your project dashboard.
2. Click **Connection Details** → select **Connection string**.
3. Copy the string — it looks like:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Add this as `DATABASE_URL` in your `.env` (local) or Streamlit Cloud Secrets (cloud).

---

## ☁️ Cloud Deployment (Streamlit Community Cloud — Free)

### 1. Push to GitHub
Ensure your repository is pushed to GitHub (public or private).

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **New app**.
3. Select your repository and set:
   - **Main file path**: `streamlit_app.py`
   - **Branch**: `main` (or your default branch)
4. Click **Advanced settings** → open the **Secrets** editor.

### 3. Add Secrets
Paste the following into the Secrets editor (fill in your real values):
```toml
DATABASE_URL          = "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require"
OPENROUTER_API_KEY    = "sk-or-..."
PLANNER_MODEL         = "google/gemini-flash-1.5-free"
EXTRACTOR_MODEL       = "google/gemini-flash-1.5-free"
SERP_API_KEYS         = "key1,key2"
SERPER_API_KEYS       = "key1"
TAVILY_API_KEYS       = "key1"
FIRECRAWL_API_KEYS    = "key1"
# For Google Sheets, paste the entire content of your credentials.json file as a single-line string.
GOOGLE_CREDENTIALS_JSON = '{"type": "service_account", ...}'
GOOGLE_SHEET_ID       = "your_sheet_id"
AUTO_SYNC_TO_SHEETS   = "true"
```
> See `.streamlit/secrets.toml.example` for a full reference.

4. Click **Deploy** — the app will be live in ~60 seconds.

> **Google Credentials**: To use Google Sheets sync on Streamlit Cloud, upload your `credentials.json` contents as a secret (paste the entire JSON as a single-line string under a key like `GOOGLE_CREDENTIALS_JSON`) and update `google_sheets.py` to parse it from the environment.

---

## 📊 Google Sheets Integration Setup

The system can automatically sync high-scoring leads to a Google Sheet.

### 1. Create a Google Service Account
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new **Project**.
3. Enable the **Google Sheets API** under **APIs & Services → Library**.
4. Go to **APIs & Services → Credentials → Create Credentials → Service Account**.
5. Download the JSON key file and rename it `credentials.json`.
6. Open the file, copy its content, and paste it into your `.env` file as `GOOGLE_CREDENTIALS_JSON` (wrap it in single quotes).

### 2. Configure the Sheet
1. Create a new Google Sheet.
2. Copy the **Sheet ID** from the URL.
3. Share the Sheet with the **Service Account Email** and give it **Editor** access.

### 3. Managing Multiple Sheets (Campaign Mode)

The system allows you to organize leads into different sheets for different campaigns without restarting the app.

- **Global Default**: The `GOOGLE_SHEET_ID` in your settings is used for general searches.
- **Campaign Specific**: When starting a new search in the UI, paste a specific **Sheet ID** into the "Campaign Sheet ID" field. Leads from that search will be routed exclusively to that sheet.

---

## 🧠 Local LLM with Ollama (100% Free)

Run the AI engine **locally for zero cost** with Ollama:

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/).
2. **Pull a Model**:
   ```bash
   ollama pull llama3
   ```
3. **Configure `.env`**:
   ```env
   OPENROUTER_API_KEY=none
   PLANNER_MODEL=llama3
   EXTRACTOR_MODEL=llama3
   OLLAMA_BASE_URL=http://localhost:11434/v1
   ```

---

## 📈 Scaling to 1000+ Leads/Day

1. **Model Choice**: Use `google/gemini-flash-1.5` (free) or a local Ollama instance.
2. **Key Rotation**: Use 3+ free-tier SerpAPI accounts. The `KeyManager` handles the rest.
3. **Rate Limiting**: Adjust `lead_engine/core/limiter.py` for higher throughput.
