"""
frontend/components/profile_widget.py
Reusable Top-Right Profile Widget returning a styled popover with session parameters.
"""
import streamlit as st

def render_profile_widget(key_suffix: str = None):
    """
    Renders a dynamic st.popover anchored to the right-most column spanning the active session state logic.
    Provides metadata about the current user.
    """
    emp_name = st.session_state.get("employee_name", "Unknown User")
    emp_id = st.session_state.get("employee_id", "EMP-???")
    emp_email = st.session_state.get("employee_email", "N/A")
    role = st.session_state.get("role_title", "N/A")
    join_date = st.session_state.get("joining_date", "N/A")
    exp = st.session_state.get("experience", "N/A")
    
    # Render a small button; clicking navigates to the full profile page
    btn_key = f"profile_button_{key_suffix}" if key_suffix else "profile_button"
    if st.button(f"👤 {emp_name}", key=btn_key):
        st.session_state["navigate_to"] = "views/profile.py"
        st.experimental_rerun()
