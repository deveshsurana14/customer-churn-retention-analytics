import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Customer Churn Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main { background-color: #F4F6FA; }
  .block-container { padding-top: 1rem; padding-bottom: 2rem; }

  [data-testid="metric-container"] {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 4px rgba(26,35,50,0.07);
  }
  [data-testid="metric-container"] label {
    color: #64748B !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  [data-testid="stMetricValue"] {
    color: #1A2332 !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
  }
  [data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

  .stTabs [data-baseweb="tab-list"] {
    background: #1A2332;
    border-radius: 10px 10px 0 0;
    gap: 4px;
    padding: 6px 8px;
  }
  .stTabs [data-baseweb="tab"] {
    color: #8898AA;
    font-weight: 500;
    font-size: 0.85rem;
    border-radius: 6px;
    padding: 6px 16px;
  }
  .stTabs [aria-selected="true"] {
    color: white !important;
    background: #2F80ED !important;
  }

  .page-header {
    background: linear-gradient(135deg, #1A2332 0%, #2C4A7C 60%, #2F80ED 100%);
    color: white;
    padding: 1.4rem 1.8rem;
    border-radius: 10px;
    margin-bottom: 1.25rem;
  }
  .page-header h2 { color: white !important; margin: 0; font-size: 1.5rem; }
  .page-header p  { color: #B0C4DE; margin: 0.2rem 0 0 0; font-size: 0.88rem; }

  .section-title {
    color: #1A2332;
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #2F80ED;
  }

  .insight-box {
    background: #EFF6FF;
    border-left: 4px solid #2F80ED;
    padding: 0.75rem 1rem;
    border-radius: 0 8px 8px 0;
    margin-top: 0.75rem;
    font-size: 0.88rem;
    color: #1A2332;
    line-height: 1.6;
  }

  .badge {
    display: inline-block;
    padding: 3px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Colours ───────────────────────────────────────────────────────
RISK_COLORS = {"Critical": "#C7363D", "High": "#E87722", "Medium": "#F2C94C", "Low": "#27AE60"}
QUAD_COLORS = {
    "High Risk · High Value": "#C7363D",
    "High Risk · Low Value":  "#E87722",
    "Low Risk · High Value":  "#27AE60",
    "Low Risk · Low Value":   "#2F80ED",
}
RISK_ORDER = ["Critical", "High", "Medium", "Low"]
PLOT_CFG   = dict(paper_bgcolor="white", plot_bgcolor="white",
                  font=dict(family="Segoe UI", color="#1A2332"),
                  margin=dict(l=40, r=20, t=40, b=40))

# ── Data ──────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "processed", "customer_risk_scores.csv")
    df = pd.read_csv(path)

    df["RiskScore"]    = (df["ChurnProbability"] * 100).round(1)
    df["ChurnFlag"]    = (df["Churn"] == "Yes").astype(int)
    df["ExpLoss"]      = (df["MonthlyCharges"] * df["ChurnProbability"]).round(2)
    df["RiskTierSort"] = df["RiskTier"].map({"Critical": 4, "High": 3, "Medium": 2, "Low": 1})
    df["SeniorLabel"]  = df["SeniorCitizen"].map({1: "Senior", 0: "Non-Senior"})
    df["FamilyType"]   = ((df["Partner"] == "Yes") | (df["Dependents"] == "Yes")).map(
                            {True: "Family", False: "Individual"})

    def value_tier(x):
        if x >= 80: return "Premium"
        if x >= 50: return "Standard"
        return "Basic"
    df["ValueTier"] = df["MonthlyCharges"].apply(value_tier)

    def tenure_band(t):
        if t <= 6:  return "0-6 mo (New)"
        if t <= 24: return "7-24 mo (Growing)"
        if t <= 48: return "25-48 mo (Established)"
        return "49+ mo (Loyal)"
    df["TenureBand"]     = df["tenure"].apply(tenure_band)
    df["TenureBandSort"] = df["tenure"].apply(lambda t: 1 if t<=6 else 2 if t<=24 else 3 if t<=48 else 4)

    def quadrant(r):
        hp = r["ChurnProbability"] >= 0.5
        hv = r["MonthlyCharges"]   >= 65
        if hp and hv: return "High Risk · High Value"
        if hp:        return "High Risk · Low Value"
        if hv:        return "Low Risk · High Value"
        return        "Low Risk · Low Value"
    df["Quadrant"] = df.apply(quadrant, axis=1)

    df["PriorityScore"] = (
        df["ChurnProbability"] * 0.6 +
        (df["MonthlyCharges"] / 120).clip(0, 1) * 0.4
    ).round(4)

    # estimated CLV
    def clv(r):
        months = 24 if r["Contract"] == "Two year" \
            else 12 if r["Contract"] == "One year" \
            else min(round(1 / r["ChurnProbability"]) if r["ChurnProbability"] > 0 else 36, 36)
        return round(r["MonthlyCharges"] * months, 2)
    df["EstCLV"] = df.apply(clv, axis=1)

    return df

df_all = load_data()

# ── Sidebar filters ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Filters")
    st.markdown("---")
    sel_risk    = st.multiselect("Risk Tier",        RISK_ORDER,                              default=RISK_ORDER)
    sel_contract= st.multiselect("Contract",         sorted(df_all["Contract"].unique()),     default=sorted(df_all["Contract"].unique()))
    sel_inet    = st.multiselect("Internet Service", sorted(df_all["InternetService"].unique()), default=sorted(df_all["InternetService"].unique()))
    sel_pay     = st.multiselect("Payment Method",   sorted(df_all["PaymentMethod"].unique()), default=sorted(df_all["PaymentMethod"].unique()))
    sel_senior  = st.multiselect("Customer Type",    ["Senior", "Non-Senior"],                default=["Senior", "Non-Senior"])
    st.markdown("---")
    st.caption("📁 Customer Churn Intelligence\n\n7,032 customers · XGBoost model")

df = df_all[
    df_all["RiskTier"].isin(sel_risk) &
    df_all["Contract"].isin(sel_contract) &
    df_all["InternetService"].isin(sel_inet) &
    df_all["PaymentMethod"].isin(sel_pay) &
    df_all["SeniorLabel"].isin(sel_senior)
].copy()

if df.empty:
    st.error("No data matches the current filters. Adjust the sidebar.")
    st.stop()

n = len(df)

# ── Shared computed values ────────────────────────────────────────
overall_churn     = df["ChurnFlag"].mean()
monthly_rev       = df["MonthlyCharges"].sum()
rev_at_risk       = df[df["RiskTier"].isin(["High","Critical"])]["MonthlyCharges"].sum()
exp_loss_monthly  = df["ExpLoss"].sum()
exp_loss_annual   = exp_loss_monthly * 12
crit_rev          = df[df["RiskTier"]=="Critical"]["MonthlyCharges"].sum()

def portfolio_health(d):
    total = len(d)
    if total == 0: return 0
    c = (d["RiskTier"]=="Critical").sum() / total * 1.0
    h = (d["RiskTier"]=="High").sum()     / total * 0.6
    m = (d["RiskTier"]=="Medium").sum()   / total * 0.2
    return round(max((1 - c - h - m) * 100, 0), 1)

health = portfolio_health(df)

def make_gauge(value, title, suffix="", max_val=100):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 13, "color": "#1A2332"}},
        number={"suffix": suffix, "font": {"size": 26, "color": "#1A2332"}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#CBD5E0"},
            "bar":  {"color": "#2F80ED", "thickness": 0.25},
            "steps": [
                {"range": [0,           max_val*0.50], "color": "#FEE2E2"},
                {"range": [max_val*0.50, max_val*0.75],"color": "#FEF3C7"},
                {"range": [max_val*0.75, max_val],     "color": "#D1FAE5"},
            ],
            "threshold": {"line":{"color":"#27AE60","width":3}, "thickness":0.75, "value":max_val*0.75}
        }
    ))
    fig.update_layout(height=220, margin=dict(l=20,r=20,t=50,b=10),
                      paper_bgcolor="white", font={"family":"Segoe UI"})
    return fig

def header(icon, title, subtitle):
    st.markdown(f"""
    <div class="page-header">
      <h2>{icon} {title}</h2>
      <p>{subtitle}</p>
    </div>""", unsafe_allow_html=True)

def section(label):
    st.markdown(f'<div class="section-title">{label}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "🏠 Command Center",
    "🔍 Risk Intelligence",
    "💰 Revenue Pulse",
    "🧬 Customer DNA",
    "⚔️ Retention War Room",
    "👤 Customer 360",
])

