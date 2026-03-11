"""
FastAPI backend for Lead Intelligence Platform
Replaces Streamlit UI with professional REST API + async job handling
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Add parent directory to path for lead_engine imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lead_engine.db.models import (
    SessionLocal, init_db, Lead, Job, Campaign, 
    AgentLog, AuditLog, ICPSettings
)
from lead_engine.core.supervisor import SupervisorAgent
from lead_engine.core.limiter import limiter
from lead_engine.core.key_manager import key_manager
from lead_engine.core.agent_chat import AssistantChat
from lead_engine.tools.google_sheets import GoogleSheetsTool
from lead_engine.security.audit import AuditLogger
from sqlalchemy import desc
from sqlalchemy.orm import Session

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize singleton instances
supervisor = SupervisorAgent()
chat_assistant = AssistantChat()
sheets_tool = GoogleSheetsTool()
audit_logger = AuditLogger()

# ============================================================================
# PYDANTIC SCHEMAS (Request/Response Models)
# ============================================================================

class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[dict] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SearchRequest(BaseModel):
    user_intent: str = Field(..., min_length=10, description="Detailed description of target audience")
    campaign_id: int
    max_leads: int = Field(default=50, ge=1, le=1000)
    sheet_id: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    name: str
    status: str
    leads_found: int
    max_leads: int
    created_at: datetime
    updated_at: datetime
    campaign_id: int
    
    class Config:
        from_attributes = True

class LeadResponse(BaseModel):
    id: int
    name: Optional[str]
    company: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    website: Optional[str]
    tech_stack: Optional[list]
    score: Optional[float]
    vetting_status: str
    country: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeadFilterRequest(BaseModel):
    search_key: Optional[str] = None
    vetting_status: Optional[str] = None  # 'good', 'junk', 'unvetted'
    min_score: Optional[float] = None
    sort_by: str = "newest"  # "newest" or "best_match"

class LeadVettingRequest(BaseModel):
    vetting_status: str  # 'good' or 'junk'
    feedback: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None

class AnalyticsResponse(BaseModel):
    total_campaigns: int
    total_leads: int
    active_jobs: int
    leads_by_status: dict
    leads_by_vetting: dict

class LogResponse(BaseModel):
    id: int
    message: str
    level: str
    timestamp: datetime
    agent_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class QuotaStatusResponse(BaseModel):
    provider: str
    used: int
    limit: int
    frequency: str
    
# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 FastAPI Backend Starting...")
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("🛑 FastAPI Backend Shutting Down...")

# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title="Lead Intelligence Platform API",
    description="Professional REST API for lead generation and management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def audit_action(action: str, user: str, resource_type: str, resource_id: str = None, details: dict = None):
    """Helper to log audit events"""
    try:
        audit_logger.log(
            action=action,
            user=user,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
    except Exception as e:
        logger.error(f"Failed to log audit: {e}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """System health status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "backend": "FastAPI",
        "version": "1.0.0"
    }

# ============================================================================
# CAMPAIGNS ENDPOINTS
# ============================================================================

