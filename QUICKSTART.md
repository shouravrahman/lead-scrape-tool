# 🚀 Quick Start Guide

## 🎯 One-Command Setup

```bash
cd /home/shourav/DIGITAL_PRODUCTS/lead-scrape-tool
./dev.sh install
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies (FastAPI, CrewAI, SQLAlchemy, etc.)
- ✅ Install all Node.js dependencies (Vue 3, Vite, etc.)
- ✅ Prepare both backend and frontend for development

---

## ▶️ Start Development

```bash
./dev.sh start
```

This starts both services simultaneously:
- **Backend API**: `http://localhost:8000` (FastAPI)
- **Frontend UI**: `http://localhost:5173` (Vue 3)
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

---

## 📱 Access the App

### Frontend (Main Interface)
Open browser to: **http://localhost:5173**

Features available:
1. **Search** - Create new lead generation jobs
2. **Leads** - View and manage all discovered leads
3. **Campaigns** - Organize leads into campaigns
4. **Analytics** - View lead scoring distribution & statistics
5. **Logs** - Monitor job execution and audit trail

### Backend API
- **Base URL**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs` (Interactive Swagger UI)
- **Health Check**: `curl http://localhost:8000/health`

---

## 🔧 Individual Commands

### Backend Only
```bash
./dev.sh backend
```
Runs FastAPI server on port 8000 with auto-reload

### Frontend Only
```bash
./dev.sh frontend
```
Runs Vite dev server on port 5173 with hot reload

### Build for Production
```bash
./dev.sh build
```
Creates optimized build in `frontend/dist/`

---

## 🌍 Environment Setup

The application uses `.env` file for configuration:

```bash
# Copy template if needed
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required variables:**
- `DATABASE_URL` - PostgreSQL connection (already configured for Neon)
- `ENCRYPTION_KEY` - Encryption key for sensitive data
- `OPENROUTER_API_KEYS` - LLM API keys
- `SERPER_API_KEYS`, `TAVILY_API_KEYS`, etc. - Search provider keys
- `GOOGLE_SHEET_ID` - Target Google Sheet
- `GOOGLE_CREDENTIALS_JSON` - Google service account

All keys can be comma-separated for multi-key rotation.

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Ensure venv is properly set up
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Frontend won't build
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
npm run dev
```

### Database connection error
```bash
# Verify DATABASE_URL in .env is correct
# Test with: python -c "from lead_engine.db.models import SessionLocal; SessionLocal()"
```

### CrewAI agent not running
```bash
# Ensure all API keys are set in .env
# Check logs in frontend Logs tab or backend console output
# Verify agent models are available (PLANNER_MODEL, EXTRACTOR_MODEL, ASSISTANT_MODEL)
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│         Frontend (Vue 3 + Vite)                      │
│  http://localhost:5173                               │
│  - SearchView                                        │
│  - LeadsView                                         │
│  - CampaignsView                                     │
│  - AnalyticsView                                     │
│  - LogsView                                          │
└────────────────────┬────────────────────────────────┘
                     │ Axios HTTP Client
                     │ Vite Proxy: /api → localhost:8000
                     ▼
┌─────────────────────────────────────────────────────┐
│  Backend (FastAPI + CrewAI)                         │
│  http://localhost:8000                               │
│  - REST API Endpoints (22 routes)                    │
│  - CrewAI Agent Orchestration                        │
│  - Job Execution & Async Tasks                       │
│  - Google Sheets Integration                         │
└────────────────────┬────────────────────────────────┘
                     │ SQLAlchemy ORM
                     │ PostgreSQL (Neon)
                     ▼
┌─────────────────────────────────────────────────────┐
│  Database (PostgreSQL on Neon)                       │
│  - Leads, Jobs, Campaigns                            │
│  - Agent Logs & Audit Trail                          │
│  - Encrypted Fields (PII)                            │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI REST API with 22 endpoints |
| `backend/requirements.txt` | Python dependencies |
| `frontend/src/App.vue` | Main Vue component with 5 tabs |
| `frontend/package.json` | Node.js dependencies |
| `.env` | Configuration (production values - encrypted) |
| `dev.sh` | Development setup & run script |
| `lead_engine/` | CrewAI agent orchestration (untouched) |

---

## ✨ Features

### Lead Generation
1. **Intelligent Search** - Describe your target audience
2. **Multi-Source Scraping** - Google, Serper, Tavily, Firecrawl
3. **AI Extraction** - CrewAI agents extract structured data
4. **Lead Scoring** - Automatic scoring based on ICP match

### Lead Management
- View all discovered leads
- Manual vetting & status updates
- Export to Google Sheets
- Organize into campaigns
- Filter & search capabilities

### Analytics
- Lead score distribution charts
- Country/domain breakdowns
- Real-time statistics
- Audit trail of all actions

### Job Tracking
- Real-time job status updates
- Agent execution logs
- Error tracking
- Performance metrics

---

## 🔐 Security

✅ **Encryption at Rest**
- API keys encrypted in `.env`
- Database PII fields encrypted
- Credentials secured with Fernet

✅ **API Security**
- CORS middleware enabled
- Rate limiting active
- Request validation with Pydantic

✅ **Audit Logging**
- All modifications logged
- User actions tracked
- Compliance ready

---

## 📞 Support

### Check Logs
```bash
# Backend logs (live)
tail -f /tmp/backend.log

# Frontend logs
# Open browser DevTools → Console
```

### Debug Mode
```bash
# Backend with verbose output
DEBUG=1 ./dev.sh backend

# Frontend with source maps
npm run dev
```

### Verify Integration
```bash
# Test imports work
cd /home/shourav/DIGITAL_PRODUCTS/lead-scrape-tool
source backend/venv/bin/activate
python -c "from lead_engine.core.supervisor import SupervisorAgent; print('✅ OK')"
```

---

## 🎉 You're Ready!

Everything is set up and verified. The application combines:
- **Modern Frontend** - Vue 3 with responsive UI
- **Scalable Backend** - FastAPI with async processing
- **Intelligent Agents** - CrewAI for automated research
- **Secure Data** - Encrypted at rest, audit trail
- **Production Ready** - Docker, documentation, error handling

Start with: `./dev.sh start` 🚀
