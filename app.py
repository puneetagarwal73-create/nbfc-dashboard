"""
NBFC Intelligence Dashboard — India's Top NBFCs
Data: FY2021-FY2025 | Source: RBI/FIDC, Screener.in, Rating agencies
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="NBFC Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nbfc_full.db")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 20px 30px; border-radius: 12px; margin-bottom: 20px;
    border-left: 5px solid #e94560;
}
.main-header h1 { color: white; margin: 0; font-size: 28px; font-weight: 700; }
.main-header p { color: #a0aec0; margin: 5px 0 0; font-size: 14px; }
.kcard {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #2d3748; border-radius: 10px;
    padding: 16px; text-align: center; height: 110px;
}
.kcard .val { font-size: 28px; font-weight: 700; color: #63b3ed; }
.kcard .lbl { font-size: 12px; color: #a0aec0; margin-top: 4px; }
.kcard .sub { font-size: 11px; color: #68d391; margin-top: 2px; }
.estimated-note {
    background: #2d3748; border-left: 3px solid #f6ad55;
    padding: 8px 12px; border-radius: 4px; font-size: 12px; color: #f6ad55;
    margin-bottom: 10px;
}
.tag-estimated { background: #744210; color: #f6ad55; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
.tag-actual { background: #1a4731; color: #68d391; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>📊 NBFC Intelligence Dashboard</h1>
    <p>India's Non-Banking Financial Companies | FY2021–FY2025 | 9,359 NBFCs tracked | Source: RBI/FIDC, Screener.in, Rating Agencies</p>
</div>
""", unsafe_allow_html=True)

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    conn = sqlite3.connect(DB_PATH)
    nbfc = pd.read_sql("SELECT * FROM nbfc", conn)
    fins = pd.read_sql("SELECT * FROM financials", conn)
    conn.close()
    nbfc["listed"] = nbfc["listed"].astype(bool)
    nbfc["has_financials"] = nbfc["has_financials"].astype(bool)
    return nbfc, fins


@st.cache_data(ttl=300)
def compute_metrics(nbfc_df, fins_df):
    """Compute CAGR, avg ROA, avg ROE, avg GNPA per NBFC."""
    metrics = []
    for nbfc_id, grp in fins_df.groupby("nbfc_id"):
        grp = grp.sort_values("fiscal_year")
        fys = grp["fiscal_year"].tolist()

        # AUM CAGR (loan_book preferred, else total_assets)
        cagr_col = "loan_book" if grp["loan_book"].notna().sum() >= 2 else "total_assets"
        cagr_rows = grp[grp[cagr_col].notna()]
        cagr = None
        if len(cagr_rows) >= 2:
            start_val = cagr_rows.iloc[0][cagr_col]
            end_val = cagr_rows.iloc[-1][cagr_col]
            n_years = len(cagr_rows) - 1
            if start_val and start_val > 0 and end_val and end_val > 0:
                cagr = ((end_val / start_val) ** (1 / n_years) - 1) * 100

        # Asset CAGR
        asset_cagr = None
        asset_rows = grp[grp["total_assets"].notna()]
        if len(asset_rows) >= 2:
            s = asset_rows.iloc[0]["total_assets"]
            e = asset_rows.iloc[-1]["total_assets"]
            n = len(asset_rows) - 1
            if s and s > 0 and e and e > 0:
                asset_cagr = ((e / s) ** (1 / n) - 1) * 100

        latest_row = grp[grp["total_assets"].notna()].iloc[-1] if len(grp[grp["total_assets"].notna()]) else None

        metrics.append({
            "nbfc_id": nbfc_id,
            "aum_cagr": round(cagr, 1) if cagr is not None else None,
            "asset_cagr": round(asset_cagr, 1) if asset_cagr is not None else None,
            "avg_roa": round(grp["roa"].dropna().mean(), 2) if grp["roa"].notna().any() else None,
            "avg_roe": round(grp["roe"].dropna().mean(), 1) if grp["roe"].notna().any() else None,
            "latest_gnpa": grp[grp["gnpa_pct"].notna()].iloc[-1]["gnpa_pct"] if grp["gnpa_pct"].notna().any() else None,
            "avg_gnpa": round(grp["gnpa_pct"].dropna().mean(), 2) if grp["gnpa_pct"].notna().any() else None,
            "gnpa_trend": round(grp["gnpa_pct"].dropna().iloc[-1] - grp["gnpa_pct"].dropna().iloc[0], 2) if grp["gnpa_pct"].notna().sum() >= 2 else None,
            "latest_assets": latest_row["total_assets"] if latest_row is not None else None,
            "latest_pat": latest_row["pat"] if latest_row is not None else None,
            "latest_fy": fys[-1] if fys else None,
            "fy_count": len(fys),
        })

    metrics_df = pd.DataFrame(metrics)
    # Rename to avoid collision with nbfc_df.latest_assets
    metrics_df = metrics_df.rename(columns={"latest_assets": "fin_latest_assets"})
    result = nbfc_df.merge(metrics_df, left_on="id", right_on="nbfc_id", how="left")
    # Use financial latest_assets where available, fallback to registry value
    result["disp_assets"] = result["fin_latest_assets"].combine_first(result["latest_assets"])
    return result


