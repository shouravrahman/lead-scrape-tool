"""
Streamlit Cloud-ready UI with full security controls.
"""
import streamlit as st
import pandas as pd
import asyncio
import os
import plotly.express as px
from datetime import datetime, timedelta
from lead_engine.db.models import SessionLocal, Lead, Job, Campaign, init_db
from lead_engine.core.supervisor import SupervisorAgent
from lead_engine.core.limiter import limiter
from lead_engine.core.key_manager import key_manager
from lead_engine.core.agent_chat import chat_assistant
from lead_engine.ui.styles import get_custom_css, get_card_html
from lead_engine.schemas import SearchQuery, FilterQuery, LeadVetting
from lead_engine.security.errors import ErrorHandler, SecureError, ValidationError
from lead_engine.security.audit import AuditLogger
from lead_engine.tools.google_sheets import GoogleSheetsTool, GoogleSheetsSecurityError
from sqlalchemy import desc, cast, String
import traceback

# ============================================================================
# PAGE CONFIG & INITIALIZATION
# ============================================================================

# --- Page Config (MUST be first Streamlit UI command) ---
st.set_page_config(
    page_title="Lead Discovery Engine",
    page_icon="🎯",
    layout="wide",
)

# --- Global Assets (Cached) ---
@st.cache_resource
def get_supervisor():
    """Heavy initialization only once per server start."""
    init_db()
    return SupervisorAgent()

# --- Initial State Setup ---
if "active_campaign_id" not in st.session_state:
    st.session_state.active_campaign_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = "streamlit_user"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================================================