# ──────────────────────────────────────────────────────────────
# TAB 1  COMMAND CENTER
# ──────────────────────────────────────────────────────────────
with tabs[0]:
    header("🏠", "Command Center",
           "Executive overview · churn risk, revenue exposure, and portfolio health")

    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Total Customers",       f"{n:,}")
    k2.metric("Churn Rate",            f"{overall_churn:.1%}",
              delta=f"{overall_churn-0.265:+.1%} vs 26.5% baseline", delta_color="inverse")
    k3.metric("Revenue at Risk",       f"${rev_at_risk:,.0f}")
    k4.metric("Expected Monthly Loss", f"${exp_loss_monthly:,.0f}")
    k5.metric("Portfolio Health",      f"{health} / 100")

    st.write("")
    col1, col2, col3 = st.columns([1.1, 1, 1.1])

    with col1:
        section("Risk Tier Distribution")
        rc = (df.groupby("RiskTier").size()
                .reindex(RISK_ORDER).reset_index(name="n"))
        fig = px.pie(rc, values="n", names="RiskTier", hole=0.55,
                     color="RiskTier", color_discrete_map=RISK_COLORS)
        fig.update_traces(textinfo="percent+label", textfont_size=11,
                          pull=[0.05 if r=="Critical" else 0 for r in rc["RiskTier"]])
        fig.update_layout(height=280, showlegend=False, **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("Portfolio Health Score")
        st.plotly_chart(make_gauge(health, "Portfolio Health"), use_container_width=True)
        st.caption("75 + = Healthy · 50-74 = Monitor · < 50 = Alert")

    with col3:
        section("Churn Rate by Contract")
        bc = (df.groupby("Contract")["ChurnFlag"].mean()
                .reset_index(name="rate")
                .sort_values("rate"))
        fig = px.bar(bc, x="rate", y="Contract", orientation="h",
                     text=bc["rate"].map("{:.1%}".format),
                     color="rate",
                     color_continuous_scale=["#27AE60","#F2C94C","#C7363D"])
        fig.add_vline(x=overall_churn, line_dash="dash", line_color="#2F80ED",
                      annotation_text=f"Avg {overall_churn:.1%}",
                      annotation_position="top right")
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=280, xaxis_tickformat=".0%",
                          xaxis_title="", yaxis_title="", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    section("Risk Tier × Revenue Summary")
    summ = (df.groupby("RiskTier").agg(
                Customers       =("customerID",      "count"),
                Monthly_Revenue =("MonthlyCharges",  "sum"),
                Avg_Churn_Prob  =("ChurnProbability", "mean"),
                Exp_Loss        =("ExpLoss",          "sum"),
                Avg_CLV         =("EstCLV",           "mean"))
              .reindex(RISK_ORDER).reset_index())
    summ["Monthly_Revenue"] = summ["Monthly_Revenue"].map("${:,.0f}".format)
    summ["Avg_Churn_Prob"]  = summ["Avg_Churn_Prob"].map("{:.1%}".format)
    summ["Exp_Loss"]        = summ["Exp_Loss"].map("${:,.0f}".format)
    summ["Avg_CLV"]         = summ["Avg_CLV"].map("${:,.0f}".format)
    summ.columns = ["Risk Tier","Customers","Monthly Revenue",
                    "Avg Churn Prob","Expected Monthly Loss","Avg Est. CLV"]
    st.dataframe(summ, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# TAB 2  RISK INTELLIGENCE
# ──────────────────────────────────────────────────────────────
with tabs[1]:
    header("🔍", "Risk Intelligence",
           "Segment-level analysis · where churn risk concentrates")

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Critical Customers",   f"{(df['RiskTier']=='Critical').sum():,}")
    k2.metric("High Risk Rate",       f"{df['RiskTier'].isin(['High','Critical']).mean():.1%}")
    k3.metric("Avg Churn Probability",f"{df['ChurnProbability'].mean():.1%}")
    k4.metric("Avg Tenure",           f"{df['tenure'].mean():.0f} months")

    st.write("")
    section("Risk-Value Quadrant Explorer  ·  click the legend to toggle groups")
    st.caption("X = tenure · Y = monthly charges · bubble size = expected revenue loss")

    fig = px.scatter(
        df, x="tenure", y="MonthlyCharges",
        size="ExpLoss", size_max=20,
        color="Quadrant", color_discrete_map=QUAD_COLORS,
        hover_data={"customerID":True, "RiskTier":True,
                    "ChurnProbability":":.1%", "Contract":True,
                    "RecommendedAction":True, "ExpLoss":":.2f",
                    "tenure":False, "MonthlyCharges":False},
        labels={"tenure":"Tenure (months)","MonthlyCharges":"Monthly Charges ($)"},
        opacity=0.75,
    )
    fig.add_hline(y=65, line_dash="dot", line_color="#94A3B8",
                  annotation_text="Premium threshold ($65)", annotation_position="bottom right")
    fig.add_vline(x=12, line_dash="dot", line_color="#94A3B8",
                  annotation_text="12-month mark", annotation_position="top left")
    fig.update_layout(height=440, legend_title="Risk-Value Quadrant", **PLOT_CFG)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        section("Risk Concentration by Contract")
        ct = (df.groupby(["Contract","RiskTier"]).size()
                .reset_index(name="n"))
        ct["RiskTier"] = pd.Categorical(ct["RiskTier"], RISK_ORDER, ordered=True)
        fig = px.bar(ct, x="n", y="Contract", color="RiskTier",
                     color_discrete_map=RISK_COLORS, orientation="h",
                     barmode="stack",
                     category_orders={"RiskTier": RISK_ORDER})
        fig.update_layout(height=300, legend_title="Risk Tier",
                          xaxis_title="Customers", yaxis_title="", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Risk Concentration by Internet Service")
        it = (df.groupby(["InternetService","RiskTier"]).size()
                .reset_index(name="n"))
        it["RiskTier"] = pd.Categorical(it["RiskTier"], RISK_ORDER, ordered=True)
        fig = px.bar(it, x="n", y="InternetService", color="RiskTier",
                     color_discrete_map=RISK_COLORS, orientation="h",
                     barmode="stack",
                     category_orders={"RiskTier": RISK_ORDER})
        fig.update_layout(height=300, legend_title="Risk Tier",
                          xaxis_title="Customers", yaxis_title="", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
      <b>Key Findings:</b><br>
      • Month-to-month contracts concentrate the most Critical and High-risk customers.<br>
      • Fiber optic subscribers show disproportionate churn risk relative to their customer share.<br>
      • New customers (0-12 months, upper-left quadrant) with high monthly charges are highest priority.
    </div>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# TAB 3  REVENUE PULSE
# ──────────────────────────────────────────────────────────────
with tabs[2]:
    header("💰", "Revenue Pulse",
           "Financial exposure · how much revenue is actually at risk in dollar terms")

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Monthly Revenue",         f"${monthly_rev:,.0f}")
    k2.metric("Revenue at Risk",         f"${rev_at_risk:,.0f}",
              delta=f"{rev_at_risk/monthly_rev:.1%} of total", delta_color="inverse")
    k3.metric("Expected Annual Loss",    f"${exp_loss_annual:,.0f}")
    k4.metric("Critical Revenue at Risk",f"${crit_rev:,.0f}")

    st.write("")
    c1, c2 = st.columns(2)

    with c1:
        section("Monthly Revenue Waterfall by Risk Tier")
        tier_rev = (df.groupby("RiskTier")["MonthlyCharges"]
                      .sum().reindex(RISK_ORDER).fillna(0))
        x_labels = list(RISK_ORDER) + ["Total"]
        y_vals   = list(tier_rev.values) + [monthly_rev]
        measures = ["relative"] * len(RISK_ORDER) + ["total"]
        wf_colors= [RISK_COLORS[t] for t in RISK_ORDER] + ["#2F80ED"]

        fig = go.Figure(go.Waterfall(
            x=x_labels, y=y_vals, measure=measures,
            connector={"line":{"color":"#E2E8F0"}},
            text=[f"${v:,.0f}" for v in y_vals],
            textposition="outside",
        ))
        fig.data[0].marker.color = wf_colors
        fig.update_layout(height=340, showlegend=False,
                          yaxis_title="Monthly Revenue ($)", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Revenue at Risk · Internet Service × Risk Tier")
        at_risk = df[df["RiskTier"].isin(["High","Critical"])]
        tree = (at_risk.groupby(["InternetService","RiskTier"])["MonthlyCharges"]
                       .sum().reset_index())
        fig = px.treemap(tree, path=["InternetService","RiskTier"],
                         values="MonthlyCharges",
                         color="RiskTier", color_discrete_map=RISK_COLORS)
        fig.update_traces(texttemplate="%{label}<br>$%{value:,.0f}")
        fig.update_layout(height=340, **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    section("Expected Revenue Loss by Payment Method")
    pay_loss = (df.groupby("PaymentMethod")["ExpLoss"]
                  .sum().reset_index(name="loss")
                  .sort_values("loss"))
    fig = px.bar(pay_loss, x="loss", y="PaymentMethod", orientation="h",
                 text=pay_loss["loss"].map("${:,.0f}".format),
                 color="loss",
                 color_continuous_scale=["#FEF3C7","#E87722","#C7363D"])
    fig.update_traces(textposition="outside")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(height=230, xaxis_title="Expected Monthly Loss ($)",
                      yaxis_title="", **PLOT_CFG)
    st.plotly_chart(fig, use_container_width=True)

    section("Top 20 At-Risk Customers by Expected Revenue Loss")
    top20 = (df[df["RiskTier"].isin(["High","Critical"])]
               .sort_values("ExpLoss", ascending=False).head(20))
    tbl = top20[["customerID","RiskTier","ChurnProbability",
                 "MonthlyCharges","ExpLoss","Contract","RecommendedAction"]].copy()
    tbl["ChurnProbability"] = tbl["ChurnProbability"].map("{:.1%}".format)
    tbl["MonthlyCharges"]   = tbl["MonthlyCharges"].map("${:.2f}".format)
    tbl["ExpLoss"]          = tbl["ExpLoss"].map("${:.2f}".format)
    tbl.columns = ["Customer ID","Risk Tier","Churn Prob",
                   "Monthly $","Expected Loss","Contract","Action"]
    st.dataframe(tbl, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# TAB 4  CUSTOMER DNA
# ──────────────────────────────────────────────────────────────
with tabs[3]:
    header("🧬", "Customer DNA",
           "Demographic and behavioural fingerprint of churn risk")

    TENURE_ORDER = ["0-6 mo (New)","7-24 mo (Growing)","25-48 mo (Established)","49+ mo (Loyal)"]

    c1, c2 = st.columns(2)

    with c1:
        section("Churn Rate by Tenure Band")
        tb = (df.groupby("TenureBand")["ChurnFlag"]
                .agg(["mean","count"]).reset_index())
        tb.columns = ["TenureBand","ChurnRate","Count"]
        tb["TenureBand"] = pd.Categorical(tb["TenureBand"], TENURE_ORDER, ordered=True)
        tb = tb.sort_values("TenureBand")
        fig = px.bar(tb, x="TenureBand", y="ChurnRate",
                     text=tb["ChurnRate"].map("{:.1%}".format),
                     color="ChurnRate",
                     color_continuous_scale=["#27AE60","#F2C94C","#C7363D"])
        fig.add_hline(y=overall_churn, line_dash="dash", line_color="#2F80ED",
                      annotation_text=f"Avg {overall_churn:.1%}")
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=300, yaxis_tickformat=".0%",
                          xaxis_title="", yaxis_title="Churn Rate", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Churn Rate by Customer Value Tier")
        vt = (df.groupby("ValueTier")["ChurnFlag"]
                .mean().reindex(["Basic","Standard","Premium"]).reset_index(name="ChurnRate"))
        vc = {"Basic":"#E87722","Standard":"#F2C94C","Premium":"#27AE60"}
        fig = px.bar(vt, x="ValueTier", y="ChurnRate",
                     text=vt["ChurnRate"].map("{:.1%}".format),
                     color="ValueTier", color_discrete_map=vc)
        fig.add_hline(y=overall_churn, line_dash="dash", line_color="#2F80ED")
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, yaxis_tickformat=".0%", showlegend=False,
                          xaxis_title="", yaxis_title="Churn Rate", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        section("Churn Distribution by Gender")
        gc = (df.groupby(["gender","Churn"]).size()
                .reset_index(name="n"))
        fig = px.bar(gc, x="n", y="gender", color="Churn",
                     color_discrete_map={"Yes":"#C7363D","No":"#27AE60"},
                     orientation="h", barmode="stack", text="n")
        fig.update_traces(textposition="inside")
        fig.update_layout(height=260, legend_title="Churned",
                          xaxis_title="Customers", yaxis_title="", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Churn Rate · Senior vs Non-Senior")
        sc = (df.groupby("SeniorLabel")["ChurnFlag"]
                .mean().reset_index(name="ChurnRate"))
        fig = px.bar(sc, x="SeniorLabel", y="ChurnRate",
                     text=sc["ChurnRate"].map("{:.1%}".format),
                     color="ChurnRate",
                     color_continuous_scale=["#27AE60","#C7363D"])
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=260, yaxis_tickformat=".0%", showlegend=False,
                          xaxis_title="", yaxis_title="Churn Rate", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    section("Churn Rate Heat Map · Payment Method × Contract")
    hmap = (df.groupby(["PaymentMethod","Contract"])["ChurnFlag"]
              .mean().unstack(fill_value=0))
    fig = px.imshow(hmap,
                    color_continuous_scale=["#27AE60","#FEF3C7","#C7363D"],
                    text_auto=".1%", aspect="auto",
                    labels={"color":"Churn Rate"})
    fig.update_layout(height=280, **PLOT_CFG)
    st.plotly_chart(fig, use_container_width=True)

    section("Churn Rate by Internet Service")
    ic = (df.groupby("InternetService")["ChurnFlag"]
            .mean().reset_index(name="ChurnRate"))
    inet_c = {"Fiber optic":"#C7363D","DSL":"#E87722","No":"#27AE60"}
    fig = px.bar(ic, x="InternetService", y="ChurnRate",
                 text=ic["ChurnRate"].map("{:.1%}".format),
                 color="InternetService", color_discrete_map=inet_c)
    fig.update_traces(textposition="outside")
    fig.update_layout(height=260, yaxis_tickformat=".0%", showlegend=False,
                      xaxis_title="", yaxis_title="Churn Rate", **PLOT_CFG)
    st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# TAB 5  RETENTION WAR ROOM
# ──────────────────────────────────────────────────────────────
with tabs[4]:
    header("⚔️", "Retention War Room",
           "Operational action centre · prioritised queue for the retention team")

    action_df  = df[df["RecommendedAction"] != "No immediate action"].copy()
    priority_df= df[df["RiskTier"].isin(["High","Critical"]) & (df["MonthlyCharges"] >= 65)]
    recovery   = action_df["MonthlyCharges"].sum() * 12 * 0.30

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Customers Needing Action",     f"{len(action_df):,}")
    k2.metric("Retention Action Rate",        f"{len(action_df)/n:.1%}")
    k3.metric("Priority Intervention",        f"{len(priority_df):,}",
              help="High/Critical risk + MonthlyCharges ≥ $65")
    k4.metric("Revenue Recovery Potential",   f"${recovery:,.0f}",
              help="Est. annual revenue saved at 30 % retention success")

    st.write("")
    c1, c2 = st.columns(2)

    with c1:
        section("Customers by Recommended Action")
        ac = (action_df.groupby("RecommendedAction").size()
                       .reset_index(name="n").sort_values("n"))
        fig = px.bar(ac, x="n", y="RecommendedAction", orientation="h",
                     text="n", color="n",
                     color_continuous_scale=["#FEF3C7","#E87722","#C7363D"])
        fig.update_traces(textposition="outside")
        fig.update_coloraxes(showscale=False)
        fig.update_layout(height=320, xaxis_title="Customers",
                          yaxis_title="", **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Revenue at Stake per Action Type")
        ar = (action_df.groupby("RecommendedAction")["ExpLoss"]
                        .sum().reset_index(name="loss")
                        .sort_values("loss", ascending=False))
        fig = go.Figure(go.Funnel(
            y=ar["RecommendedAction"], x=ar["loss"],
            texttemplate="$%{x:,.0f}",
            marker={"color": ["#C7363D","#E87722","#F2C94C",
                              "#2F80ED","#27AE60","#9B51E0"][:len(ar)]}
        ))
        fig.update_layout(height=320, **PLOT_CFG)
        st.plotly_chart(fig, use_container_width=True)

    section("Live Retention Queue · High & Critical Customers")
    st.caption("Sorted by Priority Score (higher = act now) · filter with the sidebar")

    queue = (df[df["RiskTier"].isin(["High","Critical"]) &
                (df["RecommendedAction"] != "No immediate action")]
               .sort_values("PriorityScore", ascending=False)
               [["PriorityScore","customerID","RiskTier","ChurnProbability",
                 "MonthlyCharges","tenure","Contract","RecommendedAction",
                 "InternetService","PaymentMethod"]].copy())
    queue["ChurnProbability"] = queue["ChurnProbability"].map("{:.1%}".format)
    queue["MonthlyCharges"]   = queue["MonthlyCharges"].map("${:.0f}".format)
    queue["PriorityScore"]    = queue["PriorityScore"].map("{:.3f}".format)
    queue.columns = ["Priority","Customer ID","Risk Tier","Churn Prob",
                     "Monthly $","Tenure","Contract","Action","Internet","Payment"]
    st.dataframe(queue, use_container_width=True, hide_index=True, height=420)


# ──────────────────────────────────────────────────────────────
# TAB 6  CUSTOMER 360
# ──────────────────────────────────────────────────────────────
with tabs[5]:
    header("👤", "Customer 360",
           "Individual customer profile · full risk and behavioural snapshot")

    search_col, _ = st.columns([2, 3])
    with search_col:
        cid = st.selectbox(
            "Search Customer ID",
            options=[""] + sorted(df["customerID"].tolist()),
            index=0,
        )

    if not cid:
        st.markdown("""
        <div class="insight-box">
          Select a Customer ID from the dropdown to view their full profile, risk score, and
          recommended retention action. You can type to search within the list.
        </div>""", unsafe_allow_html=True)

        st.write("")
        section("Sample Critical-Risk Customers to Explore")
        sample = (df[df["RiskTier"]=="Critical"]
                    .sort_values("PriorityScore", ascending=False).head(8)
                    [["customerID","RiskTier","ChurnProbability",
                      "MonthlyCharges","RecommendedAction"]].copy())
        sample["ChurnProbability"] = sample["ChurnProbability"].map("{:.1%}".format)
        sample["MonthlyCharges"]   = sample["MonthlyCharges"].map("${:.2f}".format)
        sample.columns = ["Customer ID","Risk Tier","Churn Prob","Monthly $","Recommended Action"]
        st.dataframe(sample, use_container_width=True, hide_index=True)

    else:
        if cid not in df["customerID"].values:
            st.warning(f"Customer '{cid}' not found in the current filtered dataset. "
                       "Try adjusting the sidebar filters.")
        else:
            r   = df[df["customerID"] == cid].iloc[0]
            tier= r["RiskTier"]
            tc  = RISK_COLORS.get(tier, "#2F80ED")
            fc  = "white" if tier != "Medium" else "#1A2332"

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">
              <span style="font-size:1.35rem;font-weight:700;color:#1A2332;">{cid}</span>
              <span class="badge" style="background:{tc};color:{fc};">{tier} Risk</span>
            </div>""", unsafe_allow_html=True)

            k1,k2,k3,k4,k5 = st.columns(5)
            k1.metric("Churn Probability",   f"{r['ChurnProbability']:.1%}")
            k2.metric("Risk Score",          f"{r['RiskScore']:.0f} / 100")
            k3.metric("Monthly Charges",     f"${r['MonthlyCharges']:.2f}")
            k4.metric("Total Charges",       f"${r['TotalCharges']:,.2f}")
            k5.metric("Tenure",              f"{r['tenure']} months")

            st.write("")
            g1, g2 = st.columns([1, 2])

            with g1:
                st.plotly_chart(
                    make_gauge(r["ChurnProbability"]*100,
                               "Churn Probability", suffix="%"),
                    use_container_width=True
                )
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                            padding:0.9rem;margin-top:0.5rem;">
                  <div style="font-size:0.72rem;color:#64748B;text-transform:uppercase;
                              letter-spacing:.05em;margin-bottom:0.2rem;">Recommended Action</div>
                  <div style="font-weight:700;color:#1A2332;">{r['RecommendedAction']}</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                            padding:0.9rem;margin-top:0.5rem;">
                  <div style="font-size:0.72rem;color:#64748B;text-transform:uppercase;
                              letter-spacing:.05em;margin-bottom:0.2rem;">Priority Score</div>
                  <div style="font-weight:700;color:#1A2332;">{r['PriorityScore']:.4f}</div>
                </div>
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
                            padding:0.9rem;margin-top:0.5rem;">
                  <div style="font-size:0.72rem;color:#64748B;text-transform:uppercase;
                              letter-spacing:.05em;margin-bottom:0.2rem;">Estimated CLV</div>
                  <div style="font-weight:700;color:#1A2332;">${r['EstCLV']:,.2f}</div>
                </div>""", unsafe_allow_html=True)

            with g2:
                section("Full Customer Profile")
                profile = pd.DataFrame({
                    "Attribute": [
                        "Gender","Senior Citizen","Partner","Dependents","Family Type",
                        "Contract","Internet Service","Payment Method",
                        "Churn Status","Value Tier","Risk-Value Quadrant",
                        "Tenure Band","Expected Revenue Loss"
                    ],
                    "Value": [
                        r["gender"], r["SeniorLabel"], r["Partner"], r["Dependents"],
                        r["FamilyType"], r["Contract"], r["InternetService"],
                        r["PaymentMethod"], r["Churn"], r["ValueTier"],
                        r["Quadrant"], r["TenureBand"],
                        f"${r['ExpLoss']:.2f} / month"
                    ]
                })
                st.dataframe(profile, use_container_width=True,
                             hide_index=True, height=400)