nbfc_df, fins_df = load_all()
full_df = compute_metrics(nbfc_df, fins_df)
has_fin_df = full_df[full_df["has_financials"] == True].copy()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔧 Filters")

    layer_opts = ["All Layers"] + sorted(nbfc_df["rbi_layer"].dropna().unique().tolist())
    sel_layer = st.selectbox("RBI Layer", layer_opts)

    cat_opts = ["All"] + sorted(has_fin_df["category"].dropna().unique().tolist())
    sel_cat = st.selectbox("Sector / Category", cat_opts)

    listing_opts = ["All", "Listed Only", "Unlisted Only"]
    sel_listing = st.selectbox("Listing Status", listing_opts)

    top_n = st.slider("Top N companies", 10, 80, 40)
    show_estimated = st.checkbox("Include estimated data", value=True)

    st.markdown("---")
    st.markdown("""
    **Data Sources**
    - 🏦 RBI/FIDC NBFC Registry
    - 📈 Screener.in (listed companies)
    - ⭐ CRISIL/ICRA/CARE reports
    - 🗓️ FY2021–FY2025
    """)
    st.markdown(f"**Coverage:** {has_fin_df.shape[0]} companies with financial data")
    if "data_quality" in has_fin_df.columns:
        est_cnt = has_fin_df[has_fin_df["data_quality"] == "estimated"].shape[0]
        st.markdown(f"**Estimated data:** {est_cnt} unlisted companies")


# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
def apply_filters(df):
    if sel_layer != "All Layers":
        df = df[df["rbi_layer"] == sel_layer]
    if sel_cat != "All":
        df = df[df["category"] == sel_cat]
    if sel_listing == "Listed Only":
        df = df[df["listed"] == True]
    elif sel_listing == "Unlisted Only":
        df = df[df["listed"] == False]
    if not show_estimated and "data_quality" in df.columns:
        df = df[df["data_quality"] != "estimated"]
    return df


filt_df = apply_filters(has_fin_df)

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
total_assets_lkh = has_fin_df["disp_assets"].sum() / 1e5
avg_cagr = has_fin_df["aum_cagr"].dropna().mean()
avg_roa = has_fin_df["avg_roa"].dropna().mean()
avg_gnpa = has_fin_df["latest_gnpa"].dropna().mean()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown("""<div class="kcard"><div class="val">9,359</div>
        <div class="lbl">Total NBFCs (RBI)</div><div class="sub">Upper·Middle·Base</div></div>""",
        unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kcard"><div class="val">{has_fin_df.shape[0]}</div>
        <div class="lbl">With Financial Data</div><div class="sub">FY2021–FY2025</div></div>""",
        unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kcard"><div class="val">₹{total_assets_lkh:.1f}L Cr</div>
        <div class="lbl">Combined Assets</div><div class="sub">of tracked companies</div></div>""",
        unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kcard"><div class="val">{avg_cagr:.1f}%</div>
        <div class="lbl">Avg AUM CAGR</div><div class="sub">across tracked NBFCs</div></div>""",
        unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kcard"><div class="val">{avg_gnpa:.1f}%</div>
        <div class="lbl">Avg GNPA %</div><div class="sub">latest available</div></div>""",
        unsafe_allow_html=True)

st.markdown("")

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab_cl, tab4, tab5, tab6, tab7 = st.tabs([
    "🏆 Growth Rankings",
    "💰 Profitability",
    "🏦 Asset Quality",
    "📉 Credit Losses",
    "📈 Trend Analysis",
    "🔍 Company Deep-Dive",
    "🌐 Full Universe",
    "📋 Raw Data",
])

