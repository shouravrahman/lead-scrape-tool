"""
Streamlit Cloud-ready UI with full security controls.
"""
import streamlit as st
import pandas as pd
import asyncio
import os
from datetime import datetime
from lead_engine.db.models import SessionLocal, Lead, Job, AgentLog, AuditLog
from lead_engine.core.supervisor import SupervisorAgent
from lead_engine.core.limiter import limiter, RateLimitExceeded
from lead_engine.core.key_manager import key_manager
from lead_engine.core.resources import resource_monitor
from lead_engine.ui.styles import get_custom_css, get_card_html
from lead_engine.schemas import SearchQuery, FilterQuery, LeadVetting
from lead_engine.security.errors import ErrorHandler, SecureError, ValidationError
from lead_engine.security.audit import AuditLogger
from lead_engine.tools.google_sheets import GoogleSheetsTool, GoogleSheetsSecurityError
from sqlalchemy import desc
from pydantic import ValidationError as PydanticValidationError

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="Lead Intelligence System",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/shouravrahman/lead-scrape-tool",
        "Report a bug": "https://github.com/shouravrahman/lead-scrape-tool/issues",
        "About": "Autonomous Lead Generation Engine"
    }
)

# Detect cloud deployment
try:
    IS_CLOUD = "streamlit.app" in st.get_page_config().get("client", {}).get("serverBaseUrl", "")
except AttributeError:
    IS_CLOUD = os.getenv("IS_CLOUD", "false").lower() == "true"

# Initialize session state
if "supervisor" not in st.session_state:
    st.session_state.supervisor = SupervisorAgent()
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "streamlit_user"

