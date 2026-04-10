"""
frontend/views/profile.py
Full profile page showing employee details.
"""
import streamlit as st
from datetime import datetime

st.title("👤 My Profile")

emp_name = st.session_state.get("employee_name", "Unknown User")
emp_id = st.session_state.get("employee_id", "EMP-???")
emp_email = st.session_state.get("employee_email", "N/A")
role = st.session_state.get("role_title", "N/A")
join_date = st.session_state.get("joining_date", "N/A")
exp = st.session_state.get("experience", "N/A")

col1, col2 = st.columns([1, 2])
with col1:
    st.image("https://placehold.co/128x128/222831/ffffff?text=👤", width=128)

with col2:
    st.markdown(f"### {emp_name}")
    st.markdown(f"- **Employee ID:** {emp_id}")
    st.markdown(f"- **Email:** {emp_email}")
    st.markdown(f"- **Role:** {role}")
    st.markdown(f"- **Joined:** {join_date}")
    st.markdown(f"- **Experience:** {exp}")

# Optionally compute years of service if joining_date is parseable
try:
    if isinstance(join_date, str):
        jd = datetime.strptime(join_date, "%d %b %Y")
        years = (datetime.utcnow() - jd).days / 365.25
        st.markdown(f"- **Years at company:** {years:.1f} years")
except Exception:
    pass