# ─── TAB 1: GROWTH RANKINGS ──────────────────────────────────────────────────
with tab1:
    st.subheader("🏆 AUM Growth Leaderboard")
    st.markdown('<div class="estimated-note">⚠️ Estimated data (unlisted companies) shown with ★ — based on credit rating agency reports, not audited accounts</div>', unsafe_allow_html=True)

    df_g = filt_df[filt_df["aum_cagr"].notna()].copy()
    df_g = df_g.sort_values("aum_cagr", ascending=False)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**🚀 Fastest Growing (Top 20)**")
        top20 = df_g.head(20).copy()
        top20["label"] = top20["name"].str[:35] + top20.apply(
            lambda r: " ★" if r.get("data_quality") == "estimated" else "", axis=1)
        fig = px.bar(top20, x="aum_cagr", y="label", orientation="h",
                     color="category", height=550,
                     labels={"aum_cagr": "AUM CAGR (%)", "label": ""},
                     title="Fastest Growing NBFCs")
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False,
                          plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                          font=dict(color="white", size=11))
        fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**🐢 Slowest Growing / Declining (Bottom 20)**")
        bot20 = df_g.tail(20).copy()
        bot20["label"] = bot20["name"].str[:35]
        fig2 = px.bar(bot20, x="aum_cagr", y="label", orientation="h",
                      color="category", height=550,
                      labels={"aum_cagr": "AUM CAGR (%)", "label": ""},
                      title="Slowest Growing NBFCs")
        fig2.update_layout(yaxis=dict(autorange="reversed"), showlegend=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white", size=11))
        fig2.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # Growth vs profitability bubble
    st.subheader("📊 Growth vs Profitability Bubble Chart")
    df_bubble = filt_df[filt_df["aum_cagr"].notna() & filt_df["disp_assets"].notna()].copy()
    df_bubble["size_val"] = (df_bubble["disp_assets"].clip(upper=500000) / 1000).clip(lower=1)
    df_bubble["label"] = df_bubble["name"].str[:30]
    fig3 = px.scatter(
        df_bubble.head(top_n), x="aum_cagr", y="avg_roa",
        size="size_val", color="category",
        hover_name="label",
        hover_data={"aum_cagr": ":.1f", "avg_roa": ":.2f", "disp_assets": ":,.0f"},
        labels={"aum_cagr": "AUM CAGR (%)", "avg_roa": "Avg ROA (%)", "size_val": "Assets (₹ '000 Cr)"},
        title="Growth (CAGR) vs Profitability (ROA) — Bubble size = Assets",
        height=500,
    )
    fig3.add_vline(x=df_bubble["aum_cagr"].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig3.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.5)
    fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
    st.plotly_chart(fig3, use_container_width=True)


# ─── TAB 2: PROFITABILITY ────────────────────────────────────────────────────
with tab2:
    st.subheader("💰 Profitability Analysis")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Most Profitable — by ROA**")
        df_roa = filt_df[filt_df["avg_roa"].notna()].sort_values("avg_roa", ascending=False)
        df_roa["label"] = df_roa["name"].str[:35]
        fig = px.bar(df_roa.head(20), x="avg_roa", y="label", orientation="h",
                     color="avg_roa", color_continuous_scale="Greens",
                     labels={"avg_roa": "Avg ROA (%)", "label": ""},
                     title="Top 20 by Return on Assets", height=550)
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                          plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white", size=11))
        fig.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Most Profitable — by ROE**")
        df_roe = filt_df[filt_df["avg_roe"].notna()].sort_values("avg_roe", ascending=False)
        df_roe["label"] = df_roe["name"].str[:35]
        fig2 = px.bar(df_roe.head(20), x="avg_roe", y="label", orientation="h",
                      color="avg_roe", color_continuous_scale="Blues",
                      labels={"avg_roe": "Avg ROE (%)", "label": ""},
                      title="Top 20 by Return on Equity", height=550)
        fig2.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white", size=11))
        fig2.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # By sector
    st.subheader("📊 Profitability by Sector")
    df_cat = filt_df[filt_df["avg_roa"].notna()].groupby("category").agg(
        avg_roa=("avg_roa", "mean"),
        avg_roe=("avg_roe", "mean"),
        count=("name", "count"),
    ).reset_index().sort_values("avg_roa", ascending=False)

    fig3 = px.bar(df_cat, x="category", y=["avg_roa", "avg_roe"],
                  barmode="group", height=400,
                  labels={"value": "Return (%)", "category": "Sector"},
                  title="Average ROA & ROE by Sector")
    fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                       font=dict(color="white"), xaxis_tickangle=-30)
    st.plotly_chart(fig3, use_container_width=True)

    # PAT trend
    st.subheader("📈 PAT Trend — Top Companies")
    top_by_pat = filt_df[filt_df["latest_pat"].notna()].nlargest(min(12, top_n), "latest_pat")
    pat_data = fins_df[fins_df["nbfc_id"].isin(top_by_pat["id"])].merge(
        nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id"
    )
    fig4 = px.line(pat_data, x="fiscal_year", y="pat", color="name",
                   labels={"pat": "PAT (₹ Cr)", "fiscal_year": "FY", "name": ""},
                   title="Net Profit (PAT) Trend — Top NBFCs", height=420)
    fig4.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                       font=dict(color="white"), legend=dict(font=dict(size=10)))
    fig4.update_traces(line=dict(width=2))
    st.plotly_chart(fig4, use_container_width=True)


