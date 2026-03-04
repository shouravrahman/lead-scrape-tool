import streamlit as st
import pandas as pd
import asyncio
import os
from lead_engine.db.models import SessionLocal, Lead, Job, AgentLog, Source
from lead_engine.core.supervisor import SupervisorAgent
from lead_engine.core.limiter import limiter
from lead_engine.core.key_manager import key_manager
from lead_engine.ui.styles import get_custom_css, get_card_html
from sqlalchemy import desc

st.set_page_config(page_title="Lead Intelligence System", layout="wide", initial_sidebar_state="collapsed")

if "supervisor" not in st.session_state:
    st.session_state.supervisor = SupervisorAgent()
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Inject Premium CSS ---
st.markdown(get_custom_css(st.session_state.theme), unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    sc1, sc2 = st.columns([4, 1])
    sc1.title("Settings")
    theme_icon = "🌙" if st.session_state.theme == "dark" else "☀️"
    if sc2.button(theme_icon, help="Toggle Theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    
    st.divider()
    
    with st.expander("🔑 API Key Pool", expanded=False):
        serp_keys = st.text_area("SerpAPI Keys (Quota: 100/mo free)", value=",".join(key_manager.keys["serpapi"]), placeholder="key1, key2...")
        serper_keys = st.text_area("Serper.dev Keys (Quota: 2500 free)", value=",".join(key_manager.keys["serper"]), placeholder="key1, key2...")
        tavily_keys = st.text_area("Tavily Keys (Quota: 1000/mo free)", value=",".join(key_manager.keys["tavily"]), placeholder="key1, key2...")
        firecrawl_keys = st.text_area("Firecrawl Keys (Quota: 500/mo free)", value=",".join(key_manager.keys["firecrawl"]), placeholder="key1, key2...")
        openrouter_keys = st.text_area("OpenRouter Keys", value=",".join(key_manager.keys["openrouter"]), placeholder="key1, key2...")
        
        if st.button("Update Keys"):
            key_manager.keys["serpapi"] = [k.strip() for k in serp_keys.split(",") if k.strip()]
            key_manager.keys["serper"] = [k.strip() for k in serper_keys.split(",") if k.strip()]
            key_manager.keys["tavily"] = [k.strip() for k in tavily_keys.split(",") if k.strip()]
            key_manager.keys["firecrawl"] = [k.strip() for k in firecrawl_keys.split(",") if k.strip()]
            key_manager.keys["openrouter"] = [k.strip() for k in openrouter_keys.split(",") if k.strip()]
            st.success("Keys updated!")
            st.rerun()

    st.subheader("📡 Provider Health")
    keys_status = key_manager.keys
    for s, k_list in keys_status.items():
        if s == "openai": continue # Keep fallback hidden for simplicity
        st.write(f"- {s.upper()}: {len(k_list)} keys")

    with st.expander("📊 Google Sheets Sync", expanded=False):
        sheet_id = st.text_input("Sheet ID", value=os.getenv("GOOGLE_SHEET_ID", ""), placeholder="e.g. 1a2b3c4d5e6f...")
        creds_file = st.text_input("Credentials JSON Path", value=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
        auto_sync = st.checkbox("Auto-Sync High Scores", value=os.getenv("AUTO_SYNC_TO_SHEETS") == "true")
        
        if st.button("Save Sheets Config"):
            # Update .env dynamically (simple version)
            os.environ["GOOGLE_SHEET_ID"] = sheet_id
            os.environ["GOOGLE_CREDENTIALS_FILE"] = creds_file
            os.environ["AUTO_SYNC_TO_SHEETS"] = "true" if auto_sync else "false"
            st.success("Config saved for current session!")

    st.divider()
    st.subheader("📉 API Quotas")
    quotas = limiter.get_quota_status()
    for service, data in quotas.items():
        used = data["used"]
        limit = data["daily_limit"]
        st.write(f"**{service.upper()}**: {used}/{limit}")
        st.progress(min(used/limit, 1.0))

# --- Main UI ---
# --- Header ---


tab1, tab2, tab3, tab4 = st.tabs(["📊 Stats", "🎯 Leads", "🔍 Search", "📜 Logs"])

with tab1:
    st.header("System Health & Yield")
    
    with SessionLocal() as db:
        total_leads = db.query(Lead).count()
        hot_leads = db.query(Lead).filter(Lead.score >= 15).count()
        active_jobs = db.query(Job).filter(Job.status.in_(['processing_intent', 'scraping'])).all()
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics with "Trends" (faked/simulated for now based on total)
    col1.markdown(get_card_html("Total Leads", total_leads, trend="12%", is_up=True, theme=st.session_state.theme), unsafe_allow_html=True)
    col2.markdown(get_card_html("Hot Leads", hot_leads, trend="5%", is_up=True, theme=st.session_state.theme), unsafe_allow_html=True)
    
    quality = (hot_leads/total_leads*100 if total_leads > 0 else 0)
    col3.markdown(get_card_html("Lead Quality", f"{quality:.1f}%", trend="2.4%", is_up=True, theme=st.session_state.theme), unsafe_allow_html=True)
    
    col4.markdown(get_card_html("Active Jobs", len(active_jobs), trend="Stable", is_up=True, theme=st.session_state.theme), unsafe_allow_html=True)
    
    if not active_jobs and total_leads == 0:
        st.markdown(f"""
        <div class="premium-card" style="border-left: 4px solid #10B981; margin-top: 20px;">
            <div style="font-family:'Outfit',sans-serif; font-size:18px; font-weight:700; margin-bottom:10px;">Ready to find leads?</div>
            <div style="font-size:14px; opacity:0.8; line-height:1.6;">
                Currently, there are no active tasks. Head over to the <b>🔍 Search</b> tab to define your target audience and launch your first scan. 
                The system will hunt for prospects and enrich their profiles in the background.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if active_jobs:
        st.subheader("Active Campaigns")
        for job in active_jobs:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**Job #{job.id}**: {job.name}")
            if c2.button("🛑 Stop", key=f"stop_{job.id}"):
                asyncio.run(st.session_state.supervisor.stop_job(job.id))
                st.rerun()

with tab2:
    st.header("🎯 Discovery Hub")
    
    # AI Filter Interface
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    fcol1, fcol2 = st.columns([4, 1])
    filter_query = fcol1.text_input("Filter leads via AI", placeholder="e.g. 'Show me only leads using React' or 'CTOs in Austin'")
    if fcol2.button("Apply Filter", use_container_width=True):
        if filter_query:
            st.session_state.filtered_leads = asyncio.run(st.session_state.supervisor.query_leads(filter_query))
        else:
            st.session_state.filtered_leads = None
            
    if st.button("Reset Filters"):
        st.session_state.filtered_leads = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    with SessionLocal() as db:
        if st.session_state.get('filtered_leads') is not None:
            leads = st.session_state.filtered_leads
        else:
            leads = db.query(Lead).order_by(desc(Lead.score)).all()
        
        if leads:
            for l in leads:
                is_hiring = "hiring" in str(l.raw_data).lower() or l.hiring_signal
                is_launch = any(k in str(l.raw_data).lower() for k in ["launch", "product hunt", "beta"])
                
                badges = []
                if is_hiring: badges.append('<span class="badge badge-hiring">💼 HIRING</span>')
                if is_launch: badges.append('<span class="badge badge-launch">🚀 LAUNCH</span>')
                if l.tech_stack: badges.append(f'<span class="badge badge-tech">🛠️ {l.tech_stack[0]}</span>')
                
                badge_html = " ".join(badges)
                
                # Card Container
                st.markdown(f"""
                <div class="premium-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
                        <div>
                            <div style="font-family:'Outfit',sans-serif; font-size:20px; font-weight:700; color:{st.session_state.theme == 'dark' and '#FFFFFF' or '#0F172A'}; margin-bottom:4px;">{l.name}</div>
                            <div style="color:#10B981; font-weight:600; font-size:14px; text-transform:uppercase; letter-spacing:0.5px;">{l.company}</div>
                        </div>
                        <div style="background:#10B98122; color:#10B981; padding:6px 12px; border-radius:8px; font-weight:800; font-size:14px;">{l.score} PTS</div>
                    </div>
                    <div style="margin-bottom:20px; display:flex; gap:8px; flex-wrap:wrap;">{badge_html}</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; font-size: 13px; color:{st.session_state.theme == 'dark' and '#E2E8F0' or '#334155'};">
                        <div>
                            <div style="opacity:0.5; font-weight:800; font-size:10px; letter-spacing:1px; margin-bottom:4px;">EMAIL</div>
                            <div style="font-weight:600;">{l.email if l.email else '<span style="color:#D97706;">Hunting...</span>'}</div>
                        </div>
                        <div>
                            <div style="opacity:0.5; font-weight:800; font-size:10px; letter-spacing:1px; margin-bottom:4px;">SOCIAL</div>
                            <div style="font-weight:600;"><a href="{l.linkedin_url}" target="_blank" style="color:inherit; text-decoration:none;">{l.linkedin_url if l.linkedin_url else 'N/A'}</a></div>
                        </div>
                        <div>
                            <div style="opacity:0.5; font-weight:800; font-size:10px; letter-spacing:1px; margin-bottom:4px;">TECH STACK</div>
                            <div style="font-weight:600;">{', '.join(l.tech_stack) if l.tech_stack else 'N/A'}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action Buttons (Balanced for mobile/desktop)
                c1, c2, c3 = st.columns(3)
                if c1.button("✅ Good", key=f"good_{l.id}"):
                    l.vetting_status = 'good'
                    db.commit()
                    st.rerun()
                if c2.button("❌ Junk", key=f"junk_{l.id}"):
                    l.vetting_status = 'junk'
                    db.commit()
                    st.rerun()
                if c3.button("📤 Sync", key=f"sync_{l.id}"):
                    st.session_state.supervisor.sheets.sync_lead(l)
                    st.success("Synced!")
        else:
            st.info("No leads found yet. Start a scan to find leads!")

with tab3:
    st.header("🔍 Start New Search")
    
    # Mission Config (No raw HTML wrap to avoid empty boxes)
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        user_intent = st.text_input("I am looking for...", placeholder="e.g. SaaS founders in Austin TX building AI tools")
    with col_b:
        target_sheet = st.text_input("Sheet ID (Optional)", placeholder="Leave blank for default")
    with col_c:
        max_leads = st.number_input("Limit", min_value=1, max_value=1000, value=50)

    if st.button("Start Search", use_container_width=True):
        if user_intent:
            job_id = asyncio.run(st.session_state.supervisor.create_job(user_intent, max_leads, sheet_id=target_sheet))
            st.success(f"Search Task #{job_id} started. See 'Logs' for activity.")
            st.rerun()
        else:
            st.warning("Please describe what you are looking for.")
    
    st.divider()
    
    # --- Search History ---
    st.subheader("📜 Search History")
    with SessionLocal() as db:
        past_jobs = db.query(Job).order_by(desc(Job.created_at)).all()
        
        if past_jobs:
            history_data = []
            for j in past_jobs:
                status_emoji = "✅" if j.status == 'completed' else "⏳" if j.status == 'scraping' else "❌" if j.status == 'failed' else "🛑"
                history_data.append({
                    "Task": j.name,
                    "Status": f"{status_emoji} {j.status.upper()}",
                    "Leads": j.leads_found,
                    "Goal": j.max_leads,
                    "Date": j.created_at.strftime("%Y-%m-%d %H:%M")
                })
            st.dataframe(history_data, use_container_width=True, hide_index=True)
        else:
            st.info("No past searches found.")

    if st.session_state.get("messages", []):
        st.divider()
        for message in st.session_state.get("messages", []):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

with tab4:
    st.header("📜 Activity Logs")

    with SessionLocal() as db:
        logs = db.query(AgentLog).order_by(desc(AgentLog.timestamp)).limit(50).all()
    
    if not logs:
        st.info("No logs captured yet. Launch a mission to see the agents in action!")
    
    for log in logs:
        color = "#10B981" if log.level == "INFO" else "#F59E0B"
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; padding: 14px 20px; margin-bottom: 12px; background: rgba({'255,255,255,0.02' if st.session_state.theme == 'dark' else '0,0,0,0.02'}); border-radius: 0 8px 8px 0; position: relative;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <div style="font-size: 11px; font-weight:800; opacity: 0.6; text-transform: uppercase; letter-spacing:1px; color:{color};">{log.agent_name}</div>
                <div style="font-size: 10px; opacity: 0.4;">{log.timestamp.strftime('%H:%S')}</div>
            </div>
            <div style="font-size: 14px; line-height:1.5; color:{'#E2E8F0' if st.session_state.theme == 'dark' else '#1E293B'};">{log.message}</div>
        </div>
        """, unsafe_allow_html=True)
