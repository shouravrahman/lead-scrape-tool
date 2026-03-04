"""
Streamlit Cloud entrypoint.
Streamlit Cloud requires the main file to live in the project root.
This wrapper initialises the database schema then loads the app.
"""
import os
from dotenv import load_dotenv

# Load .env for local dev (no-op on Streamlit Cloud where secrets are injected)
load_dotenv()

# Expose Streamlit secrets as env vars so the rest of the codebase
# can use os.getenv() uniformly (works both locally and on Streamlit Cloud)
try:
    import streamlit as st
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ.setdefault(key, value)
except Exception:
    pass  # Not running under Streamlit (e.g. during testing)

from lead_engine.db.models import init_db
init_db()

# Import the app module — Streamlit will execute it as the active page
import lead_engine.ui.app  # noqa: F401, E402