# ─── TAB 3: ASSET QUALITY ────────────────────────────────────────────────────
with tab3:
    st.subheader("🏦 Asset Quality — GNPA Analysis")

    df_gnpa = filt_df[filt_df["latest_gnpa"].notna()].sort_values("latest_gnpa")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Best Asset Quality (Low GNPA)**")
        top_gnpa = df_gnpa.head(20).copy()
        top_gnpa["label"] = top_gnpa["name"].str[:35]
        fig = px.bar(top_gnpa, x="latest_gnpa", y="label", orientation="h",
                     color="latest_gnpa", color_continuous_scale="RdYlGn_r",
                     labels={"latest_gnpa": "GNPA %", "label": ""},
                     title="Cleanest Loan Books", height=520)
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                          plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white", size=11))
        fig.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("**Highest Stress (High GNPA)**")
        bot_gnpa = df_gnpa.tail(20).sort_values("latest_gnpa", ascending=False).copy()
        bot_gnpa["label"] = bot_gnpa["name"].str[:35]
        fig2 = px.bar(bot_gnpa, x="latest_gnpa", y="label", orientation="h",
                      color="latest_gnpa", color_continuous_scale="Reds",
                      labels={"latest_gnpa": "GNPA %", "label": ""},
                      title="Highest NPA Stress", height=520)
        fig2.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white", size=11))
        fig2.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # GNPA sector trend
    st.subheader("📉 GNPA Trend — by Sector")
    gnpa_trend = fins_df[fins_df["gnpa_pct"].notna()].merge(
        nbfc_df[["id", "name", "category"]], left_on="nbfc_id", right_on="id"
    )
    gnpa_sector = gnpa_trend.groupby(["fiscal_year", "category"])["gnpa_pct"].mean().reset_index()
    fig3 = px.line(gnpa_sector, x="fiscal_year", y="gnpa_pct", color="category",
                   labels={"gnpa_pct": "Avg GNPA %", "fiscal_year": "FY", "category": "Sector"},
                   title="GNPA % Trend by Sector", height=400)
    fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
    st.plotly_chart(fig3, use_container_width=True)

    # Heatmap
    st.subheader("🗺️ GNPA Heatmap")
    pivot_gnpa = fins_df[fins_df["gnpa_pct"].notna()].merge(
        nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id"
    ).pivot_table(index="name", columns="fiscal_year", values="gnpa_pct")
    pivot_gnpa["latest"] = pivot_gnpa.max(axis=1)
    pivot_gnpa = pivot_gnpa.sort_values("latest", ascending=False).drop(columns=["latest"]).head(35)
    pivot_gnpa.index = pivot_gnpa.index.str[:35]
    fig4 = px.imshow(pivot_gnpa, color_continuous_scale="RdYlGn_r",
                     aspect="auto", height=700,
                     labels={"color": "GNPA %"},
                     title="GNPA % Heatmap — Top 35 NBFCs by Stress")
    fig4.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white", size=10))
    st.plotly_chart(fig4, use_container_width=True)