# MAIN EXECUTION WRAPPER (Global Safety Shield)
# ============================================================================
try:
    # --- Critical Startup ---
    supervisor = get_supervisor()

    # --- Sidebar ---
    with st.sidebar:
        # --- Sidebar Text Logo ---
        st.markdown(f'''
            <div style="text-align: center; margin: 0.5rem 0 2rem 0;">
                <p style="font-family: 'Outfit', sans-serif; font-size: 1.8rem; font-weight: 900; letter-spacing: -1px; color: #00FFA3; margin: 0; line-height: 1;">LEAD INTEL</p>
                <p style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 3px; font-weight: 600; margin-top: 4px; opacity: 0.8;">Intelligence Engine</p>
            </div>
        ''', unsafe_allow_html=True)

        # === Local/Cloud Indicator ===
        IS_CLOUD = os.getenv("STREAMLIT_RUNTIME_ENV") == "cloud" or os.getenv("HOME") == "/home/appuser"
        if IS_CLOUD:
            st.info("☁️ **Cloud Connectivity Active**")
        else:
            st.warning("🏠 **Local Workspace Engine**")

        # === Switch Audience ===
        st.subheader("👥 Choose Your Audience")
        with SessionLocal() as db:
            campaigns = db.query(Campaign).all()
            view_options = {"🌍 All People (Full List)": None}
            for c in campaigns:
                view_options[f"Group: {c.name}"] = c.id
            
            options_keys = list(view_options.keys())
            options_values = list(view_options.values())
            
            # Use index-based selection with a direct state update
            current_id = st.session_state.active_campaign_id
            default_idx = options_values.index(current_id) if current_id in options_values else 0

            target_label = st.selectbox(
                "Show Data For:", 
                options=options_keys,
                index=default_idx,
                help="Pick 'All People' to see everyone, or pick one group."
            )
            
            if view_options[target_label] != st.session_state.active_campaign_id:
                st.session_state.active_campaign_id = view_options[target_label]
                st.rerun()

        st.divider()

        # --- API Key Overiew ---
        st.subheader("🔑 Tools & Limits")
        with st.expander("Are the tools working?", expanded=False):
            status_data = limiter.get_quota_status()
            for provider, data in status_data.items():
                used = data.get("used", 0)
                limit = data.get("limit", 0)
                freq = data.get("frequency", "monthly")
                
                color = "🟢" if limit > 0 else "🔴"
                st.write(f"{color} **{provider.upper()}**: {used}/{limit} uses")
                if limit > 0:
                    st.progress(used / limit)
        
        # === Google Sheets Config ===
        with st.expander("📊 Sending to Sheets", expanded=False):
            sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
            auto_sync = os.getenv("AUTO_SYNC_TO_SHEETS", "false") == "true"
            
            # Status
            if sheet_id:
                st.success(f"✅ Sending to: {sheet_id[:12]}...")
            else:
                st.warning("❌ No Sheet Connected")
            
            st.caption(f"Send Automatically: {'YES' if auto_sync else 'NO'}")

        # === System Stats ===
        st.subheader("🖥️ App Stats")
        with SessionLocal() as db:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Total People", db.query(Lead).count())
            with c2:
                st.metric("Jobs Running", len(supervisor._active_jobs))
        
        st.divider()
        st.caption("AI Sidekick is Online")

    # --- Main Content Tabs ---
    tab_search, tab_leads, tab_segments, tab_analytics, tab_logs = st.tabs([
        "🚀 Find People", 
        "🎯 Leads List", 
        "📂 Manage Groups", 
        "📈 Stats", 
        "📜 History"
    ])

    with tab_search:
        st.header("🔍 Find New People")
        try:
            if not st.session_state.active_campaign_id:
                st.warning("⚠️ Please pick a group on the left side first.")
            else:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                with st.form("search_form", border=False):
                    st.subheader("🎯 Who are we looking for?")
                    user_intent = st.text_area(
                        "Describe the people you want to find...",
                        placeholder="e.g. 'Owners of pet shops in New York'",
                        help="The AI will use this to find the right people for you.",
                        height=120
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        job_name_suffix = st.text_input("Name this search", placeholder="e.g. Test 1")
                    with col2:
                        max_leads = st.number_input("How many people?", 1, 1000, 50)

                    sheet_id = st.text_input("Google Sheet ID (Optional)", placeholder="Leave blank if not sure")
                    submit = st.form_submit_button("🚀 Start Finding People", use_container_width=True, type="primary")
                st.markdown('</div>', unsafe_allow_html=True)

                if submit:
                    if not user_intent or len(user_intent) < 10:
                        st.error("❌ Please provide a more detailed target profile description.")
                    else:
                        job_id = asyncio.run(supervisor.create_job(
                            user_intent=user_intent,
                            campaign_id=st.session_state.active_campaign_id,
                            max_leads=max_leads,
                            sheet_id=sheet_id,
                            user=st.session_state.user_id
                        ))
                        st.success(f"✅ Search Job #{job_id} initiated for the selected segment!")
                        st.balloons()
        except Exception as e:
            st.error(f"Search Area Error: {e}")

        # Active Jobs section 
        with SessionLocal() as db:
            job_query = db.query(Job).filter(Job.status.in_(['processing_intent', 'scraping']))
            if st.session_state.active_campaign_id:
                job_query = job_query.filter(Job.campaign_id == st.session_state.active_campaign_id)
            
            active_jobs = job_query.order_by(desc(Job.created_at)).all()
            
            if active_jobs:
                st.divider()
                st.subheader(f"🔄 Active Jobs ({'Global' if not st.session_state.active_campaign_id else 'Selected Segment'})")
                for job in active_jobs:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**Job #{job.id}**: {job.name}")
                        st.caption(f"Leads: {job.leads_found}/{job.max_leads}")
                    with col2:
                        pct = (job.leads_found / job.max_leads) * 100 if job.max_leads > 0 else 0
                        st.progress(min(pct / 100, 1.0))
                    with col3:
                        if st.button("🛑 Stop", key=f"stop_{job.id}"):
                            asyncio.run(supervisor.stop_job(job.id))
                            st.rerun()

    with tab_leads:
        try:
            st.header("🎯 Your Leads List")
            with SessionLocal() as db:
                query = db.query(Lead)
                if st.session_state.active_campaign_id:
                    query = query.filter(Lead.campaign_id == st.session_state.active_campaign_id)
            
            with st.expander("🔍 Search, Filter & Send to Sheets", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    search_key = st.text_input("Find by Name or Skill", placeholder="e.g. 'React' or 'Designer'")
                    if search_key:
                        search_term = f"%{search_key}%"
                        query = query.filter(
                            (Lead.name.ilike(search_term)) | 
                            (Lead.company.ilike(search_term)) | 
                            (cast(Lead.tech_stack, String).ilike(search_term))
                        )
                with col2:
                    v_status = st.selectbox("Is this person a good fit?", ["Show Everyone", "good", "junk", "unvetted"])
                    if v_status != "Show Everyone":
                        query = query.filter(Lead.vetting_status == v_status)
                with col3:
                    min_score = st.number_input("Minimum Match Score", 0.0, 20.0, 0.0)
                    if min_score > 0:
                        query = query.filter(Lead.score >= min_score)
                
                if st.button("📤 Send All These People to Google Sheets", use_container_width=True):
                    filtered_leads = query.all()
                    if filtered_leads:
                        with st.spinner(f"Syncing {len(filtered_leads)} leads..."):
                            sheets = GoogleSheetsTool()
                            success_count = 0
                            for l in filtered_leads:
                                try:
                                    sheets.sync_lead(l)
                                    success_count += 1
                                except: continue
                            st.success(f"Successfully synced {success_count} leads!")
                    else:
                        st.warning("No leads found to sync.")

            sort_order = st.selectbox("How to show them?", ["Newest Found", "Best Matches First"])
            if sort_order == "Best Matches First":
                query = query.order_by(desc(Lead.score))
            else:
                query = query.order_by(desc(Lead.created_at))
                
            leads = query.limit(100).all()
            
            if not leads:
                st.info("We haven't found any people for this group yet.")
            else:
                st.write(f"We found {len(leads)} people")
                for lead in leads:
                    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"### {lead.name}")
                        st.write(f"**{lead.company}** | {lead.role or 'Decision Maker'}")
                        st.caption(f"📧 {lead.email or 'N/A'} | 🔗 [LinkedIn]({lead.linkedin_url or '#'})")
                        if lead.tech_stack:
                            st.markdown(f'<span class="badge badge-hiring">{lead.tech_stack}</span>', unsafe_allow_html=True)
                    with c2:
                        display_score = f"{lead.score:.1f}" if lead.score is not None else "0.0"
                        st.markdown(get_card_html("Match Score", display_score, trend="How Good", is_up=True), unsafe_allow_html=True)
                    with c3:
                        badge_color = "🟢" if lead.vetting_status == 'good' else "🔴" if lead.vetting_status == 'junk' else "🟡"
                        st.write(f"### {badge_color}")
                        st.caption(f"Fit: **{lead.vetting_status.upper()}**")
                    
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        if st.button("✅ Approve", key=f"g_{lead.id}", use_container_width=True):
                            lead.vetting_status = 'good'
                            db.commit(); st.rerun()
                    with ac2:
                        if st.button("❌ Reject", key=f"j_{lead.id}", use_container_width=True):
                            lead.vetting_status = 'junk'
                            db.commit(); st.rerun()
                    with ac3:
                        if st.button("📤 Export", key=f"ex_{lead.id}", use_container_width=True):
                            GoogleSheetsTool().sync_lead(lead)
                            st.success("Synced!")
                    st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"CRM Tab Error: {e}")
            st.info("Try refreshing the page or switching your View Scope.")

    with tab_segments:
        try:
            st.header("📂 Manage Audience Groups")
            with st.expander("➕ Make a New Group", expanded=False):
                with st.form("new_segment_form"):
                    c_name = st.text_input("Group Name", placeholder="e.g. New York Pet Shops")
                    c_desc = st.text_area("What is this group for?", placeholder="Helping pet shop owners get more customers")
                    template = st.selectbox("Industry", ["General", "Tech", "Local Business"])
                    submitted = st.form_submit_button("🚀 Create Group")
                    if submitted and c_name:
                        with SessionLocal() as db:
                            new_c = Campaign(name=c_name, description=c_desc, config={})
                            db.add(new_c)
                            db.commit()
                            st.success(f"Group '{c_name}' created!")
                            st.rerun()

            st.subheader("📋 Your Active Groups")
            with SessionLocal() as db:
                all_campaigns = db.query(Campaign).all()
                for c in all_campaigns:
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"### {c.name}")
                            st.write(c.description)
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_{c.id}"):
                                db.delete(c)
                                db.commit()
                                st.rerun()
        except Exception as e:
            st.error(f"Manage Groups Error: {e}")

    with tab_analytics:
        try:
            st.header("📈 How You Are Growing")
            with SessionLocal() as db:
                query = db.query(Lead)
                context_label = "Everything"
                if st.session_state.active_campaign_id:
                    query = query.filter(Lead.campaign_id == st.session_state.active_campaign_id)
                    context_label = f"Group #{st.session_state.active_campaign_id}"
                leads_data = query.all()
                if not leads_data:
                    st.info(f"We need to find more people in '{context_label}' to show stats.")
                else:
                    st.write(f"Stats for: **{context_label}**")
                    df = pd.DataFrame([{
                        "Score": l.score or 0.0,
                        "Status": l.vetting_status or "unvetted",
                        "Date": l.created_at.date() if l.created_at else datetime.now().date()
                    } for l in leads_data])
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("How good are they?")
                        fig = px.histogram(df, x="Score", nbins=10, color="Status", template="plotly_dark", color_discrete_map={"good": "#10B981", "junk": "#EF4444", "unvetted": "#F59E0B"})
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        st.subheader("Finding people over time")
                        trend_df = df.groupby("Date").size().reset_index(name="People Found")
                        fig2 = px.line(trend_df, x="Date", y="People Found", template="plotly_dark")
                        st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Analytics Tab Error: {e}")

    with tab_logs:
        try:
            st.header("📜 System Logs")
            col1, col2 = st.columns([1, 1], gap="medium")
            with col1:
                log_type = st.selectbox("Mode", ["Agent Activity", "Audit Trail"])
            with col2:
                log_limit = st.selectbox("Show Latest", [50, 100, 200, 500], index=1)
            with SessionLocal() as db:
                if log_type == "Agent Activity":
                    from lead_engine.db.models import AgentLog
                    logs = db.query(AgentLog).order_by(desc(AgentLog.timestamp)).limit(log_limit).all()
                    if not logs:
                        st.info("No agent activity captured yet.")
                    for log in logs:
                        with st.container(border=True):
                            st.write(f"**[{log.agent_name}]** {log.message}")
                            st.caption(f"{log.level} | {log.timestamp.strftime('%H:%M:%S')}")
                else:
                    from lead_engine.db.models import AuditLog
                    audits = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(log_limit).all()
                    if not audits:
                        st.info("No audit logs found.")
                    for audit in audits:
                        with st.container(border=True):
                            st.write(f"📁 **{audit.action}** ({audit.resource_type})")
                            st.caption(f"User: {audit.user} | {audit.timestamp.strftime('%H:%M:%S')}")
        except Exception as e:
            st.error(f"Logs Tab Error: {e}")

    # --- Floating AI Assistant (CSS Fix) ---
    st.markdown("""
        <style>
        div[data-testid="stPopover"] {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 999999;
        }
        div[data-testid="stPopover"] > button {
            width: 65px !important;
            height: 65px !important;
            border-radius: 50% !important;
            background-color: #00FFA3 !important;
            color: black !important;
            font-size: 28px !important;
            box-shadow: 0 12px 40px rgba(0, 255, 163, 0.5) !important;
            border: 2px solid #0B0C10 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        div[data-testid="stPopoverContent"] {
            width: 400px !important;
            max-width: 90vw !important;
            border-radius: 20px !important;
            background: rgba(17, 18, 24, 0.98) !important;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8) !important;
            bottom: 100px !important;
            right: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.popover("💬"):
        st.subheader("🤖 Intelligence Sidekick")
        st.write("I have site-wide knowledge of all leads and segments.")
        chat_box = st.container(height=450)
        with chat_box:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        if chat_prompt := st.chat_input("Ask about anything..."):
            st.session_state.chat_history.append({"role": "user", "content": chat_prompt})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(chat_prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        response = asyncio.run(chat_assistant.get_response(chat_prompt, history=st.session_state.chat_history[:-1]))
                        st.markdown(response)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

except Exception as global_e:
    # IMPORTANT: Don't catch Streamlit's own control flow exceptions
    if "RerunException" in type(global_e).__name__ or "StopException" in type(global_e).__name__:
        raise global_e
        
    st.error("🆘 **CRITICAL SYSTEM ERROR DETECTED**")
    st.warning("The app encountered an unexpected error. Please show this to support:")
    st.code(traceback.format_exc())
    if st.button("🔄 Attempt App Reset"):
        st.session_state.clear()
        st.cache_resource.clear()
        st.rerun()

st.caption("Intelligence Engine Active • Sidekick Online")
