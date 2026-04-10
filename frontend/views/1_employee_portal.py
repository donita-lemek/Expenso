"""
frontend/pages/1_employee_portal.py
Employee claim submission portal with live processing stepper.
"""
import streamlit as st
import time
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.components import api_client as api
from frontend.components.status_badge import status_pill, render_status_banner
from frontend.components.counterfactuals import render_counterfactuals
# profile widget removed from page header; profile is in sidebar


# ── CSS (inherits from app.py but re-applied for direct access) ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background-color: #070B14; color: #E2E8F0; }
[data-testid="stSidebar"] { background-color: #0D1220 !important; border-right: 1px solid #1E293B; }
[data-testid="metric-container"] { background: #111827; border: 1px solid #1E293B; border-radius: 12px; padding: 16px !important; }
h1,h2,h3 { color: #F1F5F9 !important; }
.stButton > button { background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; border-radius: 8px; font-weight: 600; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.pulse-dot { display:inline-block; width:8px; height:8px; background:#F59E0B; border-radius:50%; animation:pulse 1.5s infinite; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

CITY_TIERS = {
    "New York": "A", "London": "A", "San Francisco": "A", "Tokyo": "A",
    "Chicago": "B", "Boston": "B", "Austin": "B", "Seattle": "B",
    "Miami": "C", "Denver": "C", "Phoenix": "C", "Atlanta": "C",
}

CATEGORIES = ["Meals", "Transport", "Lodging", "Entertainment", "Other"]
CURRENCIES = ["USD", "GBP", "EUR", "JPY", "INR", "CAD", "AUD", "SGD", "CNY", "Other"]

STEPPER_STEPS = [
    ("✅", "Receipt uploaded"),
    ("🔍", "Extracting receipt data with OCR..."),
    ("🔁", "Checking for duplicate submissions..."),
    ("💱", "Converting currency..."),
    ("🛡️", "Scoring receipt authenticity..."),
    ("📋", "Cross-referencing expense policy..."),
    ("⚖️", "Generating compliance verdict..."),
]

st.title("Submit Expense Claim")

# ── Personal claim summary KPIs ───────────────────────────
emp_id = st.session_state.get("employee_id", "")
if emp_id:
    all_claims = api.list_claims(employee_id=emp_id)
    total = len(all_claims)
    pending = sum(1 for c in all_claims if c.get("status") == "Pending")
    approved = sum(1 for c in all_claims if c.get("status") == "Approved")
    rejected = sum(1 for c in all_claims if c.get("status") == "Rejected")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📄 Total Claims", total)
    pending_label = "⏳ Pending"
    k2.metric(pending_label, pending)
    k3.metric("✅ Approved", approved)
    k4.metric("❌ Rejected", rejected, delta=None)
    st.divider()

# ── Main layout: Form (left) + Dynamic panel (right) ──────
col_form, col_panel = st.columns([1, 1], gap="large")

with col_form:
    st.subheader("Claim Details")

    # Use logged-in session details (not editable here)
    emp_name = st.session_state.get("employee_name", "")
    emp_id_input = st.session_state.get("employee_id", "")
    emp_email = st.session_state.get("employee_email", "")
    st.markdown(f"**Logged in as:** {emp_name} — {emp_id_input}")

    city_options = [f"{c} (Tier {t})" for c, t in CITY_TIERS.items()]
    city_sel = st.selectbox("City", city_options)
    city = city_sel.split(" (")[0]
    city_tier = CITY_TIERS.get(city, "C")

    category = st.selectbox("Expense Category", CATEGORIES)
    expense_date = st.date_input("Expense Date")
    amount = st.number_input("Amount Claimed", min_value=0.01, value=50.0, step=0.01)
    currency = st.selectbox("Currency", CURRENCIES)

    purpose = st.text_area(
        "Business Purpose",
        placeholder="Describe the business reason for this expense (min 20 chars)",
        max_chars=500,
    )
    char_count = len(purpose)
    char_color = "#10B981" if char_count >= 20 else "#EF4444"
    st.markdown(
        f'<div style="font-size:0.78rem;color:{char_color};text-align:right;">'
        f'{char_count}/500 characters {"✓" if char_count >= 20 else "(min 20)"}</div>',
        unsafe_allow_html=True,
    )

    receipt_file = st.file_uploader(
        "📎 Upload Receipt",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Supported: JPG, PNG, PDF up to 10MB",
    )

    # Validation errors
    errors = []
    submit_clicked = st.button("🚀 Submit Claim", use_container_width=True)

    if submit_clicked:
        # Use session values — assume user is authenticated
        if char_count < 20:
            errors.append("Business purpose must be at least 20 characters.")
        if receipt_file is None:
            errors.append("Please upload a receipt image.")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
        else:
            # Ensure session state is set from login
            st.session_state.employee_id = emp_id_input
            st.session_state.employee_name = emp_name
            st.session_state.submission_state = "processing"

            # Submit
            receipt_bytes = receipt_file.read()
            result = api.submit_claim(
                employee_id=emp_id_input,
                employee_name=emp_name,
                employee_email=emp_email,
                city=city,
                city_tier=city_tier,
                category=category,
                claimed_amount=amount,
                original_currency=currency,
                business_purpose=purpose,
                receipt_bytes=receipt_bytes,
                receipt_filename=receipt_file.name,
            )

            if result:
                st.session_state.last_submitted_claim_id = result.get("claim_id", "")
                st.session_state.submission_state = "processing"
                st.rerun()

with col_panel:
    state = st.session_state.get("submission_state", "idle")
    last_claim_id = st.session_state.get("last_submitted_claim_id", "")
    uploaded_file = receipt_file

    # ── State A: Before upload ─────────────────────────────
    if state == "idle" and uploaded_file is None:
        st.markdown(
            """
            <div style="border:2px dashed #1E293B;border-radius:16px;padding:48px 24px;
                        text-align:center;background:#0D1220;margin-top:8px;">
              <div style="font-size:3rem;margin-bottom:16px;">📄</div>
              <div style="color:#64748B;font-size:0.95rem;">
                Upload your receipt to preview it here
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "💡 **Tips for best results:**\n"
            "- Ensure receipt is flat and well-lit\n"
            "- All text should be clearly visible\n"
            "- JPG, PNG, or PDF formats accepted"
        )

    # ── State B: Receipt uploaded ──────────────────────────
    elif state == "idle" and uploaded_file is not None:
        st.success("✅ Receipt ready for submission")
        uploaded_file.seek(0)
        if uploaded_file.name.lower().endswith(".pdf"):
            st.info("📄 PDF receipt uploaded — preview not available for PDFs.")
        else:
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

    # ── State C: Processing ────────────────────────────────
    elif state == "processing" and last_claim_id:
        st.subheader("⏳ Processing Your Claim")
        st.caption(f"Claim ID: `{last_claim_id}`")

        progress_placeholder = st.empty()
        step_placeholder = st.empty()

        for i, (icon, label) in enumerate(STEPPER_STEPS):
            with step_placeholder.container():
                st.markdown(
                    f"""
                    <div style="padding:12px 16px;background:#111827;border-radius:10px;
                                border:1px solid #1E293B;margin-bottom:4px;">
                    """,
                    unsafe_allow_html=True,
                )
                for j, (s_icon, s_label) in enumerate(STEPPER_STEPS):
                    if j < i:
                        color, done_icon = "#10B981", "✅"
                    elif j == i:
                        color, done_icon = "#F59E0B", "⏳"
                    else:
                        color, done_icon = "#475569", "○"
                    st.markdown(
                        f'<div style="color:{color};padding:4px 0;font-size:0.9rem;">'
                        f'{done_icon} {s_label}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            with progress_placeholder:
                st.progress((i + 1) / len(STEPPER_STEPS))

            # Poll for completion on last step
            if i == len(STEPPER_STEPS) - 1:
                # Poll until pipeline finishes
                for _ in range(30):  # up to 60s
                    time.sleep(2)
                    claim_data = api.get_claim(last_claim_id)
                    if claim_data and claim_data.get("status") != "Pending":
                        st.session_state.submission_state = "done"
                        st.rerun()
                        break
                # Timeout
                st.session_state.submission_state = "done"
                st.rerun()
            else:
                time.sleep(1.5)

    # ── State D: Result ────────────────────────────────────
    elif state == "done" and last_claim_id:
        claim_data = api.get_claim(last_claim_id)
        if claim_data:
            status = claim_data.get("status", "Pending")
            explanation = claim_data.get("explanation", "")
            render_status_banner(status, explanation)

            st.markdown(f"**Claim ID:** `{last_claim_id}`")

            # Counterfactuals for employee (simplified)
            cfs = claim_data.get("counterfactuals", [])
            if cfs and status in ("Flagged", "Rejected"):
                st.markdown("**💡 What you can do:**")
                for cf in cfs:
                    st.markdown(f"→ {cf}")

            # Next steps
            if status == "Approved":
                st.success("🎉 Your claim has been approved and will be processed shortly.")
            elif status == "Flagged":
                st.warning("📋 Your claim has been sent for manual Finance review.")
            elif status == "Rejected":
                st.error("❌ Your claim was rejected. See guidance above to resubmit.")

            if st.button("📝 Submit Another Claim", use_container_width=True):
                st.session_state.submission_state = "idle"
                st.session_state.last_submitted_claim_id = ""
                st.rerun()
        else:
            st.warning("Claim still processing... please wait.")

# ── My Claims History ─────────────────────────────────────
st.divider()
st.subheader("📜 My Previous Claims")

emp_id_filter = st.session_state.get("employee_id", "")
if emp_id_filter:
    my_claims = api.list_claims(employee_id=emp_id_filter)
    if my_claims:
        import pandas as pd
        rows = []
        for c in my_claims:
            # show merchant if available; otherwise fall back to receipt filename or processing marker
            merchant = c.get("merchant") or c.get("receipt_filename") or "—"
            # date: prefer transaction_date, else created_at (formatted), else placeholder
            tx_date = c.get("transaction_date")
            if not tx_date:
                created = c.get("created_at", "")
                tx_date = (created[:10] if created else "—")

            rows.append({
                "Claim ID": c.get("claim_id", ""),
                "Merchant": merchant,
                "Date": tx_date,
                "Amount": f"{c.get('claimed_amount',0):.2f} {c.get('original_currency','')}",
                "Category": c.get("category", ""),
                "Status": c.get("status", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No claims found for your Employee ID.")
else:
    st.info("Log in to see your claim history.")