# ─── TAB CREDIT LOSSES ───────────────────────────────────────────────────────
with tab_cl:
    st.subheader("📉 Annualized Credit Losses")

    st.markdown("""
    **Credit Loss Rate = Net Credit Losses / Loan Book (AUM) × 100**

    Credit losses = provisions for loan impairment + net write-offs − recoveries on previously written-off loans.
    This measures the actual P&L cost of defaults in a period — distinct from GNPA% (which is a balance sheet stock).
    A lower credit loss rate means fewer actual losses incurred relative to the loan portfolio.
    """)
    st.markdown('<div class="estimated-note">⚠️ Figures for unlisted companies (★) are estimated from rating agency reports</div>', unsafe_allow_html=True)

    # Pull credit cost data
    cl_data = fins_df[fins_df["credit_cost_pct"].notna()].merge(
        nbfc_df[["id", "name", "category", "rbi_layer", "listed", "data_quality"]],
        left_on="nbfc_id", right_on="id"
    )
    cl_data = cl_data[cl_data["name"].isin(filt_df["name"])]

    # ── Latest year credit cost per company ───────────────────────────────────
    latest_cl = (
        cl_data.sort_values("fiscal_year")
        .groupby("name", as_index=False)
        .last()[["name", "fiscal_year", "credit_cost_pct", "credit_losses",
                 "loan_book", "category", "rbi_layer", "listed", "data_quality"]]
    )
    latest_cl = latest_cl.sort_values("credit_cost_pct")
    latest_cl["label"] = latest_cl["name"].str[:35] + latest_cl.apply(
        lambda r: " ★" if r.get("data_quality") == "estimated" else "", axis=1)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Lowest Credit Loss Rate (Best)**")
        top_cl = latest_cl.head(20).copy()
        fig = px.bar(top_cl, x="credit_cost_pct", y="label", orientation="h",
                     color="credit_cost_pct", color_continuous_scale="RdYlGn_r",
                     labels={"credit_cost_pct": "Credit Loss Rate (%)", "label": ""},
                     title="Cleanest Books — Lowest Annual Losses", height=550)
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                          plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                          font=dict(color="white", size=11))
        fig.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Highest Credit Loss Rate (Worst)**")
        bot_cl = latest_cl.tail(20).sort_values("credit_cost_pct", ascending=False).copy()
        fig2 = px.bar(bot_cl, x="credit_cost_pct", y="label", orientation="h",
                      color="credit_cost_pct", color_continuous_scale="Reds",
                      labels={"credit_cost_pct": "Credit Loss Rate (%)", "label": ""},
                      title="Highest Annual Credit Losses", height=550)
        fig2.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white", size=11))
        fig2.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Trend: credit cost over years ─────────────────────────────────────────
    st.subheader("📊 Credit Loss Rate Trend")

    # Pick top companies by latest credit cost (most interesting to watch)
    top_names = latest_cl.sort_values("credit_cost_pct", ascending=False).head(min(14, top_n))["name"]
    cl_trend = cl_data[cl_data["name"].isin(top_names)]

    fig3 = px.line(cl_trend.sort_values("fiscal_year"), x="fiscal_year", y="credit_cost_pct",
                   color="name", markers=True, height=420,
                   labels={"credit_cost_pct": "Credit Loss Rate (%)", "fiscal_year": "FY", "name": ""},
                   title="Annual Credit Loss Rate (%) — Higher-Risk NBFCs")
    fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                       font=dict(color="white"), legend=dict(font=dict(size=9)))
    fig3.add_hline(y=2.0, line_dash="dash", line_color="orange", opacity=0.5,
                   annotation_text="2% threshold", annotation_position="right")
    st.plotly_chart(fig3, use_container_width=True)

    # ── Sector average credit cost ─────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Sector Average Credit Loss Rate**")
        sector_cl = cl_data.groupby(["fiscal_year", "category"])["credit_cost_pct"].mean().reset_index()
        fig4 = px.bar(sector_cl, x="fiscal_year", y="credit_cost_pct", color="category",
                      barmode="group", height=380,
                      labels={"credit_cost_pct": "Avg Credit Loss Rate (%)", "fiscal_year": "FY"},
                      title="Credit Loss Rate by Sector")
        fig4.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white"), xaxis_tickangle=-30)
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        st.markdown("**Credit Loss Rate vs GNPA % (Latest Year)**")
        scatter_df = latest_cl[latest_cl["credit_cost_pct"].notna()].merge(
            filt_df[["name", "latest_gnpa", "disp_assets"]], on="name", how="left"
        ).dropna(subset=["latest_gnpa"])
        scatter_df["size_val"] = (scatter_df["disp_assets"].fillna(5000).clip(upper=300000) / 3000).clip(lower=1)
        fig5 = px.scatter(scatter_df, x="latest_gnpa", y="credit_cost_pct",
                          size="size_val", color="category",
                          hover_name="name",
                          labels={"latest_gnpa": "GNPA %", "credit_cost_pct": "Credit Loss Rate %"},
                          title="Credit Loss Rate vs GNPA — Are losses aligned?",
                          height=380)
        # Diagonal reference line (credit loss should roughly equal GNPA × LGD ~40%)
        import numpy as np
        x_max = scatter_df["latest_gnpa"].max() * 1.1
        fig5.add_trace(go.Scatter(x=[0, x_max], y=[0, x_max * 0.4],
                                  mode="lines", name="Expected (40% LGD)",
                                  line=dict(dash="dash", color="gray", width=1)))
        fig5.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white"))
        st.plotly_chart(fig5, use_container_width=True)

    # ── Heatmap ───────────────────────────────────────────────────────────────
    st.subheader("🗺️ Credit Loss Rate Heatmap")
    pivot_cl = cl_data.pivot_table(index="name", columns="fiscal_year", values="credit_cost_pct")
    pivot_cl["max_cl"] = pivot_cl.max(axis=1)
    pivot_cl = pivot_cl.sort_values("max_cl", ascending=False).drop(columns=["max_cl"]).head(40)
    pivot_cl.index = pivot_cl.index.str[:38]
    fig6 = px.imshow(pivot_cl, color_continuous_scale="RdYlGn_r",
                     aspect="auto", height=750,
                     labels={"color": "Credit Loss %"},
                     title="Annual Credit Loss Rate (%) — All Companies × All Years")
    fig6.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                       font=dict(color="white", size=10))
    st.plotly_chart(fig6, use_container_width=True)

    # ── Improvement / deterioration ────────────────────────────────────────────
    st.subheader("📐 Credit Loss Rate: Improvement vs Deterioration")
    st.caption("Change in credit loss rate from first to latest year with data")

    first_cl = (
        cl_data.sort_values("fiscal_year")
        .groupby("name", as_index=False)
        .first()[["name", "credit_cost_pct"]].rename(columns={"credit_cost_pct": "first_cl"})
    )
    delta_df = latest_cl[["name", "credit_cost_pct", "category"]].merge(first_cl, on="name")
    delta_df["cl_delta"] = delta_df["credit_cost_pct"] - delta_df["first_cl"]
    delta_df = delta_df.dropna(subset=["cl_delta"]).sort_values("cl_delta")

    col_e, col_f = st.columns(2)
    with col_e:
        st.markdown("**Most Improved (Credit Loss Fell)**")
        improved = delta_df[delta_df["cl_delta"] < 0].head(15).copy()
        improved["label"] = improved["name"].str[:35]
        fig7 = px.bar(improved, x="cl_delta", y="label", orientation="h",
                      color="cl_delta", color_continuous_scale="Greens_r",
                      labels={"cl_delta": "Change in Credit Loss Rate (pp)", "label": ""},
                      title="Largest Improvement in Credit Losses", height=420)
        fig7.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white", size=11))
        fig7.update_traces(texttemplate="%{x:.2f}pp", textposition="outside")
        st.plotly_chart(fig7, use_container_width=True)

    with col_f:
        st.markdown("**Most Deteriorated (Credit Loss Rose)**")
        worsened = delta_df[delta_df["cl_delta"] > 0].tail(15).sort_values("cl_delta", ascending=False).copy()
        worsened["label"] = worsened["name"].str[:35]
        fig8 = px.bar(worsened, x="cl_delta", y="label", orientation="h",
                      color="cl_delta", color_continuous_scale="Reds",
                      labels={"cl_delta": "Change in Credit Loss Rate (pp)", "label": ""},
                      title="Largest Deterioration in Credit Losses", height=420)
        fig8.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white", size=11))
        fig8.update_traces(texttemplate="+%{x:.2f}pp", textposition="outside")
        st.plotly_chart(fig8, use_container_width=True)


