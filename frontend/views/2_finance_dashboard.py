"""
frontend/pages/2_finance_dashboard.py
Finance Auditor dashboard — KPIs, claims table, analytics.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.components import api_client as api
from frontend.components.status_badge import status_pill, forgery_pill
# profile widget removed from page header; profile is in sidebar


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background-color: #070B14; color: #E2E8F0; }
[data-testid="stSidebar"] { background-color: #0D1220 !important; border-right: 1px solid #1E293B; }
[data-testid="metric-container"] { background: #111827; border: 1px solid #1E293B; border-radius: 12px; padding: 16px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.4); }
h1,h2,h3 { color: #F1F5F9 !important; }
.stButton > button { background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; border-radius: 8px; font-weight: 400;font-size: 0.5rem; width: 100%; padding: 8px; }
.stDataFrame { border: 1px solid #1E293B; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title(" Finance Auditor Dashboard")

# ── Load all claims ───────────────────────────────────────
all_claims = api.list_claims()

if not all_claims:
    st.info("No claims in the system yet. Seed the database or submit a claim.")
    st.stop()

df = pd.DataFrame(all_claims)

# Parse amounts
for col in ["claimed_amount", "converted_amount_usd", "risk_score", "ai_confidence", "similarity_score"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

now = datetime.utcnow()
month_start = datetime(now.year, now.month, 1)

this_month = df[df["created_at"] >= month_start] if "created_at" in df.columns else df

# ── KPI Row ───────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

total_this_month = len(this_month)
pending_count = len(df[df["status"] == "Pending"])
flagged_amount = df[df["status"] == "Flagged"]["converted_amount_usd"].sum()
approved_count = len(df[df["status"] == "Approved"])
total_count = len(df)
compliance_rate = round(approved_count / total_count * 100, 1) if total_count > 0 else 0.0

k1.metric("📄 Claims This Month", total_this_month, delta=f"{total_this_month} total")
k2.metric(
    "⏳ Pending Review",
    pending_count,
    delta="Backlog" if pending_count > 5 else None,
    delta_color="inverse",
)
k3.metric("🚩 Flagged Amount", f"${flagged_amount:,.2f}")
k4.metric("✅ Compliance Rate", f"{compliance_rate}%")

st.divider()

# ── Filters ───────────────────────────────────────────────
st.subheader("📋 All Claims — Sorted by Risk Level")

f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 2, 1])

with f1:
    status_filter = st.multiselect(
        "Status", ["Pending", "Approved", "Flagged", "Rejected"], default=[]
    )
with f2:
    category_filter = st.multiselect(
        "Category",
        df["category"].dropna().unique().tolist() if "category" in df.columns else [],
        default=[],
    )
with f3:
    date_from = st.date_input("From", value=now.date() - timedelta(days=30))
with f4:
    search_query = st.text_input("🔍 Search name")
with f5:
    export_btn = st.button("Export CSV")

# Apply filters
filtered = df.copy()
if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
if category_filter:
    filtered = filtered[filtered["category"].isin(category_filter)]
if search_query:
    mask = (
        filtered["employee_name"].str.contains(search_query, case=False, na=False)
        | filtered.get("merchant", pd.Series(dtype=str)).str.contains(search_query, case=False, na=False)
    )
    filtered = filtered[mask]

# Sort: Rejected > Flagged > Pending > Approved, then risk_score desc
status_order = {"Rejected": 0, "Flagged": 1, "Pending": 2, "Approved": 3}
filtered["_sort_status"] = filtered["status"].map(status_order).fillna(4)
filtered = filtered.sort_values(["_sort_status", "risk_score"], ascending=[True, False])

if export_btn:
    csv = filtered.to_csv(index=False)
    st.download_button("Download CSV", csv, "claims_export.csv", "text/csv")

# Display table
display_cols = [
    "claim_id", "employee_name", "merchant", "transaction_date",
    "converted_amount_usd", "original_currency", "category",
    "risk_score", "forgery_risk", "duplicate_of", "status",
]
display_cols = [c for c in display_cols if c in filtered.columns]
display_df = filtered[display_cols].copy()

display_df.columns = [
    c.replace("_", " ").title() for c in display_df.columns
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Risk Score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=100, format="%d"
        ),
        "Converted Amount Usd": st.column_config.NumberColumn(
            "Amount (USD)", format="$%.2f"
        ),
    },
)

# ── Quick actions ─────────────────────────────────────────
st.subheader("🔧 Quick Actions")
qa1, qa2 = st.columns(2)

with qa1:
    review_id = st.text_input("Claim ID to Review")
    if st.button("🔍 Review Claim", use_container_width=True) and review_id:
        st.session_state.selected_claim_id = review_id
        st.switch_page("views/3_claim_detail.py")

with qa2:
    override_id = st.text_input("Claim ID for Override")
    override_col1, override_col2 = st.columns(2)
    with override_col1:
        if st.button("✅ Quick Approve", use_container_width=True) and override_id:
            result = api.override_claim(override_id, "Approved", "SYSTEM", "Quick approve", "Quick approve via dashboard")
            if result:
                st.success(f"✅ {override_id} approved.")
                st.rerun()
    with override_col2:
        if st.button("❌ Quick Reject", use_container_width=True) and override_id:
            result = api.override_claim(override_id, "Rejected", "SYSTEM", "Quick reject", "Quick reject via dashboard")
            if result:
                st.error(f"❌ {override_id} rejected.")
                st.rerun()

st.divider()

# ── Analytics tabs ────────────────────────────────────────
st.subheader("📈 Analytics")
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Spend by Category",
    "📅 Compliance Trend",
    "🥧 Risk Distribution",
    "🔍 Forgery Signals"
])

with tab1:
    if "category" in df.columns:
        spend = df.groupby("category")["converted_amount_usd"].sum().reset_index()
        spend.columns = ["Category", "Total (USD)"]
        fig = px.bar(
            spend, x="Category", y="Total (USD)",
            color="Category",
            color_discrete_sequence=px.colors.qualitative.Set3,
            title="Total Spend by Category",
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="#111827", plot_bgcolor="#111827",
            font_color="#E2E8F0", showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    if "created_at" in df.columns and "status" in df.columns:
        trend_df = df.dropna(subset=["created_at"]).copy()
        trend_df["date"] = trend_df["created_at"].dt.date
        trend = trend_df.groupby(["date", "status"]).size().reset_index(name="count")
        if not trend.empty:
            fig2 = px.line(
                trend, x="date", y="count", color="status",
                color_discrete_map={
                    "Approved": "#10B981",
                    "Flagged": "#F59E0B",
                    "Rejected": "#EF4444",
                    "Pending": "#6B7280",
                },
                title="Compliance Trend (Last 30 Days)",
                template="plotly_dark",
                markers=True,
            )
            fig2.update_layout(
                paper_bgcolor="#111827", plot_bgcolor="#111827",
                font_color="#E2E8F0",
            )
            st.plotly_chart(fig2, use_container_width=True)

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        if "forgery_risk" in df.columns:
            fr = df["forgery_risk"].fillna("Unknown").value_counts().reset_index()
            fr.columns = ["Risk", "Count"]
            fig3 = px.pie(
                fr, names="Risk", values="Count",
                color="Risk",
                color_discrete_map={"Low": "#10B981", "Medium": "#F59E0B", "High": "#EF4444", "Unknown": "#6B7280"},
                title="Forgery Risk Distribution",
                template="plotly_dark",
                hole=0.4,
            )
            fig3.update_layout(paper_bgcolor="#111827", font_color="#E2E8F0")
            st.plotly_chart(fig3, use_container_width=True)
    with c2:
        st_counts = df["status"].value_counts().reset_index()
        st_counts.columns = ["Status", "Count"]
        fig4 = px.pie(
            st_counts, names="Status", values="Count",
            color="Status",
            color_discrete_map={"Approved": "#10B981", "Flagged": "#F59E0B", "Rejected": "#EF4444", "Pending": "#6B7280"},
            title="Status Distribution",
            template="plotly_dark",
            hole=0.4,
        )
        fig4.update_layout(paper_bgcolor="#111827", font_color="#E2E8F0")
        st.plotly_chart(fig4, use_container_width=True)

with tab4:
    if "forgery_risk" in df.columns:
        forgery_claims = df[df["forgery_risk"].isin(["Medium", "High"])].copy()
        if forgery_claims.empty:
            st.success("✅ No Medium or High forgery risk claims.")
        else:
            forgery_order = {"High": 0, "Medium": 1}
            forgery_claims["_fr_order"] = forgery_claims["forgery_risk"].map(forgery_order)
            forgery_claims = forgery_claims.sort_values("_fr_order")

            for _, row in forgery_claims.iterrows():
                risk = row.get("forgery_risk", "")
                flags = row.get("forgery_flags", [])
                color = "#EF4444" if risk == "High" else "#F59E0B"
                flags_html = "".join(
                    f'<span style="background:{color}22;color:{color};padding:2px 8px;'
                    f'border-radius:4px;font-size:0.75rem;margin:2px;">{f}</span>'
                    for f in (flags if isinstance(flags, list) else [])
                )
                st.markdown(
                    f"""
                    <div style="background:#111827;border:1px solid {color}44;border-radius:8px;
                                padding:12px 16px;margin-bottom:8px;">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <strong style="color:#F1F5F9;">{row.get('claim_id','')}</strong>
                        <span style="color:#94A3B8;font-size:0.85rem;">{row.get('employee_name','')}</span>
                        <span style="color:{color};font-weight:700;">{risk} Risk</span>
                      </div>
                      <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;">{flags_html}</div>
                      <div style="color:#64748B;font-size:0.8rem;margin-top:6px;">
                        {row.get('forgery_reasoning','')[:150] if row.get('forgery_reasoning') else ''}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
