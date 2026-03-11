# Premium UI Styles for Lead Intelligence System

def get_custom_css():
    """
    Definitive high-fidelity dark dashboard styles.
    """
    bg_color = "#0B0C10"
    card_bg = "#1A1C23"
    text_color = "#F8FAFC"
    sub_text = "#94A3B8"
    border_color = "rgba(255, 255, 255, 0.08)"
    accent_green = "#00FFA3" 
    accent_orange = "#FF9D00"
    sidebar_bg = "#111218"
    input_bg = "#0F172A"
    input_border = "rgba(255, 255, 255, 0.12)"
    shadow = "0 20px 60px rgba(0, 0, 0, 0.6)"
    glass_bg = "rgba(26, 28, 35, 0.7)"
    glass_border = "rgba(255, 255, 255, 0.1)"
    glow_shadow = f"0 0 20px {accent_green}33"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;700;800&display=swap');

    /* Global Transitions & Layout */
    * {{ transition: all 0.2s ease-out; box-sizing: border-box; }}
    
    .stApp {{
        background-color: {bg_color};
        font-family: 'Inter', sans-serif;
        color: {text_color};
        overflow-x: hidden !important;
    }}

    /* Card System */
    .premium-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 24px;
        box-shadow: {shadow};
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }}
    
    /* Subtle dot pattern background for cards */
    .premium-card::after {{
        content: "";
        position: absolute;
        top: -20px; right: -20px;
        width: 100px; height: 100px;
        background-image: radial-gradient({accent_green}22 2px, transparent 0);
        background-size: 16px 16px;
        opacity: 0.3;
        pointer-events: none;
    }}

    .premium-card:hover {{
        border-color: {accent_green}55;
        transform: translateY(-2px);
        box-shadow: {shadow.replace('0.6', '0.75')};
    }}

    /* Typography Scales */
    .metric-value {{
        font-family: 'Outfit', sans-serif;
        font-size: 38px;
        font-weight: 800;
        color: {text_color} !important;
        letter-spacing: -2px;
        line-height: 1;
        margin: 12px 0 4px 0;
    }}
    .metric-label {{
        font-size: 11px;
        font-weight: 700;
        color: {sub_text} !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}

    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border_color};
    }}
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
        gap: 1rem !important;
        padding-top: 0rem !important;
    }}
    
    /* Remove padding from the actual sidebar container */
    [data-testid="stSidebarUserContent"] {{
        padding-top: 2rem !important;
    }}

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div {{
        color: {text_color} !important;
    }}
    
    /* Floating Chat Widget */
    .floating-chat-trigger {{
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 65px;
        height: 65px;
        background: {accent_green};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 8px 32px {accent_green}66;
        z-index: 999999;
        font-size: 28px;
        border: 2px solid {bg_color};
    }}

    .floating-chat-trigger:hover {{
        transform: scale(1.1) rotate(5deg);
        box-shadow: 0 12px 40px {accent_green}88;
    }}

    /* Glass Panels */
    .glass-card {{
        background: {glass_bg} !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid {glass_border} !important;
        border-radius: 16px !important;
        padding: 24px !important;
    }}
    
    /* Input & Interactive Elements Overhaul */
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox [data-baseweb="select"] {{
        background-color: {input_bg} !important;
        border: 1px solid {input_border} !important;
        color: {text_color} !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
    }}
    
    ::placeholder {{
        color: {sub_text} !important;
        opacity: 0.6 !important;
    }}
    
    .stTextInput input:hover, .stTextArea textarea:hover, .stNumberInput input:hover {{
        border-color: {accent_green}aa !important;
    }}
    
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: {accent_green} !important;
        box-shadow: 0 0 0 3px {accent_green}22 !important;
    }}

    /* Range / Slider */
    .stSlider [data-baseweb="slider"] {{ 
        height: 6px !important; 
        margin: 20px 0 !important;
        background-color: {input_border} !important;
        border-radius: 3px !important;
    }}
    .stSlider [data-baseweb="thumb"] {{
        background-color: {accent_green} !important;
        border: 2px solid {card_bg} !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }}

    /* Buttons */
    .stButton>button {{
        background: {accent_green} !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 10px 24px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px {accent_green}44;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ border: none !important; gap: 12px !important; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {input_bg} !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        color: {sub_text} !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {accent_green} !important;
        color: #000000 !important;
    }}

    /* Badges */
    .badge {{
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        display: inline-block;
        white-space: nowrap;
    }}
    .badge-hiring {{ background: {accent_green}22; color: {accent_green}; border: 1px solid {accent_green}44; }}
    .badge-launch {{ background: {accent_orange}22; color: {accent_orange}; border: 1px solid {accent_orange}44; }}

    /* Responsive Adjustments */
    @media (max-width: 768px) {{
        .premium-card {{
            padding: 16px;
        }}
        .metric-value {{
            font-size: 28px;
        }}
        .metric-label {{
            font-size: 10px;
        }}
    }}

    /* Sidebar Logo & Spacing */
    /* Cleaned up image logo CSS */

    /* Global Text Guards */
    div, span, a {{
        word-break: break-word;
    }}

    /* Chat Message Styling */
    [data-testid="stChatMessage"] {{
        background-color: {input_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.5rem !important;
    }}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
        border-left: 3px solid {accent_green} !important;
    }}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
        border-left: 3px solid {accent_orange} !important;
    }}
    
    @media (max-width: 768px) {{
        .premium-card {{
            padding: 16px !important;
            margin-bottom: 16px !important;
        }}
        .glass-card {{
            padding: 16px !important;
        }}
        .metric-value {{
            font-size: 24px !important;
        }}
        
        /* Hide floating widget or make it smaller on mobile */
        div[data-testid="stPopover"] {{
            bottom: 15px !important;
            right: 15px !important;
        }}
        div[data-testid="stPopoverContent"] {{
            width: 85vw !important;
            max-width: 320px !important;
            bottom: 70px !important;
        }}
        
        /* Stack buttons on mobile if they get too squeezed */
        .stButton button {{
            width: 100% !important;
        }}
    }}

    @media (max-width: 480px) {{
        .stTabs [data-baseweb="tab"] {{
            padding: 8px 12px !important;
            font-size: 12px !important;
        }}
    }}
    
    </style>
    """

def get_card_html(label, value, trend=None, is_up=True):
    trend_color = "#00FFA3"
    if not is_up:
        trend_color = "#FF9D00"
        
    trend_html = ""
    if trend:
        arrow = "▲" if is_up else "▼"
        trend_html = f'<div style="color:{trend_color}; font-size:13px; font-weight:700; margin-top:6px; display:flex; align-items:center; gap:4px;">{arrow} {trend}</div>'
        
    return f"""
    <div class="premium-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {trend_html}
    </div>
    """
