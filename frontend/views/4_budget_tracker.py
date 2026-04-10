"""
frontend/pages/4_budget_tracker.py
Employee monthly budget tracker + trip planner.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
import sys, os
import calendar

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from frontend.components import api_client as api


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background-color: #070B14; color: #E2E8F0; }
[data-testid="stSidebar"] { background-color: #0D1220 !important; border-right: 1px solid #1E293B; }
[data-testid="metric-container"] { background: #111827; border: 1px solid #1E293B; border-radius: 12px; padding: 16px !important; }
h1,h2,h3 { color: #F1F5F9 !important; }
.stButton > button { background: linear-gradient(135deg, #3B82F6, #2563EB); color: white; border: none; border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("💰 Expense Budget Tracker")
st.caption("Track monthly spending vs. policy limits")

CITY_TIERS = {
    "New York (Tier A)": "A", "London (Tier A)": "A", "San Francisco (Tier A)": "A", "Tokyo (Tier A)": "A",
    "Chicago (Tier B)": "B", "Boston (Tier B)": "B", "Austin (Tier B)": "B", "Seattle (Tier B)": "B",
    "Miami (Tier C)": "C", "Denver (Tier C)": "C", "Phoenix (Tier C)": "C", "Atlanta (Tier C)": "C",
}

CATEGORY_ICONS = {
    "meals": "🍽️",
    "transport": "🚗",
    "lodging": "🏨",
    "entertainment": "🎭",
    "other": "📦",
}

# ── Use logged-in employee (no dropdown) ───────────────────
selected_emp_id = st.session_state.get("employee_id", "")
if not selected_emp_id:
    st.info("Please log in to view your budget.")
    st.stop()

# Fetch budget
budget_data = api.get_employee_budget(selected_emp_id)
if not budget_data:
    st.error("Could not fetch budget data.")
    st.stop()

emp_info = budget_data.get("employee", {})
spend = budget_data.get("current_month_spend", {})
limits = budget_data.get("limits", {})
remaining = budget_data.get("remaining", {})
month_label = budget_data.get("month", datetime.utcnow().strftime("%B %Y"))
days_left = budget_data.get("days_remaining", 0)

st.subheader(f"📊 Budget Overview — {month_label}")
st.caption(f"{days_left} days remaining in {month_label}")

# ── Budget cards ──────────────────────────────────────────
categories = list(limits.keys()) if limits else ["meals", "transport", "lodging", "entertainment"]
cols = st.columns(len(categories))

for i, cat in enumerate(categories):
    with cols[i]:
        icon = CATEGORY_ICONS.get(cat.lower(), "📦")
        limit = float(limits.get(cat, 0) or 0)
        spent = float(spend.get(cat.lower(), 0) or 0)
        rem = float(remaining.get(cat, limit - spent) or 0)
        pct = spent / limit if limit > 0 else 0

        if pct < 0.70:
            bar_color, status_text = "#10B981", "On track"
        elif pct < 0.90:
            bar_color, status_text = "#F59E0B", "Near limit"
        else:
            bar_color, status_text = "#EF4444", "Over/near limit"

        st.markdown(
            f"""
            <div style="background:#111827;border:1px solid #1E293B;border-radius:12px;
                        padding:18px;text-align:center;height:100%;">
              <div style="font-size:1.8rem;">{icon}</div>
              <div style="font-weight:700;color:#F1F5F9;font-size:1rem;margin:6px 0;">
                {cat.title()}
              </div>
              <div style="background:#1E293B;border-radius:999px;height:8px;margin:10px 0;overflow:hidden;">
                <div style="background:{bar_color};width:{min(pct*100,100):.1f}%;height:100%;
                            border-radius:999px;transition:width 0.3s;"></div>
              </div>
              <div style="font-size:0.9rem;color:#94A3B8;">
                <strong style="color:{bar_color};">${spent:.0f}</strong> of
                <strong style="color:#F1F5F9;">${limit:.0f}</strong>
              </div>
              <div style="font-size:0.8rem;color:#64748B;margin-top:4px;">
                ${rem:.0f} remaining · {status_text}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

# ── Trip Planner ──────────────────────────────────────────
st.subheader("✈️ Plan a Future Trip")
st.info("Calculate your maximum reimbursable amount for an upcoming trip")

DAILY_LIMITS = {
    "A": {"meals": 110, "transport": 80, "lodging": 350, "entertainment": 50},
    "B": {"meals": 85, "transport": 60, "lodging": 250, "entertainment": 40},
    "C": {"meals": 60, "transport": 40, "lodging": 175, "entertainment": 30},
}

