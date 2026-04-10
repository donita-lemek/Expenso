"""
frontend/components/counterfactuals.py
Renders XAI counterfactuals (Layer 5).
"""
import streamlit as st
import html as _html


def render_counterfactuals(counterfactuals: list, status: str):
    """Render counterfactual explanations — only for Flagged/Rejected."""
    if status == "Approved":
        return
    if not counterfactuals:
        return

    st.subheader("💡 What Would Change This Decision?")

    for cf in counterfactuals:
        cf_esc = _html.escape(cf)
        st.markdown(
            f"""
            <div style="display:flex;align-items:flex-start;gap:10px;
                        padding:10px 14px;background:#1E293B;border-radius:8px;
                        margin-bottom:8px;border-left:3px solid #3B82F6;">
              <span style="color:#60A5FA;font-size:1rem;margin-top:2px;">→</span>
              <span style="color:#CBD5E1;font-size:0.9rem;">{cf_esc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if status == "Rejected":
        st.error(
            "❌ **Cannot auto-approve.** "
            "Request an auditor override or resubmit a revised claim."
        )
    elif status == "Flagged":
        st.warning(
            "⚠️ **Claim routed to Finance review.** "
            "No action needed from you at this time."
        )