# ─── TAB 4: TREND ANALYSIS ───────────────────────────────────────────────────
with tab4:
    st.subheader("📈 Multi-Year Trend Analysis")

    top_by_lb = filt_df[filt_df["disp_assets"].notna()].nlargest(min(12, top_n), "disp_assets")

    # AUM trend
    st.markdown("**📦 Loan Book (AUM) Growth**")
    lb_data = fins_df[fins_df["nbfc_id"].isin(top_by_lb["id"]) & fins_df["loan_book"].notna()].merge(
        nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id"
    )
    fig = px.area(lb_data.sort_values("fiscal_year"), x="fiscal_year", y="loan_book",
                  color="name", height=420,
                  labels={"loan_book": "Loan Book (₹ Cr)", "fiscal_year": "FY", "name": ""},
                  title="Loan Book Trend — Top NBFCs")
    fig.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                      font=dict(color="white"), legend=dict(font=dict(size=9)))
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        nii_data = fins_df[fins_df["nbfc_id"].isin(top_by_lb["id"]) & fins_df["nii"].notna()].merge(
            nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id"
        )
        fig2 = px.line(nii_data, x="fiscal_year", y="nii", color="name", height=380,
                       labels={"nii": "NII (₹ Cr)", "fiscal_year": "FY"},
                       title="Net Interest Income Trend")
        fig2.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                           font=dict(color="white"), legend=dict(font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        layer_aum = fins_df.merge(
            nbfc_df[["id", "rbi_layer"]], left_on="nbfc_id", right_on="id"
        ).groupby(["fiscal_year", "rbi_layer"])["total_assets"].sum().reset_index()
        fig3 = px.bar(layer_aum, x="fiscal_year", y="total_assets", color="rbi_layer",
                      height=380, barmode="stack",
                      labels={"total_assets": "Total Assets (₹ Cr)", "fiscal_year": "FY"},
                      title="Industry Assets by RBI Layer")
        fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
        st.plotly_chart(fig3, use_container_width=True)

    # ROA trend
    roa_data = fins_df[fins_df["nbfc_id"].isin(top_by_lb["id"]) & fins_df["roa"].notna()].merge(
        nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id"
    )
    fig4 = px.line(roa_data, x="fiscal_year", y="roa", color="name", height=380,
                   labels={"roa": "ROA (%)", "fiscal_year": "FY"},
                   title="Return on Assets Trend")
    fig4.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                       font=dict(color="white"), legend=dict(font=dict(size=9)))
    fig4.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.4)
    st.plotly_chart(fig4, use_container_width=True)


