"""
frontend/components/xai_panel.py
Fixed: prevents raw HTML rendering from any child component.
"""
import streamlit as st
import html as _html
from frontend.components.status_badge import render_status_banner, risk_color
from frontend.components.decision_factors import render_decision_factors
from frontend.components.policy_evidence import render_policy_evidence
from frontend.components.counterfactuals import render_counterfactuals


# ✅ UNIVERSAL SAFE RENDER
def render_safe(component_fn, *args, **kwargs):
    """
    Handles both:
    - components that return HTML
    - components that directly render via Streamlit
    """
    result = component_fn(*args, **kwargs)

    # If component RETURNS HTML → render properly
    if isinstance(result, str) and "<" in result:
        st.markdown(result, unsafe_allow_html=True)


def render_xai_panel1(claim: dict):
    status = claim.get("status", "Pending")
    explanation = claim.get("explanation", "Audit in progress...")

    # ── Layer 1: Verdict Banner ────────────────────────────
    render_safe(render_status_banner, status, explanation)

    # ── Layer 4: Confidence ────────────────────────────────
    confidence = claim.get("ai_confidence", 0.0)
    conf_pct = int(confidence * 100)

    col_conf, col_risk = st.columns(2)

    with col_conf:
        st.markdown(f"**🎯 AI Confidence: {conf_pct}%**")
        color = "#10B981" if conf_pct >= 75 else "#F59E0B"
        st.markdown(
            f'<div style="background:#1E293B;border-radius:999px;height:8px;">'
            f'<div style="background:{color};width:{conf_pct}%;height:100%;"></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_risk:
        risk_score = claim.get("risk_score", 0)
        rcolor = risk_color(risk_score)
        st.markdown(f"**⚠️ Risk Score: {risk_score}/100**")
        st.markdown(
            f'<div style="background:#1E293B;border-radius:999px;height:8px;">'
            f'<div style="background:{rcolor};width:{risk_score}%;height:100%;"></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if confidence < 0.75:
        uncertainty = claim.get("uncertainty_notes", "")
        if uncertainty:
            st.warning(f"⚠️ Low confidence: {uncertainty}")

    with st.expander("📊 Confidence Breakdown"):
        cb = claim.get("confidence_breakdown", {})
        if cb:
            c1, c2, c3 = st.columns(3)
            c1.metric("OCR", f"{int(cb.get('ocr_confidence',0)*100)}%")
            c2.metric("Policy", f"{int(cb.get('policy_match_confidence',0)*100)}%")
            c3.metric("Overall", f"{int(cb.get('overall_confidence',0)*100)}%")

    st.divider()
    
    render_safe(render_policy_evidence, claim.get("policy_evidence"))
    st.divider()

    # ── Layer 6: Audit Trail ───────────────────────────────
    with st.expander("🔍 Full Audit Trail"):
        trail = claim.get("audit_trail", [])

        if trail:
            for event in trail:
                ts = _html.escape(str(event.get("timestamp", ""))[:19].replace("T", " "))
                evt = _html.escape(str(event.get("event", "")))
                detail = _html.escape(str(event.get("detail", "")))

                st.markdown(
                    f"""
                    <div style="display:grid;grid-template-columns:160px 180px 1fr;
                                gap:8px;padding:6px 0;border-bottom:1px solid #1E293B;
                                font-size:0.82rem;">
                        <span style="color:#64748B;">{ts}</span>
                        <span style="color:#60A5FA;font-weight:600;">{evt}</span>
                        <span style="color:#CBD5E1;">{detail}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No audit trail yet.")

        with st.expander("Show Raw Claude Prompt"):
            st.code(claim.get("claude_prompt_sent", ""), language="text")

        with st.expander("Show Raw Claude Response"):
            st.code(claim.get("claude_raw_response", ""), language="json")




def render_xai_panel2(claim: dict):
    # ── Layer 2–5: SAFE WRAPPED ────────────────────────────
    render_safe(render_decision_factors, claim.get("decision_factors", []))
    st.divider()

def render_xai_panel3(claim: dict):  
    render_safe(render_counterfactuals, claim.get("counterfactuals", []), st.status)

    if claim.get("counterfactuals"):
        st.divider()