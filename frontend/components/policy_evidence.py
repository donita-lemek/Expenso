"""
frontend/components/policy_evidence.py
Renders the XAI policy evidence panel (Layer 3).
"""
import streamlit as st
import html as _html


def render_policy_evidence(evidence: dict):
    """Render the matched policy section evidence."""
    if not evidence:
        st.info("No policy evidence recorded.")
        return

    st.subheader("📋 Policy Evidence")

    # Section badge
    section = evidence.get("section", "N/A")
    title = evidence.get("section_title", "")
    # Escape dynamic content
    section_esc = _html.escape(str(section))
    title_esc = _html.escape(title)
    st.markdown(
        f"""
        <div style="display:inline-block;background:#1E3A5F;color:#60A5FA;
                    border:1px solid #3B82F6;padding:4px 14px;border-radius:6px;
                    font-weight:700;font-size:0.9rem;margin-bottom:12px;">
          📌 Section {section_esc} — {title_esc}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Full policy text
    full_text = evidence.get("full_text", "")
    if full_text:
        st.code(full_text, language="text")

    # Applied rule highlighted
    applied = evidence.get("applied_rule", "")
    if applied:
        st.warning(f"**Applied Rule:** {applied}")

    # Matching reason
    reason = evidence.get("matching_reason", "")
    if reason:
        st.caption(f"🔎 Why this section applies: {reason}")