@app.get("/api/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(db: Session = Depends(get_db)):
    """List all campaigns"""
    campaigns = db.query(Campaign).all()
    return campaigns

@app.post("/api/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Create a new campaign (target segment)"""
    try:
        new_campaign = Campaign(
            name=campaign.name,
            description=campaign.description,
            config=campaign.config or {},
            status='active'
        )
        db.add(new_campaign)
        db.commit()
        db.refresh(new_campaign)
        
        # Audit log
        if background_tasks:
            background_tasks.add_task(
                audit_action,
                "CREATE_CAMPAIGN",
                "api_user",
                "campaign",
                str(new_campaign.id),
                {"name": campaign.name}
            )
        
        logger.info(f"✅ Campaign created: {new_campaign.name} (ID: {new_campaign.id})")
        return new_campaign
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get campaign details"""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Delete a campaign"""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    db.delete(campaign)
    db.commit()
    
    if background_tasks:
        background_tasks.add_task(
            audit_action,
            "DELETE_CAMPAIGN",
            "api_user",
            "campaign",
            str(campaign_id),
            {"name": campaign.name}
        )
    
    return {"status": "deleted", "campaign_id": campaign_id}

# ============================================================================
# SEARCH & JOBS ENDPOINTS
# ============================================================================

@app.post("/api/search")
async def start_search(
    search: SearchRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Start a new lead search job"""
    try:
        # Validate campaign exists
        campaign = db.query(Campaign).get(search.campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Validate intent length
        if len(search.user_intent) < 10:
            raise HTTPException(
                status_code=400, 
                detail="User intent must be at least 10 characters"
            )
        
        # Create job using supervisor
        job_id = await supervisor.create_job(
            user_intent=search.user_intent,
            campaign_id=search.campaign_id,
            max_leads=search.max_leads,
            sheet_id=search.sheet_id,
            user="api_user"
        )
        
        if background_tasks:
            background_tasks.add_task(
                audit_action,
                "CREATE_JOB",
                "api_user",
                "job",
                str(job_id),
                {"campaign_id": search.campaign_id, "intent": search.user_intent[:50]}
            )
        
        logger.info(f"✅ Search job #{job_id} started")
        return {
            "status": "started",
            "job_id": job_id,
            "campaign_id": search.campaign_id
        }
    except Exception as e:
        logger.error(f"Failed to start search: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get job status and progress"""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/jobs/{job_id}/stop")
async def stop_job(
    job_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Stop a running job"""
    job = db.query(Job).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await supervisor.stop_job(job_id)
    
    if background_tasks:
        background_tasks.add_task(
            audit_action,
            "STOP_JOB",
            "api_user",
            "job",
            str(job_id)
        )
    
    return {"status": "stopped", "job_id": job_id}

@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(
    campaign_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering"""
    query = db.query(Job)
    
    if campaign_id:
        query = query.filter(Job.campaign_id == campaign_id)
    
    if status:
        query = query.filter(Job.status == status)
    
    jobs = query.order_by(desc(Job.created_at)).all()
    return jobs

# ============================================================================
# LEADS ENDPOINTS
# ============================================================================

@app.get("/api/leads", response_model=List[LeadResponse])
async def list_leads(
    campaign_id: Optional[int] = Query(None),
    search_key: Optional[str] = Query(None),
    vetting_status: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    sort_by: str = Query("newest"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List leads with advanced filtering"""
    query = db.query(Lead)
    
    # Filter by campaign
    if campaign_id:
        query = query.filter(Lead.campaign_id == campaign_id)
    
    # Search by name, company, or tech stack
    if search_key:
        from sqlalchemy import cast, String
        search_term = f"%{search_key}%"
        query = query.filter(
            (Lead.name.ilike(search_term)) |
            (Lead.company.ilike(search_term)) |
            (cast(Lead.tech_stack, String).ilike(search_term))
        )
    
    # Filter by vetting status
    if vetting_status and vetting_status != "all":
        query = query.filter(Lead.vetting_status == vetting_status)
    
    # Filter by minimum score
    if min_score is not None and min_score > 0:
        query = query.filter(Lead.score >= min_score)
    
    # Sort
    if sort_by == "best_match":
        query = query.order_by(desc(Lead.score))
    else:
        query = query.order_by(desc(Lead.created_at))
    
    # Pagination
    total = query.count()
    leads = query.offset(offset).limit(limit).all()
    
    return leads

@app.get("/api/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get lead details"""
    lead = db.query(Lead).get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.patch("/api/leads/{lead_id}/vetting")
async def update_lead_vetting(
    lead_id: int,
    vetting: LeadVettingRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Update lead vetting status"""
    lead = db.query(Lead).get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.vetting_status = vetting.vetting_status
    if vetting.feedback:
        lead.vetting_feedback = vetting.feedback
    
    db.commit()
    
    if background_tasks:
        background_tasks.add_task(
            audit_action,
            "VETTING_UPDATE",
            "api_user",
            "lead",
            str(lead_id),
            {"status": vetting.vetting_status}
        )
    
    return LeadResponse.from_orm(lead)

@app.post("/api/leads/export")
async def export_leads_to_sheets(
    campaign_id: Optional[int] = Query(None),
    vetting_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Export leads to Google Sheets"""
    try:
        query = db.query(Lead)
        
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        
        if vetting_status:
            query = query.filter(Lead.vetting_status == vetting_status)
        
        leads = query.all()
        
        if not leads:
            raise HTTPException(status_code=400, detail="No leads to export")
        
        success_count = 0
        for lead in leads:
            try:
                sheets_tool.sync_lead(lead)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to export lead {lead.id}: {e}")
                continue
        
        if background_tasks:
            background_tasks.add_task(
                audit_action,
                "EXPORT_LEADS",
                "api_user",
                "leads",
                None,
                {"count": success_count}
            )
        
        return {
            "status": "exported",
            "total_attempted": len(leads),
            "successful": success_count
        }
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/analytics", response_model=AnalyticsResponse)
async def get_analytics(campaign_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Get system-wide analytics"""
    try:
        total_campaigns = db.query(Campaign).count()
        
        query = db.query(Lead)
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        
        total_leads = query.count()
        active_jobs = db.query(Job).filter(Job.status.in_(['processing_intent', 'scraping'])).count()
        
        # Leads by status
        from sqlalchemy import func
        leads_by_status = {}
        status_query = db.query(Lead.status, func.count(Lead.id))
        if campaign_id:
            status_query = status_query.filter(Lead.campaign_id == campaign_id)
        for status, count in status_query.group_by(Lead.status).all():
            leads_by_status[status or 'unknown'] = count
        
        # Leads by vetting
        leads_by_vetting = {}
        vetting_query = db.query(Lead.vetting_status, func.count(Lead.id))
        if campaign_id:
            vetting_query = vetting_query.filter(Lead.campaign_id == campaign_id)
        for status, count in vetting_query.group_by(Lead.vetting_status).all():
            leads_by_vetting[status or 'unknown'] = count
        
        return AnalyticsResponse(
            total_campaigns=total_campaigns,
            total_leads=total_leads,
            active_jobs=active_jobs,
            leads_by_status=leads_by_status,
            leads_by_vetting=leads_by_vetting
        )
    except Exception as e:
        logger.error(f"Analytics query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.get("/api/analytics/distribution")
async def get_distribution_analytics(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get score and vetting status distribution for charts"""
    try:
        query = db.query(Lead)
        if campaign_id:
            query = query.filter(Lead.campaign_id == campaign_id)
        
        leads = query.all()
        
        # Score distribution (for histogram)
        scores = [l.score or 0.0 for l in leads]
        vetting_statuses = [l.vetting_status for l in leads]
        dates = [l.created_at.date().isoformat() if l.created_at else None for l in leads]
        
        # Group by date for trend
        from collections import Counter
        date_counts = Counter(dates)
        
        return {
            "scores": scores,
            "vetting_statuses": vetting_statuses,
            "trend_by_date": dict(sorted(date_counts.items()))
        }
    except Exception as e:
        logger.error(f"Distribution analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch distribution")

# ============================================================================
# LOGS ENDPOINTS
# ============================================================================

@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(
    log_type: str = Query("agent", regex="^(agent|audit)$"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get system logs"""
    try:
        if log_type == "agent":
            logs = db.query(AgentLog).order_by(desc(AgentLog.timestamp)).limit(limit).all()
        else:  # audit
            logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
        
        return logs
    except Exception as e:
        logger.error(f"Failed to fetch logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch logs")

# ============================================================================
# API KEY / QUOTA ENDPOINTS
# ============================================================================

@app.get("/api/quota-status")
async def get_quota_status():
    """Get API quota status for all providers"""
    try:
        status = limiter.get_quota_status()
        return {
            "providers": [
                {
                    "provider": provider,
                    "used": data.get("used", 0),
                    "limit": data.get("limit", 0),
                    "frequency": data.get("frequency", "monthly")
                }
                for provider, data in status.items()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get quota status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch quota status")

# ============================================================================
# CHAT / AI ASSISTANT ENDPOINTS
# ============================================================================

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    """Chat with AI assistant"""
    try:
        history = chat_request.history or []
        response = await chat_assistant.get_response(chat_request.message, history=history)
        
        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "status": "error",
        "detail": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )
