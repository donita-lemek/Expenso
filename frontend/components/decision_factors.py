"""
frontend/components/decision_factors.py
Renders the XAI decision factors table (Layer 2).
"""
import streamlit as st
import html as _html
from frontend.components.status_badge import weight_pill, RESULT_ICONS


def render_decision_factors(factors: list):
    """Render styled decision factor table with row coloring."""
    if not factors:
        st.info("No decision factors recorded.")
        return

    st.subheader("⚖️ Decision Breakdown")
    st.caption("How the AI weighed each compliance factor")

    failed_high = [f for f in factors if f.get("result") == "FAIL" and f.get("weight") == "HIGH"]
    failed_med = [f for f in factors if f.get("result") == "FAIL" and f.get("weight") == "MEDIUM"]
    warnings = [f for f in factors if f.get("result") == "WARNING"]

    for f in factors:
        result = f.get("result", "PASS")
        weight = f.get("weight", "LOW")
        icon = RESULT_ICONS.get(result, "")

        # Row background
        if result == "FAIL" and weight == "HIGH":
            bg = "rgba(239,68,68,0.12)"
            border = "#EF4444"
        elif result == "FAIL" and weight == "MEDIUM":
            bg = "rgba(245,158,11,0.12)"
            border = "#F59E0B"
        elif result == "WARNING":
            bg = "rgba(245,158,11,0.08)"
            border = "#F59E0B"
        else:
            bg = "rgba(16,185,129,0.06)"
            border = "#10B981"

        factor_esc = _html.escape(f.get("factor", ""))
        detail_esc = _html.escape(f.get("detail", ""))
        st.markdown(
            f"""
            <div style="background:{bg};border-left:3px solid {border};
                        padding:10px 14px;border-radius:6px;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <span style="font-size:1.1rem;">{icon}</span>
                <span style="font-weight:700;color:#F1F5F9;flex:1;">{factor_esc}</span>
                <span>{weight_pill(weight)}</span>
              </div>
              <div style="color:#94A3B8;font-size:0.85rem;margin-top:4px;padding-left:28px;">
                {detail_esc}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Summary line
    total = len(factors)
    fail_count = len(failed_high) + len(failed_med)
    warn_count = len(warnings)

    summary_parts = []
    if fail_count:
        summary_parts.append(f"**{fail_count} factor(s) failed**")
    if warn_count:
        summary_parts.append(f"**{warn_count} warning(s)**")
    if failed_high:
        summary_parts.append(f"**{len(failed_high)} HIGH-weight failure(s)**")

    if summary_parts:
        st.error(f"📊 Out of {total} factors: " + " · ".join(summary_parts))
    else:
        st.success(f"✅ All {total} factors passed.")
