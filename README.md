# 🎯 Autonomous Lead Intelligence System

An elite, multi-agent lead generation engine designed for high-volume discovery of SaaS founders, early-stage startups, and high-intent hiring signals. Pro-grade intelligence for developers and agencies.

## 🚀 Key Features

- **Multi-Agent Orchestration**: Specialized agents for Planning, Scraping, Extraction, Enrichment, and Scoring.
- **Cost-Zero Intelligence**: Optimized for **OpenRouter Free Models** (Gemini) and **Local Ollama** support (Llama3/Mistral) to eliminate LLM costs.
- **Elite Signal Intelligence**: Intelligent dorking targeting Product Hunt, Indie Hackers, Wellfound, Clutch, and LinkedIn.
- **Google Sheets Sync**: Real-time export and synchronization of high-quality leads to Google Sheets for outreach.
- **Advanced Google Dorks**: Autonomous generation of high-yield search operators.
- **API Key Pool & Rotation**: Built-in `KeyManager` for rotating through multiple SerpAPI, Firecrawl, and OpenRouter keys.
- **Autonomous Deep Hunting**: Automatically fills data gaps (missing emails/LinkedIn) for high-value leads.
- **Dynamic Feedback Loop**: Learns from operator feedback (Good/Junk) to refine ICP scoring.
- **Persistent Cloud Database**: [Neon](https://neon.tech) serverless PostgreSQL — free tier, always-on.
- **Sleek Operator Dashboard**: Real-time monitoring and chat-based control via Streamlit.

## 🛠️ Tech Stack

- **Core Logic**: Python (Asyncio)
- **Intelligence**: OpenRouter / OpenAI API
- **Scraping**: SerpAPI, Firecrawl
- **UI**: Streamlit (deployed on [Streamlit Community Cloud](https://streamlit.io/cloud))
- **Persistence**: SQLAlchemy + [Neon](https://neon.tech) PostgreSQL

## 🚦 Quick Start

1. **Clone & Install**:
   ```bash
   git clone <repo-url>
   cd lead-scrape-tool
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure**:
   Copy `.env.example` to `.env` and add your API keys.

3. **Initialize DB**:
   ```bash
   python -c "from lead_engine.db.models import init_db; init_db()"
   ```

4. **Run**:
   ```bash
   streamlit run streamlit_app.py
   ```

## 📈 Volume & Cost Analytics

The system is designed to scale horizontally by pooling keys. Below is an estimate of discovery volume based on your account tiers.

### 🆓 The "Zero Cost" Strategy (Multiple Free Keys)
By using `KeyManager` to pool multiple free-tier accounts, you can reach significant daily volume:

| Provider | Free Quota | 5-Key Pool Capacity | Purpose |
| :--- | :--- | :--- | :--- |
| **SerpAPI** | 100 searches/mo | **500 searches/mo** | Google Dorking (LinkedIn/GitHub) |
| **Firecrawl** | 500 scans/mo | **2,500 scans/mo** | Website Enrichment & Extraction |
| **Serper.dev**| 2,500 credits | **12,500 credits** | High-speed SERP fallback |
| **OpenRouter**| Unlimited (Free Models) | **N/A** | AI Planning & Lead Scoring |

**Total Discovery Capacity**: ~300-500 high-enrichment leads per month for $0.

### 💰 Professional Scaling (Paid Tiers)
If you switch to paid versions, the system can handle enterprise-grade volumes without code changes:

- **SerpAPI ($50/mo)**: 5,000 searches. *Potential: ~2,500 hot leads/mo.*
- **Firecrawl ($20/mo)**: 3,000+ credits. *Potential: Comprehensive tech profiling for thousands of domains.*
- **OpenRouter (Paid Models)**: Use Claude 3.5 Sonnet or GPT-4o for ultra-precise high-ticket lead vetting (~$0.01 per lead).

**Recommended for Agencies**: 1 Paid SerpAPI key + 1 Paid Firecrawl key = **3,000+ enriched leads/mo**.

## 📜 Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Case Study: Why & How](CASE_STUDY.md)
- [Walkthrough](walkthrough.md)

## 🛡️ License

MIT License. See `LICENSE` for details.
