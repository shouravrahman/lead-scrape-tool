# 🎯 Lead Intelligence Platform - FastAPI + Vue.js

A modern, scalable lead generation and prospect research platform with CrewAI-powered intelligent agents. Replaces Streamlit with FastAPI backend + Vue.js frontend for better performance, scalability, and architecture.

## 🎉 What This Is

**Professional SaaS lead discovery platform** for:
- 🔍 Finding high-intent prospects (SaaS founders, startups, agencies)
- 📊 Intelligent lead scoring and vetting
- 🤖 Multi-agent AI orchestration (CrewAI)
- 📱 Modern REST API + React-like SPA frontend
- 🔐 Encrypted data, audit logging, rate limiting

---

## ⚡ Quick Start (30 seconds)

```bash
cd lead-scrape-tool
./dev.sh install    # One-time setup
./dev.sh start      # Start both backend & frontend
```

Then open:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🛠️ Tech Stack

### Backend (FastAPI)
- **Framework**: FastAPI (async REST API)
- **ORM**: SQLAlchemy 2.0 + PostgreSQL
- **AI**: CrewAI (multi-agent orchestration)
- **LLM**: LiteLLM (OpenRouter, Gemini, Claude)
- **Security**: Encryption (Fernet), Rate limiting, Audit logging

### Frontend (Vue 3)
- **Framework**: Vue 3 Composition API
- **Build**: Vite (hot reload, ultra-fast)
- **State**: Pinia (reactive state management)
- **API**: Axios (HTTP client)
- **Charts**: Chart.js (analytics visualization)
- **Styling**: SCSS (dark theme, responsive)

### Data & Infrastructure
- **Database**: PostgreSQL (Neon.tech)
- **Scraping**: Serper, Tavily, SerpAPI, Firecrawl
- **Cloud**: Docker + Docker Compose

---

## 📂 Project Structure

```
backend/
├── main.py                    (707 lines - 22 REST endpoints)
├── requirements.txt           (25+ Python packages)
└── venv/                      (Python environment)

frontend/
├── src/
│   ├── App.vue                (Main component - 5 tabs)
│   ├── components/            (Reusable Vue components)
│   ├── stores/                (Pinia state management)
│   ├── api/                   (Axios HTTP client)
│   └── styles/                (SCSS + dark theme)
├── node_modules/              (71 npm packages)
└── vite.config.js             (Vite configuration)

lead_engine/                    (CrewAI agents - untouched)
├── core/                       (Supervisor, Crew, Chat, Keys, Limiter)
├── agents/                     (Planner, Extractor, Verifier)
├── tools/                      (Google Sheets, Search providers)
├── security/                   (Encryption, Audit logging)
└── db/                         (SQLAlchemy ORM models)

.env                            (Configuration - encrypted keys)
dev.sh                          (Setup & run script)
docker-compose.yml              (Container orchestration)
```

---

## � Features

✅ **Intelligent Lead Generation** - AI-powered prospect discovery
✅ **Multi-Source Scraping** - Google, LinkedIn, company sites, directories
✅ **Lead Scoring** - Automatic ICP matching and ranking
✅ **Campaign Management** - Organize leads into target groups
✅ **Google Sheets Export** - Auto-sync high-scoring prospects
✅ **Real-time Analytics** - Score distribution, trends, metrics
✅ **REST API** - 22 endpoints with auto-generated docs
✅ **Encrypted Storage** - PII fields encrypted at rest
✅ **Audit Logging** - Track all modifications
✅ **Rate Limiting** - Built-in protection
✅ **Dark Theme UI** - Modern, responsive frontend
✅ **Hot Reload** - Instant updates during development

---

## � API Endpoints (22 total)

**Health**: `/health`, `/api/quota-status`
**Search**: `POST /api/search`, `GET /api/jobs`, `GET /api/jobs/{id}`
**Leads**: `GET /api/leads`, `PATCH /api/leads/{id}`, `DELETE /api/leads/{id}`, `POST /api/leads/export`
**Campaigns**: `GET /api/campaigns`, `POST /api/campaigns`, `DELETE /api/campaigns/{id}`
**Analytics**: `GET /api/analytics`, `GET /api/analytics/distribution`
**Chat & Logs**: `POST /api/chat`, `GET /api/logs`

👉 **Full Docs**: http://localhost:8000/docs (when running)

---

## 🐍 Python Environment (VS Code Fix)

### Fix Red Squiggly Lines

**Quick Fix (1 minute):**
1. `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Python: Select Interpreter`
3. Choose: `./backend/venv/bin/python`
4. Restart VS Code

**Automatic Fix:**
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.analysis.extraPaths": ["${workspaceFolder}"]
}
```

### Why the Confusion?
- Old setup: `.venv/` in root (Streamlit)
- New setup: `backend/venv/` (FastAPI isolated)
- Solution: Tell VS Code about the new location

---

## 📋 Setup & Development

### First Time
```bash
./dev.sh install
```

### Daily Development
```bash
./dev.sh start
```

Runs both services:
- Backend: http://localhost:8000 (auto-reload)
- Frontend: http://localhost:5173 (hot reload)

### Configuration
```bash
cp .env.example .env
# Edit with your API keys: DATABASE_URL, OPENROUTER_API_KEYS, search keys, etc.
```

---

## � Documentation

- **[START_HERE.md](START_HERE.md)** — Full overview
- **[QUICKSTART.md](QUICKSTART.md)** — Quick start guide
- **[SECURITY.md](SECURITY.md)** — Security & encryption
- **[API Docs](http://localhost:8000/docs)** — Interactive Swagger UI

---

## 🚢 Production

### Docker
```bash
docker-compose up -d
```

### Manual
```bash
# Backend
cd backend && source venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0

# Frontend
cd frontend && npm run build && npx http-server dist/ -p 3000
```

---

## 📄 License

Proprietary - All rights reserved

**Last Updated**: March 2026 | **Status**: ✅ Production Ready