# ─── TAB 5: DEEP DIVE ────────────────────────────────────────────────────────
with tab5:
    st.subheader("🔍 Company Deep-Dive")

    company_list = sorted(has_fin_df["name"].dropna().unique().tolist())
    sel_company = st.selectbox("Select Company", company_list)

    company_row = has_fin_df[has_fin_df["name"] == sel_company].iloc[0]
    nbfc_id = company_row["id"]
    company_fins = fins_df[fins_df["nbfc_id"] == nbfc_id].sort_values("fiscal_year")
    is_est = company_row.get("data_quality") == "estimated"

    # Header
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown(f"### {sel_company}")
        tag = '<span class="tag-estimated">★ Estimated</span>' if is_est else '<span class="tag-actual">✓ Actual</span>'
        st.markdown(
            f"{tag} &nbsp;| {company_row.get('rbi_layer','—')} Layer "
            f"&nbsp;| {company_row.get('category','—')} "
            f"&nbsp;| {'Listed 🟢' if company_row.get('listed') else 'Unlisted 🔴'}",
            unsafe_allow_html=True)
    with col_h2:
        if is_est:
            st.warning("Data from credit rating reports — not audited accounts.")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    latest_ta = company_fins["total_assets"].dropna().iloc[-1] if len(company_fins["total_assets"].dropna()) else 0
    with k1:
        st.metric("Latest Total Assets", f"₹{latest_ta:,.0f} Cr")
    with k2:
        v = company_row.get("aum_cagr")
        st.metric("AUM CAGR", f"{v:.1f}%" if v else "N/A")
    with k3:
        v = company_row.get("avg_roa")
        st.metric("Avg ROA", f"{v:.2f}%" if v else "N/A")
    with k4:
        v = company_row.get("latest_gnpa")
        st.metric("Latest GNPA", f"{v:.2f}%" if v else "N/A")

    if not company_fins.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            if company_fins["total_assets"].notna().any():
                fig.add_trace(go.Bar(x=company_fins["fiscal_year"], y=company_fins["total_assets"],
                                     name="Total Assets", marker_color="#63b3ed", opacity=0.8))
            if company_fins["loan_book"].notna().any():
                fig.add_trace(go.Bar(x=company_fins["fiscal_year"], y=company_fins["loan_book"],
                                     name="Loan Book", marker_color="#48bb78", opacity=0.8))
            fig.update_layout(title="Assets & Loan Book (₹ Cr)", barmode="group",
                              plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                              font=dict(color="white"), height=320)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure()
            if company_fins["nii"].notna().any():
                fig2.add_trace(go.Bar(x=company_fins["fiscal_year"], y=company_fins["nii"],
                                      name="NII", marker_color="#f6ad55", opacity=0.8))
            if company_fins["pat"].notna().any():
                fig2.add_trace(go.Scatter(x=company_fins["fiscal_year"], y=company_fins["pat"],
                                          name="PAT", mode="lines+markers",
                                          line=dict(color="#e94560", width=2), marker=dict(size=8)))
            fig2.update_layout(title="Revenue (NII) & Profit (₹ Cr)",
                               plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                               font=dict(color="white"), height=320)
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            if company_fins["gnpa_pct"].notna().any():
                gdf = company_fins[company_fins["gnpa_pct"].notna()]
                fig3 = px.line(gdf, x="fiscal_year", y="gnpa_pct", markers=True, height=300,
                               labels={"gnpa_pct": "GNPA %", "fiscal_year": "FY"},
                               title="GNPA % Trend")
                fig3.update_traces(line=dict(color="#e94560", width=2))
                fig3.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("GNPA data not available for this company")

        with col4:
            if company_fins["roa"].notna().any():
                fig4 = go.Figure()
                fig4.add_trace(go.Bar(x=company_fins["fiscal_year"], y=company_fins["roa"],
                                      name="ROA %", marker_color="#9f7aea"))
                if company_fins["roe"].notna().any():
                    fig4.add_trace(go.Scatter(x=company_fins["fiscal_year"], y=company_fins["roe"],
                                              name="ROE %", mode="lines+markers",
                                              line=dict(color="#63b3ed", width=2)))
                fig4.update_layout(title="ROA & ROE (%)", plot_bgcolor="#0f172a",
                                   paper_bgcolor="#0f172a", font=dict(color="white"), height=300)
                st.plotly_chart(fig4, use_container_width=True)

        # Credit losses chart
        if company_fins["credit_cost_pct"].notna().any():
            st.markdown("**📉 Annual Credit Loss Rate (%)**")
            cl_df = company_fins[company_fins["credit_cost_pct"].notna()]
            fig_cl = go.Figure()
            fig_cl.add_trace(go.Bar(x=cl_df["fiscal_year"], y=cl_df["credit_cost_pct"],
                                    name="Credit Loss Rate", marker_color="#fc8181", opacity=0.85))
            fig_cl.add_trace(go.Scatter(x=cl_df["fiscal_year"], y=cl_df["credit_losses"],
                                        name="Credit Losses (₹ Cr)", mode="lines+markers",
                                        yaxis="y2", line=dict(color="#f6ad55", width=2)))
            fig_cl.update_layout(
                title="Credit Loss Rate & Absolute Credit Losses",
                plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                font=dict(color="white"), height=300,
                yaxis=dict(title="Credit Loss Rate (%)", side="left"),
                yaxis2=dict(title="Credit Losses (₹ Cr)", overlaying="y", side="right"),
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_cl, use_container_width=True)

        st.subheader("Financial Data Table")
        display_cols = ["fiscal_year", "loan_book", "total_assets", "nii", "pat",
                        "credit_losses", "credit_cost_pct", "gnpa_pct",
                        "equity_capital", "roa", "roe", "is_estimated"]
        avail_cols = [c for c in display_cols if c in company_fins.columns]
        fmt_df = company_fins[avail_cols].set_index("fiscal_year").T
        st.dataframe(fmt_df.style.format("{:,.1f}", na_rep="—"), use_container_width=True)
    else:
        st.info("No financial data available for selected company.")


