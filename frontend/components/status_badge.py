"""
frontend/components/status_badge.py
Renders colored status pills and risk score indicators.
"""
import streamlit as st


STATUS_COLORS = {
    "Approved": ("#10B981", "#052e16"),
    "Flagged": ("#F59E0B", "#451a03"),
    "Rejected": ("#EF4444", "#450a0a"),
    "Pending": ("#6B7280", "#111827"),
}

FORGERY_COLORS = {
    "Low": ("#10B981", "#052e16"),
    "Medium": ("#F59E0B", "#451a03"),
    "High": ("#EF4444", "#450a0a"),
}

WEIGHT_COLORS = {
    "HIGH": "#EF4444",
    "MEDIUM": "#F59E0B",
    "LOW": "#6B7280",
}

RESULT_ICONS = {
    "PASS": "✅",
    "FAIL": "❌",
    "WARNING": "⚠️",
}


def status_pill(status: str) -> str:
    """Return HTML for a colored status pill."""
    fg, bg = STATUS_COLORS.get(status, ("#9CA3AF", "#1F2937"))
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {fg};'
        f'padding:2px 10px;border-radius:9999px;font-size:0.8rem;font-weight:600;">'
        f"{status}</span>"
    )


def forgery_pill(risk: str) -> str:
    """Return HTML for a colored forgery risk pill."""
    fg, bg = FORGERY_COLORS.get(risk, ("#9CA3AF", "#1F2937"))
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {fg};'
        f'padding:2px 10px;border-radius:9999px;font-size:0.8rem;font-weight:600;">'
        f"🔍 {risk} Risk</span>"
    )


def weight_pill(weight: str) -> str:
    color = WEIGHT_COLORS.get(weight, "#9CA3AF")
    return (
        f'<span style="background:{color}22;color:{color};border:1px solid {color}44;'
        f'padding:1px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;">'
        f"{weight}</span>"
    )


def risk_color(score: int) -> str:
    """Return a hex color for a 0-100 risk score."""
    if score <= 30:
        return "#10B981"
    elif score <= 60:
        return "#F59E0B"
    else:
        return "#EF4444"


def render_status_banner(status: str, explanation: str):
    """Large colored banner for claim verdict."""
    fg, bg = STATUS_COLORS.get(status, ("#9CA3AF", "#1F2937"))
    icons = {"Approved": "✅", "Flagged": "⚠️", "Rejected": "❌", "Pending": "⏳"}
    icon = icons.get(status, "")
    st.markdown(
        f"""
        <div style="background:{bg};border:2px solid {fg};border-radius:12px;
                    padding:20px 24px;margin-bottom:16px;">
          <div style="color:{fg};font-size:1.6rem;font-weight:800;letter-spacing:0.05em;">
            {icon} {status.upper()}
          </div>
          <div style="color:#E2E8F0;font-size:1rem;margin-top:8px;line-height:1.5;">
            {explanation}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
