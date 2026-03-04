# 🚀 Deployment & Scaling Guide

This guide covers local and production deployment for the Autonomous Lead Intelligence System.

## 💻 Local Deployment (Recommended)

The system is optimized for local-first execution to maintain data privacy and speed.

### Prerequisites
- Python 3.10+
- Virtual environment (`venv`)

### Steps
1. **Setup Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Key Pooling**:
   Add your keys to `.env`. For high-volume (500+ leads/day), add multiple keys separated by commas:
   ```env
   SERP_API_KEYS=key1,key2,key3
   FIRECRAWL_API_KEYS=key1,key2
   ```

## 📊 Google Sheets Integration Setup

The system can automatically sync high-scoring leads to a Google Sheet. Follow these steps to set it up:

### 1. Create a Google Service Account
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new **Project**.
3.  Navigate to **APIs & Services > Library**, search for **Google Sheets API**, and click **Enable**.
4.  Navigate to **APIs & Services > Credentials**.
5.  Click **Create Credentials > Service Account**.
6.  Give it a name (e.g., "Lead-Scraper") and click **Create and Continue**. Skip optional steps and click **Done**.
7.  Click on the newly created Service Account email, go to the **Keys** tab, and click **Add Key > Create New Key**. Select **JSON** and download the file.
8.  Rename this file to `credentials.json` and place it in the root of the project.

### 2. Configure the Sheet
1.  Create a new Google Sheet.
2.  Copy the **Sheet ID** from the URL (the long string between `/d/` and `/edit`).
3.  **Crucial**: Share the Google Sheet with the **Service Account Email** (found in your `.json` file) and give it "Editor" access.

## ☁️ Cloud Deployment (Render)

The system is fully compatible with **Render**. It includes a `render.yaml` blueprint for one-click deployment.

### 1. Blueprint Setup
1. Fork the repository to your GitHub.
2. In the Render Dashboard, click **New > Blueprint**.
3. Select your forked repository.

### 2. Configuration & Persistence
Render will automatically detect the `render.yaml` file. It will create:
- **Web Service**: Running the Streamlit dashboard.
- **Persistent Disk**: A 1GB disk mounted at `/data` to keep your leads safe between deployments.

### 3. Environment Secrets
You MUST manually add the following as **Environment Variables** (or Secret Files) in the Render dashboard:
- `OPENROUTER_API_KEY`: For AI planning.
- `SERPER_API_KEYS`: Comma-separated search keys.
- `GOOGLE_SHEET_ID`: Your target sheet.
- `GOOGLE_CREDENTIALS_FILE`: Set this to `credentials.json`.
- `AUTO_SYNC_TO_SHEETS`: Set to `true`.

**Note**: To upload `credentials.json` on Render, go to **Dashboard > [Specific Service] > Environment > Secret Files** and upload your JSON file there.

## 🧠 Local LLM with Ollama (100% Free)

If you have a modern Mac or PC with an M-series chip or NVIDIA GPU, you can run the entire intelligence engine **locally for zero cost**.

1.  **Install Ollama**: Download from [ollama.com](https://ollama.com/).
2.  **Pull a Model**: 
    ```bash
    ollama pull llama3
    ```
3.  **Configure `.env`**:
    ```env
    OPENROUTER_API_KEY=none
    PLANNER_MODEL=llama3
    EXTRACTOR_MODEL=llama3
    # Uncomment this in your .env:
    # OLLAMA_BASE_URL=http://localhost:11434/v1
    ```

## 📈 Scaling to 1000+ Leads/Day
To achieve high volume without high costs:
1. **Model Choice**: Set `EXTRACTOR_MODEL=google/gemini-flash-1.5` or use a local Ollama instance for extremely low-cost extraction.
2. **Key Rotation**: Use 3+ free-tier SerpAPI accounts. The `KeyManager` handles the rest.
3. **Rate Limiting**: The system defaults to conservative delays. Adjust `lead_engine/core/limiter.py` if needed.