# ─── TAB 6: FULL UNIVERSE ────────────────────────────────────────────────────
with tab6:
    st.subheader("🌐 Full NBFC Universe")

    layer_counts = nbfc_df.groupby("rbi_layer").agg(
        total=("id", "count"),
        with_data=("has_financials", "sum"),
    ).reset_index()
    layer_counts.columns = ["Layer", "Total", "With Financial Data"]

    col_pie1, col_pie2 = st.columns(2)
    with col_pie1:
        fig = px.pie(layer_counts, names="Layer", values="Total",
                     title="NBFCs by RBI Layer", height=350,
                     color_discrete_sequence=["#e94560", "#f6ad55", "#63b3ed"])
        fig.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
        st.plotly_chart(fig, use_container_width=True)

    with col_pie2:
        cat_counts = has_fin_df.groupby("category").size().reset_index(name="count").sort_values("count", ascending=False).head(12)
        fig2 = px.bar(cat_counts, x="count", y="category", orientation="h",
                      title="Companies with Data by Sector", height=350,
                      labels={"count": "Count", "category": ""},
                      color="count", color_continuous_scale="Viridis")
        fig2.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                           plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="white"))
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(layer_counts, use_container_width=True)

    st.subheader(f"Top {top_n} NBFCs by Assets")
    top_assets = filt_df.nlargest(top_n, "disp_assets")[
        ["name", "rbi_layer", "category", "listed", "data_quality",
         "disp_assets", "aum_cagr", "avg_roa", "latest_gnpa"]
    ].copy()
    top_assets.columns = ["Name", "Layer", "Sector", "Listed", "Data Quality",
                          "Assets (₹ Cr)", "AUM CAGR %", "Avg ROA %", "GNPA %"]
    top_assets["Assets (₹ Cr)"] = top_assets["Assets (₹ Cr)"].apply(
        lambda x: f"₹{x:,.0f}" if pd.notna(x) else "—")
    st.dataframe(top_assets, use_container_width=True, height=500)


# ─── TAB 7: RAW DATA ─────────────────────────────────────────────────────────
with tab7:
    st.subheader("📋 Raw Data Export")

    search = st.text_input("Search company name", "")

    raw = full_df.copy()
    if "disp_assets" not in raw.columns:
        raw["disp_assets"] = raw["latest_assets"]
    if search:
        raw = raw[raw["name"].str.contains(search, case=False, na=False)]

    display_df = raw[["name", "rbi_layer", "category", "listed", "data_quality",
                       "disp_assets", "aum_cagr", "asset_cagr", "avg_roa", "avg_roe",
                       "latest_gnpa", "avg_gnpa", "latest_fy", "fy_count"]].copy()
    display_df.columns = ["Name", "Layer", "Sector", "Listed", "Data Quality",
                          "Assets (₹ Cr)", "AUM CAGR %", "Asset CAGR %", "Avg ROA %", "Avg ROE %",
                          "Latest GNPA %", "Avg GNPA %", "Latest FY", "FY Count"]

    st.dataframe(display_df, use_container_width=True, height=600)
    csv = display_df.to_csv(index=False)
    st.download_button("⬇️ Download as CSV", csv, "nbfc_data.csv", "text/csv")

    st.subheader("Raw Financials Table")
    fins_export = fins_df.merge(nbfc_df[["id", "name"]], left_on="nbfc_id", right_on="id")
    if search:
        fins_export = fins_export[fins_export["name"].str.contains(search, case=False, na=False)]
    drop_cols = [c for c in ["id_x", "id_y", "nbfc_id"] if c in fins_export.columns]
    st.dataframe(fins_export.drop(columns=drop_cols), use_container_width=True, height=400)