tp_col1, tp_col2 = st.columns(2)

with tp_col1:
    dest_city = st.selectbox("Destination City", list(CITY_TIERS.keys()))
    trip_tier = CITY_TIERS.get(dest_city, "C")
    num_days = st.number_input("Number of Days", min_value=1, max_value=30, value=3)
    trip_cats = st.multiselect(
        "Categories Needed",
        ["Meals", "Transport", "Lodging", "Entertainment"],
        default=["Meals", "Transport", "Lodging"],
    )
    trip_start = st.date_input("Trip Start Date", value=date.today())
    calc_btn = st.button("🧮 Calculate Budget", use_container_width=True)

with tp_col2:
    if calc_btn and trip_cats:
        daily = DAILY_LIMITS.get(trip_tier, DAILY_LIMITS["C"])
        trip_rows = []
        grand_total = 0.0

        for cat in trip_cats:
            cat_key = cat.lower()
            daily_limit = daily.get(cat_key, 0)
            cat_total = daily_limit * num_days
            already_spent = float(spend.get(cat_key, 0) or 0)
            cat_limit_month = float(limits.get(cat_key, 0) or 0)
            headroom = max(0.0, cat_limit_month - already_spent)
            effective = min(cat_total, headroom)

            trip_rows.append({
                "Category": cat,
                "Daily Limit": f"${daily_limit}",
                "Days": num_days,
                "Trip Total": f"${cat_total:.0f}",
                "Month Headroom": f"${headroom:.0f}",
                "Effective Max": f"${effective:.0f}",
            })
            grand_total += effective

        st.dataframe(pd.DataFrame(trip_rows), hide_index=True, use_container_width=True)

        st.markdown(
            f"""
            <div style="background:#1E3A5F;border:1px solid #3B82F6;border-radius:10px;
                        padding:16px;text-align:center;margin-top:12px;">
              <div style="color:#60A5FA;font-size:0.85rem;font-weight:600;">TOTAL TRIP BUDGET</div>
              <div style="color:#F1F5F9;font-size:2rem;font-weight:800;">${grand_total:.2f}</div>
              <div style="color:#64748B;font-size:0.8rem;">Tier {trip_tier} · {num_days} days</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if any(float(spend.get(c.lower(), 0) or 0) > 0 for c in trip_cats):
            st.warning(
                "⚠️ You have existing spend this month. "
                "Effective maximum reflects remaining monthly headroom."
            )

st.divider()

# ── Spend History Chart ────────────────────────────────────
st.subheader("📅 Monthly Spend History")

claims = api.list_claims(employee_id=selected_emp_id)
if claims:
    df = pd.DataFrame(claims)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["date"] = df["created_at"].dt.date
    df["converted_amount_usd"] = pd.to_numeric(df["converted_amount_usd"], errors="coerce").fillna(0)

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1).date()
    df_month = df[df["date"] >= month_start].copy()

    if df_month.empty:
        st.info("No claim spend this month to chart.")
    else:
        categories_in_data = df_month["category"].dropna().unique().tolist()
        fig = go.Figure()

        cat_colors = {
            "Meals": "#60A5FA", "Transport": "#34D399",
            "Lodging": "#A78BFA", "Entertainment": "#F87171", "Other": "#94A3B8"
        }

        for cat in categories_in_data:
            cat_df = df_month[df_month["category"] == cat].sort_values("date")
            cat_df["cumulative"] = cat_df["converted_amount_usd"].cumsum()
            color = cat_colors.get(cat, "#94A3B8")
            fig.add_trace(go.Scatter(
                x=cat_df["date"].astype(str),
                y=cat_df["cumulative"],
                mode="lines+markers",
                name=cat,
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))

            # Dashed limit line
            cat_limit = float(limits.get(cat.lower(), 0) or 0)
            if cat_limit > 0:
                fig.add_hline(
                    y=cat_limit, line_dash="dash",
                    line_color=color, opacity=0.5,
                    annotation_text=f"{cat} limit ${cat_limit:.0f}",
                    annotation_position="top right",
                )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font_color="#E2E8F0",
            legend=dict(orientation="h", y=-0.15),
            margin=dict(l=0, r=0, t=30, b=40),
            title="Cumulative Spend This Month by Category",
            xaxis_title="Date",
            yaxis_title="Cumulative USD",
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No claims found for this employee.")
