"""
frontend/views/3_claim_detail.py
Full XAI audit report — Premium layout with Hero metrics and 3-column dense evidence grid.
Finance Auditor view only.
"""
import streamlit as st
import html as _html
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.components import api_client as api
from frontend.components.status_badge import status_pill, forgery_pill, risk_color
from frontend.components.xai_panel import render_xai_panel1, render_xai_panel2, render_xai_panel3

st.title("Claim Audit Report")

# ──────────────────────────────────────────────────────────
# ✅ SAFE STRING HELPER (FIX FOR YOUR ERROR)
# ──────────────────────────────────────────────────────────
def safe_str(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return ""
    return str(value)

# ── Claim selector ────────────────────────────────────────
col_back, col_input = st.columns([1, 3])

with col_back:
    if st.button("← Back to Dashboard"):
        st.switch_page("views/2_finance_dashboard.py")

with col_input:
    claim_id_input = st.text_input(
        "Claim ID",
        value=st.session_state.get("selected_claim_id", ""),
        label_visibility="collapsed",
        placeholder="Enter Claim ID here (e.g. CLM-001) or select from dashboard...",
    )
    if claim_id_input:
        st.session_state.selected_claim_id = claim_id_input

claim_id = st.session_state.get("selected_claim_id", "")
if not claim_id:
    st.info("Enter a Claim ID above or click Review from the Finance Dashboard.")
    st.stop()

# ── Fetch claim ────────────────────────────────────────────
claim = api.get_claim(claim_id)
if not claim:
    st.error(f"Claim {claim_id} not found.")
    st.stop()

# ── 🌟 HERO SECTION ────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

risk_score = int(claim.get("risk_score", 0))
rc = risk_color(risk_score)
confidence = int(claim.get("ai_confidence", 0.0) * 100)
status = claim.get("status", "Pending")
pill = status_pill(status)

hero_html = f"""
<div style="background: rgba(15, 23, 42, 0.4); backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.08); border-radius: 24px; padding: 32px 40px;
            margin-bottom: 32px; display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);">
    <div>
        <div style="color: #94A3B8; font-size: 0.9rem; text-transform: uppercase; font-weight: 600;">Claim Identity</div>
        <div style="display: flex; align-items: center; gap: 16px;">
            <div style="font-size: 2.2rem; font-weight: 800; color: #F8FAFC;">{safe_str(claim_id)}</div>
            {pill}
        </div>
        <div style="color: #CBD5E1; font-size: 1.1rem; margin-top: 8px;">
            {_html.escape(safe_str(claim.get('employee_name', 'Unknown User')))}
        </div>
    </div>

</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

# ── 3-COLUMN LAYOUT ───────────────────────────────────────
c1, c2, c3 = st.columns([1.1, 1.1, 1.3], gap="large")

# ── COLUMN 1: RECEIPT ─────────────────────────────────────
with c1:
    render_xai_panel1(claim)
    

# ── COLUMN 2: OCR DATA ────────────────────────────────────
with c2:
    st.subheader("📄 Extracted Data")

    ocr_rows = [
        ("Merchant", claim.get("merchant") or "—"),
        ("Date", claim.get("transaction_date") or "—"),
        ("Time", claim.get("transaction_time") or "—"),
        ("Amount", f"{float(claim.get('claimed_amount', 0)):.2f} {safe_str(claim.get('original_currency', ''))}"),
        ("Quality", claim.get("receipt_quality") or "Unknown"),
    ]

    table_html = '<table style="width:100%;border-collapse:collapse;font-size:0.95rem;">'

    for label, value in ocr_rows:
        lbl = _html.escape(safe_str(label))
        val = _html.escape(safe_str(value))  # 🔥 FIX

        table_html += (
            f'<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<td style="padding:12px 4px;color:#94A3B8;width:40%;">{lbl}</td>'
            f'<td style="padding:12px 4px;color:#F8FAFC;font-weight:600;">{val}</td>'
            f"</tr>"
        )

    table_html += "</table>"
    st.markdown(table_html, unsafe_allow_html=True)
    
    render_xai_panel2(claim)
 

# ── COLUMN 3: XAI + OVERRIDE ──────────────────────────────
with c3:
    st.subheader("🖼️ Receipt Image")

    gcs_url = safe_str(claim.get("receipt_gcs_url", ""))
    filename = safe_str(claim.get("receipt_filename", "receipt"))
    created_at = safe_str(claim.get("created_at", ""))[:19].replace("T", " ")

    if gcs_url.startswith("data:image") or gcs_url.startswith("http"):
        st.image(gcs_url, caption=f"{filename} · Uploaded {created_at}", use_container_width=True)
    else:
        st.info("📄 Receipt image not available in local dev mode.")
    st.subheader("🛡️ Integrity Signals")

    forgery_risk = safe_str(claim.get("forgery_risk") or "Low")
    st.markdown(forgery_pill(forgery_risk), unsafe_allow_html=True)

    if bool(claim.get("is_screenshot")):
        st.error("⚠️ This receipt appears to be a screenshot.")

    if claim.get("duplicate_of"):
        st.warning("⚠️ Duplicate detected")
    else:
        st.success("✅ Unique Submission")
        
    render_xai_panel3(claim)
   
    st.subheader("🔑 Auditor Bypass")

    if claim.get("auditor_override"):
        st.success("Manual override applied")
    else:
        reason = st.text_area("Reason")
        auditor = st.text_input("Auditor ID")

        if st.button("Approve"):
            api.override_claim(claim_id, "Approved", auditor, reason, reason)
            st.rerun()

        if st.button("Reject"):
            api.override_claim(claim_id, "Rejected", auditor, reason, reason)
            st.rerun()
    