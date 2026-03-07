from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, create_engine, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy_utils import StringEncryptedType
import os

Base = declarative_base()

# Get encryption key for database fields
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if ENCRYPTION_KEY:
    EncryptedString = lambda: StringEncryptedType(String, ENCRYPTION_KEY)
else:
    # Fallback: use regular String if encryption key not available
    # ⚠️ This is not secure! Only for development.
    def EncryptedString():
        import logging
        logging.warning("⚠️  ENCRYPTION_KEY not set. Using plaintext database. Set ENCRYPTION_KEY immediately!")
        return String

class Lead(Base):
    __tablename__ = 'leads'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    company = Column(String)
    # 🔐 Encrypt PII
    email = Column(EncryptedString(), unique=True)
    linkedin_url = Column(EncryptedString())
    website = Column(String)
    tech_stack = Column(JSON)  # List of technologies
    # 🔐 Encrypt hiring signal (may contain scraped personal data)
    hiring_signal = Column(EncryptedString())
    score = Column(Float, default=0.0)
    status = Column(String, default='pending')  # pending, contacted, ignored, personal_outreach
    vetting_status = Column(String, default='unvetted')  # unvetted, good, junk
    vetting_feedback = Column(Text)
    country = Column(String)
    source_url = Column(String)
    raw_data = Column(JSON)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_lead_job_id', 'job_id'),
        Index('idx_lead_score', 'score'),
        Index('idx_lead_status', 'status'),
    )

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)  # e.g., "SaaS Founders in US"
    status = Column(String, default='idle')  # idle, running, completed, failed
    queries = Column(JSON)  # List of generated queries
    sources = Column(JSON)  # Sources used
    leads_found = Column(Integer, default=0)
    max_leads = Column(Integer, default=100)  # Max leads to find
    sheet_id = Column(String)  # Target Google Sheet for this search
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # serp, reddit, github, etc.
    leads_count = Column(Integer, default=0)
    hot_leads_count = Column(Integer, default=0)
    yield_rate = Column(Float, default=0.0)

class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'))
    agent_name = Column(String)
    message = Column(Text)
    level = Column(String, default='INFO')
    timestamp = Column(DateTime, default=datetime.utcnow)

class ICPSettings(Base):
    __tablename__ = 'icp_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(JSON)
    description = Column(String)


class AuditLog(Base):
    """Immutable audit trail for compliance and security monitoring"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    action = Column(String(50), nullable=False)  # 'CREATE_JOB', 'EXPORT_LEAD', 'ROTATE_KEY', etc.
    user = Column(String(100), nullable=False)  # Username or 'system'
    resource_type = Column(String(50))  # 'lead', 'job', 'key', etc.
    resource_id = Column(String(100))
    # Details stored encrypted if sensitive
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(50))  # Optional: for cloud deployments
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_user', 'user'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

# Database Setup
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "For local dev, add it to your .env file. "
        "For Streamlit Cloud, add it to your app Secrets."
    )

# pool_pre_ping: reconnects dropped connections (important for Neon serverless)
# pool_recycle: recycles connections before Neon's 5-min idle timeout
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
