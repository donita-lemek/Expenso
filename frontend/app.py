"""
frontend/app.py
Expenso — Streamlit multi-page application entry point with secure role routing.
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from frontend.components import profile_widget

st.set_page_config(
    page_title="Expenso",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────
# Hide Streamlit specific UI artifacts, hide default navigation
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Hide standard Streamlit footer */
    footer { visibility: hidden; }

    /* Deep Glassmorphism background */
    .stApp {
        background: radial-gradient(circle at 15% 50%, #081121, #03060C 60%);
        color: #E2E8F0;
    }
    
    [data-testid="stSidebar"] {
        background: rgba(8, 14, 27, 0.4) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        flex-direction: column;
    }
    
    /* Inject Expenso Brand above the Navigation Links natively */
    [data-testid="stSidebarNav"] {
        padding-top: 24px !important;
    }
    
    [data-testid="stSidebarNav"]::before {
        content: "Expenso";
        display: block;
        
        padding: -20px 20px 24px 32px;
        font-size: 2.5rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    
    }
    
    /* Pin the Logout button to the absolute bottom */
    .st-key-logout_btn {
        position: absolute !important;
        bottom: 32px !important;
        left: 24px !important;
        right: 24px !important;
        width: auto !important;
    }
    
    /* Transparent block elements (fallback for standard containers) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        background: rgba(17, 24, 39, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(20, 28, 43, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Neon Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00D2FF 0%, #3A7BD5 100%);
        color: #050814;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 210, 255, 0.5);
        color: #000;
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
        backdrop-filter: blur(4px);
    }

    /* Headings gradient */
    h1 { 
        background: -webkit-linear-gradient(45deg, #00D2FF, #3A7BD5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important; 
        letter-spacing: -1px;
    }
    h2 { color: #F1F5F9 !important; font-weight: 700 !important; }
    h3 { color: #94A3B8 !important; font-weight: 600 !important; }
    
    /* Dividers */
    hr { border-color: rgba(255,255,255,0.05) !important; }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 30px;
        background: rgba(0,0,0,0.2);
    }

    .stProgress > div > div > div { border-radius: 9999px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state initialization ──────────────────────────
# ── Session state initialization ──────────────────────────
defaults = {
    "authenticated": False,
    "current_role": "",
    "employee_id": "",
    "employee_name": "",
    "selected_claim_id": "",
    "last_submitted_claim_id": "",
    "submission_state": "idle",  # idle | processing | done
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Dynamic Role Navigation ───────────────────────────────
if not st.session_state.authenticated:
    # Lock the router down to just the login page. 
    # position="hidden" ensures Streamlit doesn't render a sidebar menu for it.
    pg = st.navigation([st.Page("views/0_login.py", title="Gateway", icon="🔒")], position="hidden")
else:
    # ── Sidebar Config ───────────────────────────────────────
    # Brand is rendered via CSS ::before on stSidebarNav automatically

    if st.session_state.current_role == "Employee":
        pg = st.navigation({
            "Employee Actions": [
                st.Page("views/1_employee_portal.py", title="Submit Claim", icon="➕"),
                st.Page("views/4_budget_tracker.py", title="Budget Tracker", icon="📊")
            ]
        })
    else:
        pg = st.navigation({
            "Auditor Actions": [
                st.Page("views/2_finance_dashboard.py", title="Finance Dashboard", icon="📈"),
                st.Page("views/3_claim_detail.py", title="Claim Details", icon="🔍")
            ]
        })

    with st.sidebar:
        # Profile icon placed above the logout button
        # Render profile widget; no fallback label under the button
        try:
            profile_widget.render_profile_widget(key_suffix="sidebar")
        except Exception:
            pass

        if st.button("Log Out", use_container_width=True, key="logout_btn"):
            st.session_state.clear()
            st.rerun()

# If a component requested navigation to a page, run that page directly
nav_target = st.session_state.pop("navigate_to", None)
if nav_target:
    import runpy
    # run the target page script directly so it appears as a full page
    runpy.run_path(f"frontend/{nav_target}", run_name="__main__")
else:
    # Run the selected page
    pg.run()