# Inject custom CSS
st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    # Header
    col_title, col_theme = st.columns([4, 1])
    col_title.title("⚙️ Settings")
    
    theme_icon = "🌙" if st.session_state.theme == "dark" else "☀️"
    if col_theme.button(theme_icon, help="Toggle Theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    
    st.divider()
    
    # === API Key Management ===
    with st.expander("🔑 API Keys", expanded=False):
        if IS_CLOUD:
            st.info("""
            🔐 **Keys configured via Streamlit Secrets**
            
            To update:
            1. Settings > Secrets
            2. Edit SERP_API_KEYS, OPENROUTER_API_KEYS, etc.
            3. App reloads automatically
            """)
        else:
            st.warning("⚠️ **Local Mode** - Keys loaded from .env (encrypted)")
        
        # Show key health
        st.subheader("📡 Provider Status")
        providers = ["serpapi", "serper", "tavily", "firecrawl", "openrouter"]
        for provider in providers:
            count = len(key_manager.keys.get(provider, []))
            color = "🟢" if count > 0 else "🔴"
            st.write(f"{color} **{provider.upper()}**: {count} key(s)")
    
    st.divider()
    
    # === Google Sheets Config ===
    with st.expander("📊 Google Sheets", expanded=False):
        sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        auto_sync = os.getenv("AUTO_SYNC_TO_SHEETS", "false") == "true"
        
        if IS_CLOUD:
            st.info("""
            📊 **Configure via Secrets**
            
            Add to Streamlit Secrets:
            ```toml
            GOOGLE_SHEET_ID = "1a2b3c..."
            GOOGLE_CREDENTIALS_FILE = "service.json"
            AUTO_SYNC_TO_SHEETS = "true"
            ```
            """)
        
        # Status
        if sheet_id:
            st.success(f"✅ Sheet ID: {sheet_id[:15]}...")
        else:
            st.warning("❌ Not configured")
        
        st.write(f"Auto-Sync: {'✅ Enabled' if auto_sync else '❌ Disabled'}")
    
    st.divider()
    
    # === Quotas ===
    st.subheader("📉 Daily Quotas")
    try:
        quotas = limiter.get_quota_status()
        for service, data in quotas.items():
            used = data.get("used", 0)
            limit = data.get("limit", 0)
            if limit > 0:
                pct = min(used / limit, 1.0)
                st.write(f"**{service.upper()}**: {used}/{limit}")
                
                # Color bar based on usage
                if pct > 0.9:
                    st.progress(pct, text="🔴 CRITICAL")
                elif pct > 0.7:
                    st.progress(pct, text="🟡 WARNING")
                else:
                    st.progress(pct)
    except Exception as e:
        st.error(f"Quota error: {str(e)[:80]}")
    
    st.divider()
    
    # === System Status ===
    st.subheader("🖥️ System Health")
    try:
        status = resource_monitor.get_status()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Memory", f"{status['memory_rss_mb']:.0f} MB")
        with col2:
            st.metric("Uptime", f"{status['uptime_hours']:.1f}h")
        
        if resource_monitor.check_memory(threshold_mb=500):
            st.warning("⚠️ High memory usage")
    except Exception:
        st.info("Health check unavailable")

# ============================================================================
# MAIN CONTENT TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🎯 Leads",
    "🔍 Search",
    "📜 Logs",
    "❓ Help"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    st.header("📊 System Dashboard")
    
    try:
        with SessionLocal() as db:
            total_leads = db.query(Lead).count()
            hot_leads = db.query(Lead).filter(Lead.score >= 15).count()
            good_leads = db.query(Lead).filter(Lead.vetting_status == 'good').count()
            active_jobs = db.query(Job).filter(Job.status.in_(['processing_intent', 'scraping'])).all()
            completed_jobs = db.query(Job).filter(Job.status == 'completed').count()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", total_leads, delta="Discovered")
        with col2:
            st.metric("Hot Leads (15+ pts)", hot_leads, delta="High Quality")
        with col3:
            st.metric("Vetted (Good)", good_leads, delta="✅ Ready")
        with col4:
            st.metric("Active Jobs", len(active_jobs), delta="Running")
        
        # Quality metric
        if total_leads > 0:
            quality = (hot_leads / total_leads) * 100
            col_q = st.columns(1)[0]
            col_q.metric("Lead Quality Score", f"{quality:.1f}%", delta="Leads scoring 15+")
        
        # Job Status
        if active_jobs:
            st.subheader("🔄 Active Jobs")
            for job in active_jobs:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Job #{job.id}**: {job.name}")
                    if job.queries:
                        st.caption(f"Queries: {len(job.queries)} | Found: {job.leads_found}")
                
                with col2:
                    pct = (job.leads_found / job.max_leads) * 100 if job.max_leads > 0 else 0
                    st.progress(min(pct / 100, 1.0))
                
                with col3:
                    if st.button("🛑 Stop", key=f"stop_{job.id}"):
                        try:
                            asyncio.run(st.session_state.supervisor.stop_job(job.id))
                            AuditLogger.log('JOB_STOPPED', 'job', job.id, user=st.session_state.user_id)
                            st.success("✅ Job stopped")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to stop job: {str(e)[:100]}")
        
        elif total_leads == 0:
            st.info("💡 No leads yet. Start a search from the 🔍 **Search** tab!")
        
        # Recent activity
        st.subheader("📈 Recent Leads")
        with SessionLocal() as db:
            recent = db.query(Lead).order_by(desc(Lead.created_at)).limit(5).all()
            if recent:
                data = []
                for lead in recent:
                    data.append({
                        "Name": lead.name or "?",
                        "Company": lead.company or "?",
                        "Score": f"{lead.score:.1f}",
                        "Status": lead.vetting_status.upper(),
                        "Date": lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else "?"
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.caption("No leads discovered yet")
    
    except Exception as e:
        error_msg = ErrorHandler.log_and_sanitize(e, "Dashboard load failed")
        st.error(error_msg)

# ============================================================================
# TAB 2: LEADS
# ============================================================================
with tab2:
    st.header("🎯 Lead Management")
    
    try:
        # Filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_filter = st.text_input(
                "🔎 Filter by keyword",
                placeholder="e.g. 'React', 'CEO', 'Austin'",
                help="Searches name, company, tech stack"
            )
        
        with col2:
            status_filter = st.selectbox(
                "Status",
                ["All", "good", "junk", "pending"]
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Score (High→Low)", "Score (Low→High)", "Newest"]
            )
        
        # Load leads
        with SessionLocal() as db:
            query = db.query(Lead)
            
            # Apply filters
            if search_filter:
                search_term = f"%{search_filter}%"
                query = query.filter(
                    (Lead.name.ilike(search_term)) |
                    (Lead.company.ilike(search_term))
                )
            
            if status_filter != "All":
                query = query.filter(Lead.vetting_status == status_filter)
            
            # Sort
            if sort_by == "Newest":
                query = query.order_by(desc(Lead.created_at))
            elif sort_by == "Score (Low→High)":
                query = query.order_by(Lead.score)
            else:
                query = query.order_by(desc(Lead.score))
            
            # Pagination
            total_leads = query.count()
            page_size = 20
            total_pages = max(1, (total_leads + page_size - 1) // page_size)
            
            col_p1, col_p2 = st.columns([3, 1])
            with col_p1:
                st.write(f"Showing {total_leads} lead(s)")
            with col_p2:
                page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            
            offset = (page - 1) * page_size
            leads = query.offset(offset).limit(page_size).all()
        
        if not leads:
            st.info("No leads match your filters. Try adjusting them.")
        else:
            
            # Display leads
            for idx, lead in enumerate(leads):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{lead.name}** @ {lead.company}")
                        if lead.email:
                            st.caption(f"📧 {lead.email}")
                        if lead.linkedin_url:
                            st.caption(f"🔗 [LinkedIn]({lead.linkedin_url})")
                    
                    with col2:
                        st.metric("Score", f"{lead.score:.1f}")
                    
                    with col3:
                        # Status badge
                        status_colors = {
                            "good": "🟢",
                            "junk": "🔴",
                            "pending": "🟡"
                        }
                        st.write(f"{status_colors.get(lead.vetting_status, '⚪')} {lead.vetting_status.upper()}")
                    
                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("✅ Good", key=f"good_{lead.id}"):
                            try:
                                with SessionLocal() as db:
                                    l = db.query(Lead).get(lead.id)
                                    l.vetting_status = 'good'
                                    db.commit()
                                AuditLogger.log_lead_action('VET_GOOD', lead.id, user=st.session_state.user_id)
                                st.success("Marked as good!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {str(e)[:80]}")
                    
                    with col2:
                        if st.button("❌ Junk", key=f"junk_{lead.id}"):
                            try:
                                with SessionLocal() as db:
                                    l = db.query(Lead).get(lead.id)
                                    l.vetting_status = 'junk'
                                    db.commit()
                                AuditLogger.log_lead_action('VET_JUNK', lead.id, user=st.session_state.user_id)
                                st.info("Marked as junk")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Update failed: {str(e)[:80]}")
                    
                    with col3:
                        if st.button("📤 Export", key=f"export_{lead.id}"):
                            try:
                                # Find the sheet ID associated with the job that created this lead
                                with SessionLocal() as db:
                                    job = db.query(Job).filter(Job.id == lead.job_id).first()
                                    target_sheet_id = job.sheet_id if job else None
                                
                                sheets = GoogleSheetsTool()
                                # Pass the specific sheet_id for this lead's campaign
                                sheets.sync_lead(lead, override_sheet_id=target_sheet_id, user=st.session_state.user_id)
                                st.success("✅ Exported to Sheets!")
                            except GoogleSheetsSecurityError as e:
                                st.warning(f"⚠️ {str(e)[:100]}")
                            except Exception as e:
                                error_msg = ErrorHandler.log_and_sanitize(e, f"Export lead {lead.id}")
                                st.error(error_msg)
                    
                    with col4:
                        if st.button("ℹ️ Details", key=f"details_{lead.id}"):
                            with st.expander("Full Details", expanded=True):
                                st.json({
                                    "id": lead.id,
                                    "name": lead.name,
                                    "company": lead.company,
                                    "email": lead.email,
                                    "linkedin": lead.linkedin_url,
                                    "tech_stack": lead.tech_stack,
                                    "score": lead.score,
                                    "created_at": lead.created_at.isoformat() if lead.created_at else None
                                })
    
    except Exception as e:
        error_msg = ErrorHandler.log_and_sanitize(e, "Leads tab load failed")
        st.error(error_msg)

# ============================================================================
# TAB 3: SEARCH
# ============================================================================
with tab3:
    st.header("🔍 Start New Search")
    
    try:
        with st.form("search_form"):
            st.subheader("1. Campaign Details")
            col1, col2 = st.columns(2)
            with col1:
                campaign_name = st.text_input(
                    "Campaign Name",
                    placeholder="e.g. Q2 SaaS Outreach",
                    help="Give this search a memorable name."
                )
            with col2:
                max_leads = st.number_input(
                    "Max Leads",
                    min_value=1,
                    max_value=500,
                    value=50,
                    help="Target number of leads to find for this campaign."
                )

            st.subheader("2. AI Prompt")
            user_intent = st.text_area(
                "Describe your Ideal Lead Profile",
                placeholder="e.g. 'SaaS founders in Austin who recently raised a Series A and are hiring engineers'",
                help="This is the natural language prompt for the AI to find leads.",
                height=100
            )

            st.subheader("3. Export (Optional)")
            sheet_id = st.text_input(
                "Campaign Sheet ID",
                placeholder="Paste Google Sheet ID here",
                help="Optional. Paste a specific Google Sheet ID to send these leads to. If blank, uses the default sheet from settings."
            )
            
            submit = st.form_submit_button("🚀 Start Search", use_container_width=True, type="primary")

        if submit:
            if not campaign_name or len(campaign_name) < 3:
                st.error("❌ Please provide a campaign name (min 3 chars).")
            elif not user_intent or len(user_intent) < 10:
                st.error("❌ Please provide a more detailed AI prompt (min 10 chars).")
            else:
                try:
                    # Validate input
                    query = SearchQuery(
                        intent=user_intent,
                        max_leads=max_leads,
                        sheet_id=sheet_id
                    )
                    
                    # Create job
                    job_id = asyncio.run(
                        st.session_state.supervisor.create_job(
                            user_intent=query.intent,
                            campaign_name=campaign_name,
                            max_leads=query.max_leads,
                            sheet_id=query.sheet_id,
                            user=st.session_state.user_id
                        )
                    )
                    
                    AuditLogger.log(
                        'CREATE_JOB',
                        resource_type='job',
                        resource_id=str(job_id),
                        details={'campaign': campaign_name, 'intent': user_intent[:50], 'max_leads': max_leads},
                        user=st.session_state.user_id
                    )
                    
                    st.success(f"✅ Search #{job_id} started!")
                    st.info("👉 Check Dashboard tab for live progress")
                
                except PydanticValidationError as e:
                    st.error(f"❌ Invalid input: {e.errors()[0]['msg']}")
                except Exception as e:
                    error_msg = ErrorHandler.log_and_sanitize(e, f"Create job")
                    st.error(error_msg)
        
        # History
        st.divider()
        st.subheader("📜 Search History")
        
        try:
            with SessionLocal() as db:
                jobs = db.query(Job).order_by(desc(Job.created_at)).limit(20).all()
                
                if jobs:
                    history_data = []
                    for j in jobs:
                        status_icons = {
                            'completed': '✅',
                            'scraping': '⏳',
                            'processing_intent': '🤔',
                            'failed': '❌',
                            'stopped': '🛑'
                        }
                        
                        history_data.append({
                            "ID": j.id,
                            "Campaign": j.name[:40],
                            "Status": f"{status_icons.get(j.status, '❓')} {j.status}",
                            "Leads": f"{j.leads_found}/{j.max_leads}",
                            "Date": j.created_at.strftime("%m/%d %H:%M") if j.created_at else "?"
                        })
                    
                    st.dataframe(
                        pd.DataFrame(history_data),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No search history yet")
        except Exception as e:
            st.error(f"Failed to load history: {str(e)[:80]}")
    
    except Exception as e:
        error_msg = ErrorHandler.log_and_sanitize(e, "Search tab error")
        st.error(error_msg)

# ============================================================================
# TAB 4: LOGS
# ============================================================================
with tab4:
    st.header("📜 Activity Logs")
    
    try:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            log_type = st.selectbox(
                "Log Type",
                ["Agent Logs", "Audit Trail"],
                help="View agent activity or security audit"
            )
        
        with col2:
            limit = st.select_slider("Show last N entries", 10, 100, 50)
        
        with SessionLocal() as db:
            if log_type == "Agent Logs":
                logs = db.query(AgentLog).order_by(desc(AgentLog.timestamp)).limit(limit).all()
                
                if logs:
                    for log in logs:
                        color = "#10B981" if log.level == "INFO" else "#F59E0B" if log.level == "WARNING" else "#EF4444"
                        
                        with st.container(border=True):
                            col1, col2 = st.columns([4, 1])
                            
                            with col1:
                                st.write(f"**[{log.agent_name}]** {log.message}")
                            
                            with col2:
                                st.caption(log.timestamp.strftime("%H:%M:%S"))
                else:
                    st.info("No logs yet")
            
            else:  # Audit Trail
                audits = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
                
                if audits:
                    for audit in audits:
                        action_icons = {
                            'CREATE_JOB': '🆕',
                            'VET_GOOD': '✅',
                            'VET_JUNK': '❌',
                            'EXPORT_TO_SHEETS': '📤',
                            'ROTATE_KEY': '🔄',
                            'API_CALL': '📡'
                        }
                        
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            
                            with col1:
                                icon = action_icons.get(audit.action, '📋')
                                st.write(f"{icon} **{audit.action}**")
                            
                            with col2:
                                st.caption(f"User: {audit.user}")
                            
                            with col3:
                                st.caption(audit.timestamp.strftime("%H:%M:%S"))
                else:
                    st.info("No audit entries yet")
    
    except Exception as e:
        st.error(f"Failed to load logs: {str(e)[:100]}")

# ============================================================================
# TAB 5: HELP
# ============================================================================
with tab5:
    st.header("❓ Help & Documentation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Quick Start")
        st.write("""
        1. **Start a Search** (🔍 tab)
           - Describe your target audience
           - Set max leads limit
           - Click "Start Search"
        
        2. **Monitor Progress** (📊 tab)
           - Watch active jobs in real-time
           - See discovered leads
           - Stop jobs if needed
        
        3. **Review Leads** (🎯 tab)
           - Mark as Good/Junk
           - Filter & sort
           - Export to Google Sheets
        """)
    
    with col2:
        st.subheader("⚙️ Configuration")
        st.write("""
        **API Keys** (⚙️ sidebar)
        - Local: Edit in `.env`
        - Cloud: Streamlit Secrets
        
        **Google Sheets** (⚙️ sidebar)
        - Add credentials via Secrets
        - Enable Auto-Sync
        - Leads auto-export on completion
        
        **Quotas** (⚙️ sidebar)
        - View daily API usage
        - Yellow: 70%+ usage
        - Red: 90%+ usage
        """)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 What is 'Score'?")
        st.write("""
        Leads are scored 0-20 points based on:
        - **Founder/CTO role** (+5)
        - **Active company** (+5)
        - **Hiring signal** (+6)
        - **Launch momentum** (+4)
        - **Tech stack match** (+7)
        
        **15+**: Hot leads 🔥
        **10-14**: Warm leads 🟡
        **<10**: Cold leads ❄️
        """)
    
    with col2:
        st.subheader("🔐 Security")
        st.write("""
        ✅ All API keys encrypted
        ✅ Database fields encrypted
        ✅ No plaintext credentials
        ✅ Audit logging
        ✅ Rate limiting
        ✅ Input validation
        
        [View Security Audit](https://github.com/shouravrahman/lead-scrape-tool/blob/master/SECURITY_AUDIT.md)
        """)
    
    st.divider()
    
    st.subheader("🔗 Resources")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📖 Full Documentation", use_container_width=True):
            st.info("See README.md in repository")
    
    with col2:
        if st.button("🐛 Report Bug", use_container_width=True):
            st.info("GitHub Issues: github.com/shouravrahman/lead-scrape-tool")
    
    with col3:
        if st.button("💬 Discussions", use_container_width=True):
            st.info("GitHub Discussions for questions")
    
    st.divider()
    
    st.caption("""
    **Autonomous Lead Intelligence System** | v2.0 (Hardened)
    
    🔒 Security Enhanced | 🚀 Production Ready | ☁️ Streamlit Cloud Compatible
    """)
