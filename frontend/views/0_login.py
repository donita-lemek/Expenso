"""
frontend/views/0_login.py
Gateway screen for authentication.
"""
import streamlit as st
import time
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.components import api_client as api

# Hide the sidebar completely on the login page via CSS
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1.2, 1])

with col2:
    st.markdown(
        """
        <div style="text-align:center; margin-bottom: 24px;">
            <div style="font-size:3.5rem; font-weight:800; background: -webkit-linear-gradient(45deg, #00D2FF, #3A7BD5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing:-1px;">Expenso</div>
            <div style="color:#94A3B8; font-size:1.1rem; font-weight:500;">Secure Portal Gateway</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Glassmorphism Login Container
    with st.container():
        st.markdown(
            """
            <style>
            .stTabs [data-baseweb="tab-list"] { justify-content: center; background: transparent; border: none; }
            .stTabs [data-baseweb="tab"] { font-size: 1.1rem; padding: 12px 24px; color: #94A3B8 !important; border-radius: 8px; margin: 0 4px; }
            .stTabs [aria-selected="true"] { background: rgba(59, 130, 246, 0.2) !important; color: #38BDF8 !important; border: 1px solid rgba(56, 189, 248, 0.3) !important; }
            </style>
            """, unsafe_allow_html=True
        )
        
        tab1, tab2 = st.tabs(["👨‍💼 Employee Login", "🔐 Finance Auditor"])
        
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            emp_id = st.text_input("Employee ID", placeholder="e.g. EMP-001")
            emp_pass = st.text_input("Password", type="password", placeholder="password123")
            
            if st.button("Log In as Employee", use_container_width=True):
                if not emp_id or not emp_pass:
                    st.error("⚠️ Please enter both ID and Password.")
                else:
                    # Fetch from backend to simulate auth
                    employees = api.list_employees()
                    user = next((e for e in employees if e.get("employee_id") == emp_id and e.get("password") == emp_pass), None)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_role = "Employee"
                        st.session_state.employee_id = user["employee_id"]
                        st.session_state.employee_name = user["name"]
                        st.session_state.employee_email = user.get("email", "")
                        st.session_state.role_title = user.get("role_title", "Employee")
                        st.session_state.joining_date = user.get("joining_date", "N/A")
                        st.session_state.experience = user.get("experience", "N/A")
                        st.success(f"✅ Welcome back, {user['name']}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Employee ID or Password.")
                        
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            aud_id = st.text_input("Finance Auditor ID", placeholder="e.g. AUD-491")
            aud_pass = st.text_input("Auditor Password", type="password", placeholder="admin")
            
            if st.button("Log In as Auditor", use_container_width=True):
                if not aud_id or not aud_pass:
                    st.error("⚠️ Please enter Auditor ID and Password.")
                else:
                    # Mocking auditor auth against seeded values since DB didn't expose /auditors API
                    if aud_id == "AUD-491" and aud_pass == "admin":
                        st.session_state.authenticated = True
                        st.session_state.current_role = "Finance Auditor"
                        st.session_state.employee_id = aud_id
                        st.session_state.employee_name = "System Auditor"
                        st.session_state.employee_email = "audit@acmecorp.com"
                        st.session_state.role_title = "Lead Finance Auditor"
                        st.session_state.joining_date = "10 Feb 2017"
                        st.session_state.experience = "9.1 Years"
                        st.success("✅ Secure Auditor session established.")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid Finance Auditor credentials.")
