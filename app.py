"""
NBFC Intelligence Dashboard — India
FY2021–FY2026 (incl. quarterly) | 9,359 NBFCs | 74 with financial data
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from datetime import datetime, timedelta

st.set_page_config(
    page_title="NBFC Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nbfc_full.db")

# ── DESIGN SYSTEM ─────────────────────────────────────────────────────────────
ACCENT   = "#4f46e5"   # indigo-600
GREEN    = "#059669"   # emerald-600
RED      = "#dc2626"   # red-600
AMBER    = "#d97706"   # amber-600
BLUE     = "#2563eb"   # blue-600
MUTED    = "#475569"   # slate-600 (darker than before)
BG_PAGE  = "#ffffff"   # white
BG_CARD  = "#f8fafc"   # slate-50
BORDER   = "#cbd5e1"   # slate-300 (slightly darker border)
TEXT     = "#0f172a"   # slate-900
SUBTEXT  = "#334155"   # slate-700 — much more readable on white

GRID_COLOR = "#e2e8f0"  # slightly visible grid lines

PLOT_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color=TEXT, family="Inter, sans-serif", size=12),
    title_font=dict(size=14, color=TEXT, family="Inter, sans-serif"),
    margin=dict(l=10, r=120, t=48, b=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor=BORDER,
        borderwidth=1,
        font=dict(size=11, color=TEXT),
    ),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=SUBTEXT, size=11)),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=TEXT, size=11)),
)

PALETTE = ["#4f46e5","#059669","#d97706","#dc2626","#2563eb",
           "#7c3aed","#0891b2","#ea580c","#65a30d","#db2777","#0d9488","#9333ea"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {TEXT};
}}

/* ── page background ── */
[data-testid="stAppViewContainer"] {{
    background: {BG_PAGE};
}}
[data-testid="block-container"] {{
    padding-top: 1.8rem;
    max-width: 1400px;
}}

/* ── sidebar ── */
[data-testid="stSidebar"] {{
    background: {BG_CARD};
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {{
    color: {TEXT} !important;
}}

/* ── tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: {BG_CARD};
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    border: 1px solid {BORDER};
    margin-bottom: 20px;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    border-radius: 7px;
    color: {SUBTEXT};
    font-size: 13px;
    font-weight: 500;
    padding: 7px 18px;
    border: none;
    background: transparent;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    background: {ACCENT} !important;
    color: white !important;
}}

/* ── dataframe ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    overflow: hidden;
}}

/* ── metric ── */
[data-testid="metric-container"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px;
}}
/* Force ALL text inside metric cards to be dark and fully opaque */
[data-testid="metric-container"] * {{
    opacity: 1 !important;
    filter: none !important;
}}
[data-testid="metric-container"] label,
[data-testid="metric-container"] label *,
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] [data-testid="stMetricLabel"] * {{
    color: #475569 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricValue"] *,
[data-testid="metric-container"] [data-testid="metric-value"],
[data-testid="metric-container"] [data-testid="metric-value"] * {{
    color: #0f172a !important;
    font-size: 26px !important;
    font-weight: 800 !important;
}}
[data-testid="metric-container"] [data-testid="stMetricDelta"],
[data-testid="metric-container"] [data-testid="stMetricDelta"] *,
[data-testid="metric-container"] [data-testid="metric-delta"],
[data-testid="metric-container"] [data-testid="metric-delta"] * {{
    color: #15803d !important;
    font-size: 12px !important;
    font-weight: 600 !important;
}}

/* ── headers ── */
h1, h2 {{ color: {TEXT} !important; font-weight: 700; }}

/* ── pills ── */
.pill {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
}}
.pill-green  {{ background: #d1fae5; color: #065f46; }}
.pill-amber  {{ background: #fef3c7; color: #92400e; }}
.pill-red    {{ background: #fee2e2; color: #991b1b; }}
.pill-indigo {{ background: #e0e7ff; color: #3730a3; }}
.pill-blue   {{ background: #dbeafe; color: #1e40af; }}

/* ── note banner ── */
.note-banner {{
    background: #fffbeb;
    border: 1px solid #f59e0b;
    border-left: 4px solid {AMBER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    font-weight: 500;
    color: #78350f;
    margin-bottom: 16px;
}}

/* ── section label ── */
.section-label {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #334155;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid {BORDER};
}}

/* ── page title ── */
.page-title {{
    font-size: 30px;
    font-weight: 700;
    color: {TEXT};
    margin: 0;
    letter-spacing: -0.02em;
}}
.page-subtitle {{
    font-size: 13px;
    color: #475569;
    font-weight: 500;
    margin: 4px 0 24px;
}}

/* ── plotly chart container ── */
[data-testid="stPlotlyChart"] {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    overflow: hidden;
    background: white;
    padding: 4px;
}}
</style>
""", unsafe_allow_html=True)


# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all():
    conn = sqlite3.connect(DB_PATH)
    nbfc = pd.read_sql("SELECT * FROM nbfc", conn)
    fins = pd.read_sql("SELECT * FROM financials", conn)
    conn.close()
    nbfc["listed"] = nbfc["listed"].astype(bool)
    nbfc["has_financials"] = nbfc["has_financials"].astype(bool)
    return nbfc, fins


def _fy_sort_key(fy):
    """Sort key: FY2025 → (2025, 0), FY2026-Q1 → (2026, 1), FY2026-Q2 → (2026, 2)."""
    import re
    m = re.match(r'FY(\d{4})(?:-Q(\d))?', str(fy))
    if m:
        return (int(m.group(1)), int(m.group(2)) if m.group(2) else 0)
    return (0, 0)


@st.cache_data(ttl=300)
def compute_metrics(nbfc_df, fins_df):
    rows = []
    for nbfc_id, grp in fins_df.groupby("nbfc_id"):
        grp = grp.copy()
        grp["_sort"] = grp["fiscal_year"].map(_fy_sort_key)
        grp = grp.sort_values("_sort")
        fys = grp["fiscal_year"].tolist()

        # Use only annual (non-quarterly) rows for CAGR & avg ratios
        annual = grp[~grp["fiscal_year"].str.contains("-Q", na=False)]
        annual_fys = annual["fiscal_year"].tolist()

        def _cagr(col, src=annual):
            s = src[src[col].notna()]
            if len(s) < 2: return None
            sv, ev, n = s.iloc[0][col], s.iloc[-1][col], len(s)-1
            if sv and sv > 0 and ev and ev > 0:
                return round(((ev/sv)**(1/n)-1)*100, 1)

        lr = grp[grp["total_assets"].notna()]
        latest = lr.iloc[-1] if len(lr) else None

        # Data range labels for hover tooltips
        fy_range = f"{annual_fys[0]}–{annual_fys[-1]}" if len(annual_fys) >= 2 else (annual_fys[0] if annual_fys else "—")
        latest_fy_label = fys[-1] if fys else "—"

        rows.append({
            "nbfc_id": nbfc_id,
            "aum_cagr":     _cagr("loan_book") or _cagr("total_assets"),
            "asset_cagr":   _cagr("total_assets"),
            "avg_roa":      round(annual["roa"].dropna().mean(), 2)  if annual["roa"].notna().any()  else None,
            "avg_roe":      round(annual["roe"].dropna().mean(), 1)  if annual["roe"].notna().any()  else None,
            "latest_gnpa":  grp[grp["gnpa_pct"].notna()].iloc[-1]["gnpa_pct"] if grp["gnpa_pct"].notna().any() else None,
            "avg_gnpa":     round(grp["gnpa_pct"].dropna().mean(), 2) if grp["gnpa_pct"].notna().any() else None,
            "latest_cl":    grp[grp["credit_cost_pct"].notna()].iloc[-1]["credit_cost_pct"] if grp["credit_cost_pct"].notna().any() else None,
            "fin_latest_assets": latest["total_assets"] if latest is not None else None,
            "latest_pat":   latest["pat"]          if latest is not None else None,
            "latest_fy":    fys[-1] if fys else None,
            "fy_count":     len(fys),
            "fy_range":     fy_range,
            "latest_fy_label": latest_fy_label,
        })
    mdf = pd.DataFrame(rows)
    result = nbfc_df.merge(mdf, left_on="id", right_on="nbfc_id", how="left")
    result["disp_assets"] = result["fin_latest_assets"].combine_first(result["latest_assets"])
    return result


nbfc_df, fins_df = load_all()
full_df  = compute_metrics(nbfc_df, fins_df)
has_df   = full_df[full_df["has_financials"]].copy()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">Filters</p>', unsafe_allow_html=True)

    layer_opts = ["All Layers"] + sorted(nbfc_df["rbi_layer"].dropna().unique())
    sel_layer  = st.selectbox("RBI Layer", layer_opts)

    cat_opts   = ["All Sectors"] + sorted(has_df["category"].dropna().unique())
    sel_cat    = st.selectbox("Sector", cat_opts)

    list_opts  = ["All", "Listed Only", "Unlisted Only"]
    sel_list   = st.selectbox("Listing Status", list_opts)

    top_n      = st.slider("Show top N", 10, 80, 40)
    show_est   = st.checkbox("Include estimated data", True)

    st.markdown("---")
    st.markdown('<p class="section-label">About</p>', unsafe_allow_html=True)
    st.markdown(f"""
<span style="color:#334155;font-size:12px;line-height:1.9;font-weight:500">
🏦 RBI/FIDC registry — 9,359 NBFCs<br>
📈 Screener.in / yfinance — listed companies<br>
🏢 Company IR filings — fintech NBFCs<br>
⭐ CRISIL / ICRA / CARE — unlisted estimates<br>
🗓️ Coverage: FY2021–FY2025 + FY2026 Q1–Q3
</span>
""", unsafe_allow_html=True)

    est_cnt = has_df[has_df["data_quality"] == "estimated"].shape[0] if "data_quality" in has_df.columns else 0
    st.markdown(f"""
<br>
<span style="color:#334155;font-size:12px;font-weight:500">
<b style="color:{TEXT}">{has_df.shape[0]}</b> companies with financials<br>
<b style="color:{TEXT}">{est_cnt}</b> with estimated data ★
</span>
""", unsafe_allow_html=True)


def apply_filters(df):
    if sel_layer != "All Layers":     df = df[df["rbi_layer"] == sel_layer]
    if sel_cat   != "All Sectors":    df = df[df["category"]  == sel_cat]
    if sel_list  == "Listed Only":    df = df[df["listed"]     == True]
    elif sel_list == "Unlisted Only": df = df[df["listed"]     == False]
    if not show_est and "data_quality" in df.columns:
        df = df[df["data_quality"] != "estimated"]
    return df

filt_df = apply_filters(has_df)


# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown('<p class="page-title">NBFC Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">India\'s Non-Banking Financial Companies · FY2021–FY2025 annual + FY2026 Q1–Q3 quarterly · 74 companies · RBI/FIDC, Screener.in, Rating Agencies</p>', unsafe_allow_html=True)

# ── KPI ROW ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total NBFCs", "9,359", "RBI registered")
with k2:
    st.metric("With Financial Data", str(has_df.shape[0]), "FY2021–FY2026")
with k3:
    ta = has_df["disp_assets"].sum() / 1e5
    st.metric("Combined Assets", f"₹{ta:.1f}L Cr", "tracked companies")
with k4:
    cagr = has_df["aum_cagr"].dropna().mean()
    st.metric("Avg AUM CAGR", f"{cagr:.1f}%", "across tracked NBFCs")
with k5:
    gnpa = has_df["latest_gnpa"].dropna().mean()
    st.metric("Avg GNPA", f"{gnpa:.1f}%", "latest available")

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Growth", "Profitability", "Asset Quality",
    "Credit Losses", "Trends", "Deep Dive", "Valuation", "Universe", "Data", "SQL",
])

# helper: consistent chart styling
def style(fig, height=420, legend=True):
    fig.update_layout(**PLOT_LAYOUT, height=height, showlegend=legend)
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)
    return fig

def hbar(df, x, y, title, color_col=None, color_scale="Blues", text_fmt=".1f", period_col=None):
    """Horizontal bar — height auto-scales to number of rows."""
    n = len(df)
    height = max(300, min(n * 26 + 70, 680))  # 26px/row, capped at 680px
    kw = dict(color=x, color_continuous_scale=color_scale)
    hover_data = {period_col: True} if period_col and period_col in df.columns else {}
    fig = px.bar(df, x=x, y=y, orientation="h", title=title, **kw,
                 labels={x: x, y: "", **({"period_col": "Period"} if period_col else {})},
                 hover_data=hover_data if hover_data else None)
    layout = {**PLOT_LAYOUT, "margin": dict(l=10, r=100, t=40, b=10)}
    fig.update_layout(**layout, height=height, showlegend=False, coloraxis_showscale=False)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=11, color=TEXT))
    fig.update_xaxes(tickfont=dict(size=10, color=SUBTEXT))
    fig.update_traces(
        texttemplate=f"%{{x:{text_fmt}}}",
        textposition="outside",
        textfont=dict(size=11, color="#1e293b"),
        cliponaxis=False,
    )
    return fig


# ═══ TAB 1: GROWTH ═══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-label">AUM Growth Rankings — FY2024 → FY2025</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">★ Estimated data for unlisted companies — sourced from CRISIL/ICRA/CARE rating rationales, not audited accounts.</div>', unsafe_allow_html=True)

    # Compute FY2024→FY2025 YoY growth from fins_df
    fy24_lb = fins_df[fins_df["fiscal_year"]=="FY2024"][["nbfc_id","loan_book","total_assets"]].rename(
        columns={"loan_book":"lb24","total_assets":"ta24"})
    fy25_lb = fins_df[fins_df["fiscal_year"]=="FY2025"][["nbfc_id","loan_book","total_assets"]].rename(
        columns={"loan_book":"lb25","total_assets":"ta25"})
    growth_raw = fy24_lb.merge(fy25_lb, on="nbfc_id")
    # Use loan_book if available, fall back to total_assets
    growth_raw["base24"] = growth_raw["lb24"].combine_first(growth_raw["ta24"])
    growth_raw["base25"] = growth_raw["lb25"].combine_first(growth_raw["ta25"])
    growth_raw = growth_raw[(growth_raw["base24"].notna()) & (growth_raw["base25"].notna()) & (growth_raw["base24"] > 0)]
    growth_raw["yoy_growth"] = (growth_raw["base25"] / growth_raw["base24"] - 1) * 100
    growth_raw["period"] = "FY2024→FY2025"

    df_g = filt_df.merge(growth_raw[["nbfc_id","yoy_growth","period"]], left_on="id", right_on="nbfc_id", how="inner")
    df_g = df_g.sort_values("yoy_growth", ascending=False)
    df_g["label"] = df_g["name"].str[:20] + df_g.apply(lambda r: " ★" if r.get("data_quality")=="estimated" else "", axis=1)

    c1, c2 = st.columns(2)
    with c1:
        top = df_g.head(20)
        fig = hbar(top, "yoy_growth", "label", "Fastest Growing (FY25 vs FY24)", color_scale="Greens", text_fmt=".1f", period_col="period")
        fig.update_traces(marker_color=GREEN, opacity=0.85)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        bot = df_g.tail(20).sort_values("yoy_growth")
        fig2 = hbar(bot, "yoy_growth", "label", "Slowest Growing / Declining (FY25 vs FY24)", color_scale="Reds", text_fmt=".1f", period_col="period")
        fig2.update_traces(marker_color=RED, opacity=0.85)
        st.plotly_chart(fig2, use_container_width=True)

    # Bubble — FY2025 growth vs FY2025 ROA
    st.markdown('<p class="section-label" style="margin-top:8px">Growth vs Profitability (FY2025)</p>', unsafe_allow_html=True)
    fy25_roa = fins_df[fins_df["fiscal_year"]=="FY2025"][["nbfc_id","roa"]].rename(columns={"roa":"fy25_roa"})
    bub = df_g.merge(fy25_roa, left_on="id", right_on="nbfc_id", how="left")
    bub = bub[bub["fy25_roa"].notna() & bub["disp_assets"].notna()]
    bub["sz"] = (bub["disp_assets"].clip(upper=400000)/800).clip(lower=3)
    bub["label"] = bub["name"].str[:20]
    fig3 = px.scatter(bub.head(top_n), x="yoy_growth", y="fy25_roa", size="sz",
                      color="category", color_discrete_sequence=PALETTE,
                      hover_name="label",
                      hover_data={"yoy_growth":":.1f","fy25_roa":":.2f","sz":False,"period":True},
                      labels={"yoy_growth":"AUM Growth FY25 vs FY24 (%)","fy25_roa":"ROA FY2025 (%)","category":"Sector","period":"Period"})
    fig3.add_vline(x=bub["yoy_growth"].median(), line_dash="dot", line_color=BORDER, line_width=1)
    fig3.add_hline(y=0, line_dash="dot", line_color=RED, line_width=1, opacity=0.4)
    fig3.add_annotation(x=bub["yoy_growth"].median()+0.5, y=bub["fy25_roa"].max()*0.95,
                        text="Median growth", showarrow=False, font=dict(size=10, color=MUTED))
    style(fig3, height=460)
    st.plotly_chart(fig3, use_container_width=True)


# ═══ TAB 2: PROFITABILITY ════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-label">Profitability — ROA & ROE (FY2025)</p>', unsafe_allow_html=True)

    # Get FY2025 actual roa/roe values
    fy25_prof = fins_df[fins_df["fiscal_year"]=="FY2025"][["nbfc_id","roa","roe","pat"]].copy()
    fy25_prof["period"] = "FY2025"
    prof_df = filt_df.merge(fy25_prof, left_on="id", right_on="nbfc_id", how="inner")

    c1, c2 = st.columns(2)
    with c1:
        df_roa = prof_df[prof_df["roa"].notna()].sort_values("roa", ascending=False).head(20).copy()
        df_roa["label"] = df_roa["name"].str[:20]
        fig = hbar(df_roa, "roa", "label", "Top 20 by Return on Assets — FY2025",
                   color_scale="Greens", text_fmt=".2f", period_col="period")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df_roe = prof_df[prof_df["roe"].notna()].sort_values("roe", ascending=False).head(20).copy()
        df_roe["label"] = df_roe["name"].str[:20]
        fig2 = hbar(df_roe, "roe", "label", "Top 20 by Return on Equity — FY2025",
                    color_scale="Blues", text_fmt=".1f", period_col="period")
        st.plotly_chart(fig2, use_container_width=True)

    # Sector bar — FY2025 only
    st.markdown('<p class="section-label" style="margin-top:8px">By Sector — FY2025</p>', unsafe_allow_html=True)
    sec = prof_df[prof_df["roa"].notna()].groupby("category").agg(
        avg_roa=("roa","mean"), avg_roe=("roe","mean"), n=("name","count")
    ).reset_index().sort_values("avg_roa", ascending=False)
    fig3 = px.bar(sec, x="category", y=["avg_roa","avg_roe"], barmode="group",
                  color_discrete_map={"avg_roa": GREEN, "avg_roe": ACCENT},
                  labels={"value":"Return (%)","category":"Sector","variable":"Metric"})
    fig3.update_layout(**PLOT_LAYOUT, height=360, xaxis_tickangle=-30)
    st.plotly_chart(fig3, use_container_width=True)

    # PAT trend
    st.markdown('<p class="section-label" style="margin-top:8px">PAT Trend — Top Companies</p>', unsafe_allow_html=True)
    top_pat = filt_df[filt_df["latest_pat"].notna()].nlargest(min(10,top_n), "latest_pat")
    pat_data = fins_df[fins_df["nbfc_id"].isin(top_pat["id"])].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    pat_data = pat_data.copy(); pat_data["_s"] = pat_data["fiscal_year"].map(_fy_sort_key); pat_data = pat_data.sort_values("_s").drop(columns=["_s"])
    fig4 = px.line(pat_data, x="fiscal_year", y="pat", color="name",
                   color_discrete_sequence=PALETTE,
                   labels={"pat":"Net Profit (₹ Cr)","fiscal_year":"","name":""})
    fig4.update_traces(line_width=2)
    style(fig4, height=380)
    st.plotly_chart(fig4, use_container_width=True)


# ═══ TAB 3: ASSET QUALITY ════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-label">Asset Quality — GNPA % (FY2025)</p>', unsafe_allow_html=True)

    # Use FY2025 GNPA values specifically
    fy25_gnpa = fins_df[fins_df["fiscal_year"]=="FY2025"][["nbfc_id","gnpa_pct"]].rename(columns={"gnpa_pct":"fy25_gnpa"})
    fy25_gnpa["period"] = "FY2025"
    aq_df = filt_df.merge(fy25_gnpa, left_on="id", right_on="nbfc_id", how="inner")
    aq_df = aq_df[aq_df["fy25_gnpa"].notna()].sort_values("fy25_gnpa")
    aq_df["label"] = aq_df["name"].str[:20]

    c1, c2 = st.columns(2)
    with c1:
        top20 = aq_df.head(20)
        fig = hbar(top20, "fy25_gnpa", "label", "Cleanest Loan Books — Lowest GNPA (FY2025)",
                   color_scale="Greens_r", text_fmt=".2f", period_col="period")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        bot20 = aq_df.tail(20).sort_values("fy25_gnpa", ascending=False)
        fig2 = hbar(bot20, "fy25_gnpa", "label", "Highest NPA Stress (FY2025)",
                    color_scale="Reds", text_fmt=".2f", period_col="period")
        st.plotly_chart(fig2, use_container_width=True)

    # Sector bar — FY2025 GNPA by sector
    st.markdown('<p class="section-label" style="margin-top:8px">GNPA by Sector — FY2025</p>', unsafe_allow_html=True)
    sec_fy25 = aq_df.groupby("category")["fy25_gnpa"].mean().reset_index().sort_values("fy25_gnpa", ascending=False)
    fig_sec = px.bar(sec_fy25, x="category", y="fy25_gnpa", color="fy25_gnpa",
                     color_continuous_scale="RdYlGn_r",
                     labels={"fy25_gnpa":"Avg GNPA % (FY2025)","category":"Sector"})
    fig_sec.update_layout(**PLOT_LAYOUT, height=340, xaxis_tickangle=-30, coloraxis_showscale=False)
    st.plotly_chart(fig_sec, use_container_width=True)

    # Sector trend (multi-year context)
    st.markdown('<p class="section-label" style="margin-top:8px">GNPA Trend by Sector (Historical)</p>', unsafe_allow_html=True)
    gd = fins_df[fins_df["gnpa_pct"].notna()].merge(nbfc_df[["id","category"]], left_on="nbfc_id", right_on="id")
    gd = gd[gd["category"].isin(filt_df["category"].unique())]
    sec_g = gd.groupby(["fiscal_year","category"])["gnpa_pct"].mean().reset_index()
    fig3 = px.line(sec_g, x="fiscal_year", y="gnpa_pct", color="category",
                   color_discrete_sequence=PALETTE, markers=True,
                   labels={"gnpa_pct":"Avg GNPA %","fiscal_year":"","category":"Sector"})
    fig3.update_traces(line_width=2)
    style(fig3, height=360)
    st.plotly_chart(fig3, use_container_width=True)

    # Heatmap
    st.markdown('<p class="section-label" style="margin-top:8px">GNPA Heatmap</p>', unsafe_allow_html=True)
    piv = fins_df[fins_df["gnpa_pct"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    piv = piv.pivot_table(index="name", columns="fiscal_year", values="gnpa_pct")
    piv["_max"] = piv.max(axis=1)
    piv = piv.sort_values("_max", ascending=False).drop(columns=["_max"]).head(35)
    piv.index = piv.index.str[:20]
    fig4 = px.imshow(piv, color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels={"color":"GNPA %"})
    fig4.update_layout(**PLOT_LAYOUT, height=560, coloraxis_colorbar=dict(len=0.5))
    st.plotly_chart(fig4, use_container_width=True)


# ═══ TAB 4: CREDIT LOSSES ════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-label">Annualized Credit Loss Rate = Credit Losses / Loan Book</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">Credit losses = net provisions + write-offs − recoveries. Measures actual P&L cost of defaults — distinct from GNPA% (balance sheet stock).</div>', unsafe_allow_html=True)

    cl_raw = fins_df[fins_df["credit_cost_pct"].notna()].merge(
        nbfc_df[["id","name","category","data_quality"]], left_on="nbfc_id", right_on="id")
    cl_raw = cl_raw[cl_raw["name"].isin(filt_df["name"])]

    # Use FY2025 specifically; fall back to latest only for companies missing FY2025
    fy25_cl = cl_raw[cl_raw["fiscal_year"]=="FY2025"].copy()
    missing_fy25 = set(cl_raw["name"].unique()) - set(fy25_cl["name"].unique())
    fallback_cl = cl_raw[cl_raw["name"].isin(missing_fy25)].sort_values("fiscal_year").groupby("name", as_index=False).last()
    latest_cl = pd.concat([fy25_cl, fallback_cl], ignore_index=True)
    latest_cl["label"] = latest_cl["name"].str[:20] + latest_cl.apply(
        lambda r: " ★" if r.get("data_quality")=="estimated" else "", axis=1)
    latest_cl = latest_cl.sort_values("credit_cost_pct")

    c1, c2 = st.columns(2)
    with c1:
        fig = hbar(latest_cl.head(20), "credit_cost_pct", "label",
                   "Lowest Credit Loss Rate — FY2025", color_scale="Greens_r", text_fmt=".2f", period_col="fiscal_year")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = hbar(latest_cl.tail(20).sort_values("credit_cost_pct", ascending=False),
                    "credit_cost_pct", "label", "Highest Credit Loss Rate — FY2025",
                    color_scale="Reds", text_fmt=".2f", period_col="fiscal_year")
        st.plotly_chart(fig2, use_container_width=True)

    # Trend for high-risk names
    st.markdown('<p class="section-label" style="margin-top:8px">Credit Loss Rate Trend</p>', unsafe_allow_html=True)
    top_names = latest_cl.sort_values("credit_cost_pct", ascending=False).head(min(12,top_n))["name"]
    cl_trend  = cl_raw[cl_raw["name"].isin(top_names)]
    fig3 = px.line(cl_trend.sort_values("fiscal_year"), x="fiscal_year", y="credit_cost_pct",
                   color="name", color_discrete_sequence=PALETTE, markers=True,
                   labels={"credit_cost_pct":"Credit Loss Rate (%)","fiscal_year":"","name":""})
    fig3.add_hline(y=2, line_dash="dot", line_color=AMBER, line_width=1, opacity=0.6,
                   annotation_text="2% threshold", annotation_font_color=AMBER)
    fig3.update_traces(line_width=2)
    style(fig3, height=380)
    st.plotly_chart(fig3, use_container_width=True)

    # Credit loss vs GNPA scatter + improvement/deterioration
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<p class="section-label">Credit Loss Rate vs GNPA %</p>', unsafe_allow_html=True)
        sc = latest_cl[latest_cl["credit_cost_pct"].notna()].merge(
            filt_df[["name","latest_gnpa","disp_assets"]], on="name", how="left").dropna(subset=["latest_gnpa"])
        sc["sz"] = (sc["disp_assets"].fillna(5000).clip(upper=300000)/3000).clip(lower=1)
        fig4 = px.scatter(sc, x="latest_gnpa", y="credit_cost_pct", size="sz",
                          color="category", color_discrete_sequence=PALETTE,
                          hover_name="name",
                          labels={"latest_gnpa":"GNPA %","credit_cost_pct":"Credit Loss Rate %","category":"Sector"})
        x_max = sc["latest_gnpa"].max()*1.1
        fig4.add_trace(go.Scatter(x=[0,x_max], y=[0,x_max*0.4], mode="lines",
                                  name="40% LGD ref", line=dict(dash="dash",color=MUTED,width=1)))
        style(fig4, height=360)
        st.plotly_chart(fig4, use_container_width=True)

    with c4:
        st.markdown('<p class="section-label">Change in Credit Loss Rate</p>', unsafe_allow_html=True)
        first_cl = cl_raw.sort_values("fiscal_year").groupby("name",as_index=False).first()[["name","credit_cost_pct"]].rename(columns={"credit_cost_pct":"first_cl"})
        delta = latest_cl[["name","credit_cost_pct","category"]].merge(first_cl, on="name")
        delta["delta"] = delta["credit_cost_pct"] - delta["first_cl"]
        delta = delta.dropna(subset=["delta"]).sort_values("delta")
        delta["color"] = delta["delta"].apply(lambda x: GREEN if x < 0 else RED)
        delta["label2"] = delta["name"].str[:20]
        fig5 = go.Figure(go.Bar(
            x=delta["delta"], y=delta["label2"], orientation="h",
            marker_color=delta["color"],
            text=delta["delta"].apply(lambda x: f"{x:+.2f}pp"),
            textposition="outside", textfont=dict(size=10, color=SUBTEXT),
        ))
        fig5.update_layout(**{**PLOT_LAYOUT, "yaxis": dict(autorange="reversed", gridcolor=BORDER)}, height=360)
        fig5.add_vline(x=0, line_color=BORDER, line_width=1)
        st.plotly_chart(fig5, use_container_width=True)

    # Heatmap
    st.markdown('<p class="section-label" style="margin-top:8px">Credit Loss Rate Heatmap</p>', unsafe_allow_html=True)
    piv_cl = cl_raw.pivot_table(index="name", columns="fiscal_year", values="credit_cost_pct")
    piv_cl["_max"] = piv_cl.max(axis=1)
    piv_cl = piv_cl.sort_values("_max", ascending=False).drop(columns=["_max"]).head(40)
    piv_cl.index = piv_cl.index.str[:20]
    fig6 = px.imshow(piv_cl, color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels={"color":"Credit Loss %"})
    fig6.update_layout(**PLOT_LAYOUT, height=600, coloraxis_colorbar=dict(len=0.5))
    st.plotly_chart(fig6, use_container_width=True)


# ═══ TAB 5: TRENDS ═══════════════════════════════════════════════════════════
with tab5:
    st.markdown('<p class="section-label">Multi-Year Trends</p>', unsafe_allow_html=True)

    top_lb = filt_df[filt_df["disp_assets"].notna()].nlargest(min(10,top_n), "disp_assets")

    # Loan book area
    lb_d = fins_df[fins_df["nbfc_id"].isin(top_lb["id"]) & fins_df["loan_book"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    lb_d = lb_d.copy(); lb_d["_s"] = lb_d["fiscal_year"].map(_fy_sort_key); lb_d = lb_d.sort_values("_s").drop(columns=["_s"])
    fig = px.area(lb_d, x="fiscal_year", y="loan_book", color="name",
                  color_discrete_sequence=PALETTE,
                  labels={"loan_book":"Loan Book (₹ Cr)","fiscal_year":"","name":""})
    fig.update_traces(line_width=1.5)
    style(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        nii_d = fins_df[fins_df["nbfc_id"].isin(top_lb["id"]) & fins_df["nii"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
        nii_d = nii_d.copy(); nii_d["_s"] = nii_d["fiscal_year"].map(_fy_sort_key); nii_d = nii_d.sort_values("_s").drop(columns=["_s"])
        fig2 = px.line(nii_d, x="fiscal_year", y="nii", color="name",
                       color_discrete_sequence=PALETTE,
                       labels={"nii":"NII (₹ Cr)","fiscal_year":"","name":""}, title="Net Interest Income")
        fig2.update_traces(line_width=2)
        style(fig2, height=340)
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        lay_d = fins_df.merge(nbfc_df[["id","rbi_layer"]], left_on="nbfc_id", right_on="id"
                ).groupby(["fiscal_year","rbi_layer"])["total_assets"].sum().reset_index()
        fig3 = px.bar(lay_d, x="fiscal_year", y="total_assets", color="rbi_layer",
                      barmode="stack", color_discrete_sequence=[ACCENT, GREEN, AMBER],
                      labels={"total_assets":"Total Assets (₹ Cr)","fiscal_year":"","rbi_layer":"Layer"},
                      title="Industry Assets by RBI Layer")
        style(fig3, height=340)
        st.plotly_chart(fig3, use_container_width=True)

    roa_d = fins_df[fins_df["nbfc_id"].isin(top_lb["id"]) & fins_df["roa"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    roa_d = roa_d.copy(); roa_d["_s"] = roa_d["fiscal_year"].map(_fy_sort_key); roa_d = roa_d.sort_values("_s").drop(columns=["_s"])
    fig4 = px.line(roa_d, x="fiscal_year", y="roa", color="name",
                   color_discrete_sequence=PALETTE,
                   labels={"roa":"ROA (%)","fiscal_year":"","name":""}, title="Return on Assets Trend")
    fig4.add_hline(y=0, line_dash="dot", line_color=RED, line_width=1, opacity=0.4)
    fig4.update_traces(line_width=2)
    style(fig4, height=340)
    st.plotly_chart(fig4, use_container_width=True)


# ═══ TAB 6: DEEP DIVE ════════════════════════════════════════════════════════
with tab6:
    st.markdown('<p class="section-label">Company Deep-Dive</p>', unsafe_allow_html=True)

    company_list = sorted(has_df["name"].dropna().unique())
    sel_co = st.selectbox("Select company", company_list, label_visibility="collapsed")

    crow = has_df[has_df["name"] == sel_co].iloc[0]
    cid  = crow["id"]
    cfins = fins_df[fins_df["nbfc_id"] == cid].copy()
    cfins["_s"] = cfins["fiscal_year"].map(_fy_sort_key)
    cfins = cfins.sort_values("_s").drop(columns=["_s"])
    has_quarterly = cfins["fiscal_year"].str.contains("-Q", na=False).any()
    is_est = crow.get("data_quality") == "estimated"

    # Company header
    layer_pill = {"Upper": "pill-indigo", "Middle": "pill-blue", "Base": "pill-amber"}.get(crow.get("rbi_layer",""), "pill-blue")
    est_pill   = "pill-amber" if is_est else "pill-green"
    est_label  = "★ Estimated" if is_est else "✓ Audited"
    list_pill  = "pill-green" if crow.get("listed") else "pill-red"
    list_label = "Listed" if crow.get("listed") else "Unlisted"

    st.markdown(f"""
    <div style="margin-bottom:16px">
        <p style="font-size:22px;font-weight:700;color:{TEXT};margin:0;letter-spacing:-0.01em">{sel_co}</p>
        <p style="margin:6px 0 0">
            <span class="pill {layer_pill}">{crow.get('rbi_layer','—')} Layer</span>&nbsp;
            <span class="pill {est_pill}">{est_label}</span>&nbsp;
            <span class="pill {list_pill}">{list_label}</span>&nbsp;
            <span class="pill pill-indigo">{crow.get('category','—')}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

    if is_est:
        st.markdown(f'<div class="note-banner">Data sourced from credit rating agency rationales and investor presentations — not audited financial statements.</div>', unsafe_allow_html=True)
    if has_quarterly:
        st.markdown(f'<div class="note-banner">Quarterly entries (FY2026-Q1 to Q3) show as-reported figures; PAT and ROA are not annualized. Source: company investor relations disclosures.</div>', unsafe_allow_html=True)

    # KPIs
    m1, m2, m3, m4, m5 = st.columns(5)
    latest_ta = cfins["total_assets"].dropna().iloc[-1] if cfins["total_assets"].notna().any() else 0
    with m1: st.metric("Total Assets", f"₹{latest_ta:,.0f} Cr")
    with m2: st.metric("AUM CAGR", f"{crow.get('aum_cagr'):.1f}%" if crow.get("aum_cagr") else "—")
    with m3: st.metric("Avg ROA", f"{crow.get('avg_roa'):.2f}%" if crow.get("avg_roa") else "—")
    with m4: st.metric("Avg ROE", f"{crow.get('avg_roe'):.1f}%" if crow.get("avg_roe") else "—")
    with m5: st.metric("Latest GNPA", f"{crow.get('latest_gnpa'):.2f}%" if crow.get("latest_gnpa") else "—")

    st.markdown("<br>", unsafe_allow_html=True)

    if not cfins.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            if cfins["total_assets"].notna().any():
                fig.add_bar(x=cfins["fiscal_year"], y=cfins["total_assets"], name="Total Assets", marker_color=ACCENT, opacity=0.7)
            if cfins["loan_book"].notna().any():
                fig.add_bar(x=cfins["fiscal_year"], y=cfins["loan_book"], name="Loan Book", marker_color=GREEN, opacity=0.85)
            fig.update_layout(**PLOT_LAYOUT, barmode="group", title="Assets & Loan Book (₹ Cr)", height=300)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure()
            if cfins["nii"].notna().any():
                fig2.add_bar(x=cfins["fiscal_year"], y=cfins["nii"], name="NII", marker_color=AMBER, opacity=0.8)
            if cfins["pat"].notna().any():
                fig2.add_scatter(x=cfins["fiscal_year"], y=cfins["pat"], name="PAT",
                                 mode="lines+markers", line=dict(color=RED, width=2), marker=dict(size=7))
            fig2.update_layout(**PLOT_LAYOUT, title="Revenue & Profit (₹ Cr)", height=300)
            st.plotly_chart(fig2, use_container_width=True)

        c3, c4, c5 = st.columns(3)
        with c3:
            if cfins["gnpa_pct"].notna().any():
                gdf = cfins[cfins["gnpa_pct"].notna()]
                fig3 = px.area(gdf, x="fiscal_year", y="gnpa_pct", markers=True,
                               labels={"gnpa_pct":"GNPA %","fiscal_year":""}, title="GNPA %")
                fig3.update_traces(line_color=RED, fillcolor=f"rgba(239,68,68,0.15)")
                style(fig3, height=280, legend=False)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No GNPA data")

        with c4:
            if cfins["roa"].notna().any():
                fig4 = go.Figure()
                fig4.add_bar(x=cfins["fiscal_year"], y=cfins["roa"], name="ROA %", marker_color=ACCENT, opacity=0.8)
                if cfins["roe"].notna().any():
                    fig4.add_scatter(x=cfins["fiscal_year"], y=cfins["roe"], name="ROE %",
                                     mode="lines+markers", line=dict(color=BLUE, width=2))
                fig4.update_layout(**PLOT_LAYOUT, title="ROA & ROE (%)", height=280)
                st.plotly_chart(fig4, use_container_width=True)

        with c5:
            if cfins["credit_cost_pct"].notna().any():
                cdf = cfins[cfins["credit_cost_pct"].notna()]
                fig5 = go.Figure()
                fig5.add_bar(x=cdf["fiscal_year"], y=cdf["credit_cost_pct"], name="Loss Rate %",
                             marker_color=AMBER, opacity=0.85)
                fig5.update_layout(**PLOT_LAYOUT, title="Credit Loss Rate (%)", height=280)
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("No credit loss data")

        # Data table
        st.markdown('<p class="section-label" style="margin-top:8px">Financial Summary Table</p>', unsafe_allow_html=True)
        cols = ["fiscal_year","loan_book","total_assets","nii","pat","credit_losses","credit_cost_pct","gnpa_pct","equity_capital","roa","roe"]
        disp = cfins[[c for c in cols if c in cfins.columns]].set_index("fiscal_year").T
        disp.index = ["Loan Book","Total Assets","NII","PAT","Credit Losses","Credit Loss %","GNPA %","Equity","ROA %","ROE %"][:len(disp)]
        st.dataframe(disp.style.format("{:,.1f}", na_rep="—"), use_container_width=True)


# ═══ TAB 7: VALUATION ════════════════════════════════════════════════════════
# NSE ticker map — listed NBFCs with financials
TICKER_MAP = {
    "Bajaj Finance Ltd.":                                   "BAJFINANCE.NS",
    "Shriram Finance Limited":                              "SHRIRAMFIN.NS",
    "Cholamandalam Investment and Finance Company Limited": "CHOLAFIN.NS",
    "Muthoot Finance Limited":                              "MUTHOOTFIN.NS",
    "L&T Finance Limited":                                  "LTF.NS",
    "Mahindra & Mahindra Financial Services Ltd":           "M&MFIN.NS",
    "Power Finance Corporation Ltd.":                       "PFC.NS",
    "REC Limited":                                          "RECLTD.NS",
    "Indian Railway Finance Corporation Ltd":               "IRFC.NS",
    "Indian Renewable Energy Development Agency Limited":   "IREDA.NS",
    "LIC Housing Finance Limited":                          "LICHSGFIN.NS",
    "PNB Housing Finance Limited":                          "PNBHOUSING.NS",
    "Bajaj Housing Finance Limited":                        "BAJAJHFL.NS",
    "Can Fin Homes Limited":                                "CANFINHOME.NS",
    "Aavas Financiers Limited":                             "AAVAS.NS",
    "Aptus Value Housing Finance India Limited":            "APTUS.NS",
    "Repco Home Finance Limited":                           "REPCOHOME.NS",
    "Home First Finance Company India Limited":             "HOMEFIRST.NS",
    "India Shelter Finance Corporation Limited":            "INDIASHLTR.NS",
    "GIC Housing Finance Limited":                          "GICHSGFIN.NS",
    "Sundaram Finance Limited":                             "SUNDARMFIN.NS",
    "SBI Cards and Payment Services Limited":               "SBICARD.NS",
    "Poonawalla Fincorp Limited":                           "POONAWALLA.NS",
    "IIFL Finance Limited":                                 "IIFL.NS",
    "Indostar Capital Finance Limited":                     "INDOSTAR.NS",
    "JM Financial Limited":                                 "JMFINANCIL.NS",
    "Edelweiss Financial Services Limited":                 "EDELWEISS.NS",
    "Fedbank Financial Services Limited":                   "FEDFINA.NS",
    "Northern Arc Capital Limited":                         "NORTHARC.NS",
    "SK Finance Limited":                                   "SKFIN.NS",
    "SBFC Finance Limited":                                 "SBFC.NS",
    "MAS Financial Services Limited":                       "MASFIN.NS",
    "Five Star Business Finance Limited":                   "FIVESTAR.NS",
    "Ugro Capital Limited":                                 "UGROCAP.NS",
    "Paisalo Digital Limited":                              "PAISALO.NS",
    "Arman Financial Services Limited":                     "ARMANFIN.NS",
    "Manappuram Finance Limited":                           "MANAPPURAM.NS",
    "Creditaccess Grameen Limited":                         "CREDITACC.NS",
    "Spandana Sphoorty Financial Limited":                  "SPANDANA.NS",
    "Fusion Micro Finance Limited":                         "FUSION.NS",
    "Muthoot Microfin Ltd":                                 "MUTHOOTMF.NS",
    "Satin Creditcare Network Limited":                     "SATIN.NS",
    "IFCI Limited":                                         "IFCI.NS",
    "Sammaan Capital Limited":                              "SAMMAANCAP.NS",
    "Jio Financial Services Limited":                       "JIOFIN.NS",
    "Aditya Birla Capital Limited":                         "ABCAPITAL.NS",
    "360 ONE Prime Limited":                                "360ONE.NS",
}

@st.cache_data(ttl=3600)
def fetch_valuation_data():
    import yfinance as yf
    rows = []
    end = datetime.today()
    start = end - timedelta(days=370)
    all_tickers = list(TICKER_MAP.values())
    # Batch download price history for all tickers at once (faster, more reliable)
    try:
        hist_all = yf.download(all_tickers, start=start.strftime("%Y-%m-%d"),
                               end=end.strftime("%Y-%m-%d"), interval="1mo",
                               auto_adjust=True, progress=False)["Close"]
    except Exception:
        hist_all = pd.DataFrame()

    for name, ticker in TICKER_MAP.items():
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            pe     = getattr(info, "pe_ratio", None)
            pb     = getattr(info, "price_to_book", None)
            mktcap = getattr(info, "market_cap", None)
            price  = getattr(info, "last_price", None)
            # Fallback to .info for PE/PB if fast_info missing
            if pe is None or pb is None:
                full = t.info
                pe = pe or full.get("trailingPE")
                pb = pb or full.get("priceToBook")
                mktcap = mktcap or full.get("marketCap")
                price  = price or full.get("currentPrice") or full.get("regularMarketPrice")
            # 12M price change from batch download
            price_chg = None
            if not hist_all.empty and ticker in hist_all.columns:
                col = hist_all[ticker].dropna()
                if len(col) >= 2 and price:
                    price_chg = round((price / col.iloc[0] - 1) * 100, 1)
            elif not hist_all.empty and len(hist_all.columns) == 1:
                # single ticker fallback
                col = hist_all.iloc[:, 0].dropna()
                if len(col) >= 2 and price:
                    price_chg = round((price / col.iloc[0] - 1) * 100, 1)
            rows.append({
                "name":      name,
                "ticker":    ticker.replace(".NS", ""),
                "pe_ttm":    round(float(pe), 1)       if pe and float(pe) > 0  else None,
                "pb":        round(float(pb), 2)       if pb and float(pb) > 0  else None,
                "mktcap_cr": round(float(mktcap)/1e7)  if mktcap               else None,
                "price":     round(float(price), 1)    if price                 else None,
                "price_chg": price_chg,
            })
        except Exception:
            rows.append({"name": name, "ticker": ticker.replace(".NS", ""),
                         "pe_ttm": None, "pb": None, "mktcap_cr": None,
                         "price": None, "price_chg": None})
    return pd.DataFrame(rows)

with tab7:
    st.markdown('<p class="section-label">Valuation Metrics — Listed NBFCs</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">Live data via NSE. P/E is trailing twelve months (TTM). Price change is vs ~12 months ago. Refreshes every hour.</div>', unsafe_allow_html=True)

    with st.spinner("Fetching live market data…"):
        vdf = fetch_valuation_data()

    vdf_clean = vdf.dropna(subset=["pe_ttm","pb","price_chg"], how="all").copy()
    n_loaded = vdf_clean[vdf_clean["price"].notna()].shape[0]
    if n_loaded == 0:
        st.error("Could not fetch market data. Please try refreshing the page in a few minutes.")
        st.stop()
    st.caption(f"Loaded data for {n_loaded} of {len(TICKER_MAP)} listed NBFCs.")

    # ── KPI row ──
    v1, v2, v3 = st.columns(3)
    with v1:
        med_pe = vdf_clean["pe_ttm"].dropna().median()
        st.metric("Median P/E (TTM)", f"{med_pe:.1f}x")
    with v2:
        med_pb = vdf_clean["pb"].dropna().median()
        st.metric("Median P/B", f"{med_pb:.2f}x")
    with v3:
        med_chg = vdf_clean["price_chg"].dropna().median()
        st.metric("Median 12M Price Chg", f"{med_chg:+.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    live_date = datetime.today().strftime("%b %d, %Y")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p class="section-label">P/E Ratio (TTM)</p>', unsafe_allow_html=True)
        pe_df = vdf_clean[vdf_clean["pe_ttm"].notna()].sort_values("pe_ttm", ascending=False).copy()
        pe_df["label"] = pe_df["name"].str[:20]
        pe_df["as_of"] = live_date
        fig = hbar(pe_df, "pe_ttm", "label", "P/E Ratio (TTM) — highest to lowest", color_scale="Blues", text_fmt=".1f", period_col="as_of")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown('<p class="section-label">Price-to-Book (P/B)</p>', unsafe_allow_html=True)
        pb_df = vdf_clean[vdf_clean["pb"].notna()].sort_values("pb", ascending=False).copy()
        pb_df["label"] = pb_df["name"].str[:20]
        pb_df["as_of"] = live_date
        fig2 = hbar(pb_df, "pb", "label", "P/B Ratio — highest to lowest", color_scale="Purples", text_fmt=".2f", period_col="as_of")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-label" style="margin-top:8px">12-Month Price Change (%)</p>', unsafe_allow_html=True)
    chg_df = vdf_clean[vdf_clean["price_chg"].notna()].sort_values("price_chg").copy()
    chg_df["label"] = chg_df["name"].str[:20]
    chg_df["color"] = chg_df["price_chg"].apply(lambda x: GREEN if x >= 0 else RED)
    fig3 = go.Figure(go.Bar(
        x=chg_df["price_chg"], y=chg_df["label"], orientation="h",
        marker_color=chg_df["color"],
        text=chg_df["price_chg"].apply(lambda x: f"{x:+.1f}%"),
        textposition="outside", textfont=dict(size=11, color="#1e293b"),
        customdata=[[live_date]] * len(chg_df),
        hovertemplate="%{y}<br>12M Change: %{x:+.1f}%<br>As of: %{customdata[0]}<extra></extra>",
    ))
    n = len(chg_df)
    fig3.update_layout(
        **{**PLOT_LAYOUT, "yaxis": dict(autorange="reversed", gridcolor=BORDER, tickfont=dict(size=11, color=TEXT))},
        height=max(300, min(n*26+70, 680)), title="12-Month Stock Price Change (%)"
    )
    fig3.add_vline(x=0, line_color=BORDER, line_width=1.5)
    st.plotly_chart(fig3, use_container_width=True)

    # ── Summary table ──
    st.markdown('<p class="section-label" style="margin-top:8px">Full Valuation Table</p>', unsafe_allow_html=True)
    tbl = vdf_clean[["ticker","name","price","pe_ttm","pb","mktcap_cr","price_chg"]].copy()
    tbl.columns = ["Ticker","Company","Price (₹)","P/E (TTM)","P/B","Mkt Cap (₹ Cr)","12M Chg %"]
    tbl = tbl.sort_values("Mkt Cap (₹ Cr)", ascending=False)
    tbl["Company"] = tbl["Company"].str[:40]
    st.dataframe(
        tbl.style
           .format({"Price (₹)": "{:,.1f}", "P/E (TTM)": "{:.1f}", "P/B": "{:.2f}",
                    "Mkt Cap (₹ Cr)": "{:,.0f}", "12M Chg %": "{:+.1f}"}, na_rep="—"),
        use_container_width=True, height=500
    )


# ═══ TAB 8: UNIVERSE ═════════════════════════════════════════════════════════
with tab8:
    st.markdown('<p class="section-label">Full NBFC Universe — 9,359 Companies</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        lc = nbfc_df.groupby("rbi_layer").agg(total=("id","count"), with_data=("has_financials","sum")).reset_index()
        lc.columns = ["Layer","Total","With Data"]
        fig = px.pie(lc, names="Layer", values="Total", color_discrete_sequence=[ACCENT, GREEN, AMBER],
                     hole=0.5)
        fig.update_layout(**PLOT_LAYOUT, height=300, title="NBFCs by RBI Layer")
        fig.update_traces(textfont_size=12)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(lc, use_container_width=True)

    with c2:
        cc = has_df.groupby("category").size().reset_index(name="n").sort_values("n",ascending=False).head(12)
        fig2 = px.bar(cc, x="n", y="category", orientation="h",
                      color="n", color_continuous_scale="Blues",
                      labels={"n":"Companies","category":""}, title="Companies with Data by Sector")
        fig2.update_layout(**{**PLOT_LAYOUT, "yaxis": dict(autorange="reversed", gridcolor=BORDER)}, height=360, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<p class="section-label" style="margin-top:8px">Top Companies by Assets</p>', unsafe_allow_html=True)
    top_a = filt_df.nlargest(top_n, "disp_assets")[
        ["name","rbi_layer","category","listed","data_quality","disp_assets","aum_cagr","avg_roa","latest_gnpa","latest_cl"]
    ].copy()
    top_a.columns = ["Name","Layer","Sector","Listed","Data","Assets (₹ Cr)","AUM CAGR %","Avg ROA %","GNPA %","Credit Loss %"]
    top_a["Assets (₹ Cr)"] = top_a["Assets (₹ Cr)"].apply(lambda x: f"₹{x:,.0f}" if pd.notna(x) else "—")
    st.dataframe(top_a, use_container_width=True, height=500)


# ═══ TAB 9: DATA ═════════════════════════════════════════════════════════════
with tab9:
    st.markdown('<p class="section-label">Raw Data & Export</p>', unsafe_allow_html=True)

    search = st.text_input("Search company", "", placeholder="Type company name…", label_visibility="collapsed")
    raw = full_df.copy()
    if search:
        raw = raw[raw["name"].str.contains(search, case=False, na=False)]

    out = raw[["name","rbi_layer","category","listed","data_quality",
               "disp_assets","aum_cagr","asset_cagr","avg_roa","avg_roe",
               "latest_gnpa","avg_gnpa","latest_cl","latest_fy","fy_count"]].copy()
    out.columns = ["Name","Layer","Sector","Listed","Data Quality",
                   "Assets (₹ Cr)","AUM CAGR %","Asset CAGR %","Avg ROA %","Avg ROE %",
                   "Latest GNPA %","Avg GNPA %","Latest Credit Loss %","Latest FY","FY Count"]
    st.dataframe(out, use_container_width=True, height=500)
    st.download_button("⬇️ Download CSV", out.to_csv(index=False), "nbfc_data.csv", "text/csv")

    st.markdown('<p class="section-label" style="margin-top:12px">Financials Table</p>', unsafe_allow_html=True)
    fe = fins_df.merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    if search:
        fe = fe[fe["name"].str.contains(search, case=False, na=False)]
    drop = [c for c in ["id_x","id_y","nbfc_id"] if c in fe.columns]
    st.dataframe(fe.drop(columns=drop), use_container_width=True, height=380)


# ═══ TAB 10: SQL ══════════════════════════════════════════════════════════════
with tab10:
    st.markdown('<p class="section-label">SQL Query Explorer</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">Run any SELECT query against the database. Results export to CSV. Only SELECT queries are allowed.</div>', unsafe_allow_html=True)

    # ── Schema reference ──
    with st.expander("📋 Table Reference — click to expand"):
        st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:12px;color:{SUBTEXT}">
<div>
<b style="color:{TEXT}">companies</b><br>
id, name, short_name, sector, business_type, rbi_layer,<br>
listed, nse_ticker, data_quality, promoter_group
</div>
<div>
<b style="color:{TEXT}">income_statement</b><br>
company_id, period, period_type, period_end_date,<br>
net_interest_income, net_credit_losses, credit_cost_pct, pat, source
</div>
<div>
<b style="color:{TEXT}">balance_sheet</b><br>
company_id, period, period_type, period_end_date,<br>
loan_book, total_assets, total_equity, source
</div>
<div>
<b style="color:{TEXT}">key_ratios</b><br>
company_id, period, period_type, period_end_date,<br>
roa, roe, gnpa_pct, credit_cost_pct, leverage_ratio,<br>
loan_book_growth, asset_growth, pat_growth
</div>
<div>
<b style="color:{TEXT}">valuation_snapshots</b><br>
company_id, snapshot_date, price, market_cap_cr,<br>
pe_ttm, pb_ratio, price_chg_1m, price_chg_12m
</div>
<div>
<b style="color:{TEXT}">data_sources</b><br>
company_id, period, source_type, source_url,<br>
fetched_date, verified
</div>
</div>
""", unsafe_allow_html=True)

    # ── Plain English → SQL ──────────────────────────────────────────────────
    st.markdown('<p class="section-label">Ask in Plain English</p>', unsafe_allow_html=True)

    SCHEMA_CONTEXT = """
SQLite database with these tables:

companies(id, name, short_name, sector, business_type, rbi_layer, listed, nse_ticker, data_quality)
income_statement(company_id, period, period_type, period_end_date, net_interest_income, net_credit_losses, credit_cost_pct, pat, source)
balance_sheet(company_id, period, period_type, period_end_date, loan_book, total_assets, total_equity, source)
key_ratios(company_id, period, period_type, period_end_date, roa, roe, gnpa_pct, credit_cost_pct, leverage_ratio, loan_book_growth, asset_growth, pat_growth)
valuation_snapshots(company_id, snapshot_date, price, market_cap_cr, pe_ttm, pb_ratio, price_chg_12m)
data_sources(company_id, period, source_type, source_url, fetched_date, verified)

Key facts:
- All financial values are in ₹ Crore
- period values: 'FY2021', 'FY2022', 'FY2023', 'FY2024', 'FY2025', 'FY2026-Q1', 'FY2026-Q2', 'FY2026-Q3'
- period_type: 'annual' or 'quarterly'
- sector values include: 'Microfinance', 'Housing Finance', 'Affordable Housing', 'Gold Loans', 'Vehicle Finance', 'Consumer & SME', 'Infrastructure Finance', 'SME & Business Loans', 'Diversified Finance', 'Credit Cards'
- rbi_layer: 'Upper', 'Middle', 'Base'
- listed: 1 = listed on NSE/BSE, 0 = unlisted
- data_quality: 'actual' = audited, 'estimated' = projected
"""

    nl_col, btn_col = st.columns([5, 1])
    with nl_col:
        nl_query = st.text_input("Describe what you want to see", placeholder="e.g. Show me the top 10 microfinance companies by loan book in FY2025", label_visibility="collapsed")
    with btn_col:
        nl_run = st.button("✨ Generate SQL", use_container_width=True)

    if nl_run and nl_query.strip():
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = None
        if not api_key:
            st.warning("Anthropic API key not configured. Add ANTHROPIC_API_KEY to your Streamlit secrets to enable this feature.")
        else:
            try:
                import anthropic
                with st.spinner("Generating SQL…"):
                    client = anthropic.Anthropic(api_key=api_key)
                    msg = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=512,
                        messages=[{
                            "role": "user",
                            "content": f"""Given this database schema:
{SCHEMA_CONTEXT}

Write a SQLite SELECT query for: {nl_query}

Rules:
- Return ONLY the SQL query, no explanation, no markdown code blocks
- Use table aliases (c for companies, k for key_ratios, b for balance_sheet, i for income_statement)
- Always JOIN companies to get short_name and sector
- LIMIT to 50 rows unless the user specifies otherwise
- Only use SELECT, never INSERT/UPDATE/DELETE"""
                        }]
                    )
                generated_sql = msg.content[0].text.strip().removeprefix("```sql").removeprefix("```").removesuffix("```").strip()
                st.session_state["generated_sql"] = generated_sql
            except Exception as e:
                st.error(f"Could not generate SQL: {e}")

    # If we have a generated query, show it in the editor below
    if "generated_sql" in st.session_state:
        st.markdown(f'<div class="note-banner" style="border-left-color:{ACCENT}">✨ Generated SQL — review and run below</div>', unsafe_allow_html=True)

    st.markdown("---")
    # ── Example queries ──
    EXAMPLES = {
        "Top 15 by ROA (FY2025)": """SELECT c.short_name, c.sector, k.roa, k.roe, k.gnpa_pct, k.leverage_ratio
FROM key_ratios k JOIN companies c ON k.company_id = c.id
WHERE k.period = 'FY2025' AND c.listed = 1
ORDER BY k.roa DESC
LIMIT 15""",

        "Loan book growth FY2021→FY2025": """SELECT c.short_name, c.sector,
  MAX(CASE WHEN b.period='FY2021' THEN b.loan_book END) AS lb_fy21,
  MAX(CASE WHEN b.period='FY2025' THEN b.loan_book END) AS lb_fy25,
  ROUND((MAX(CASE WHEN b.period='FY2025' THEN b.loan_book END) /
         MAX(CASE WHEN b.period='FY2021' THEN b.loan_book END) - 1) * 100, 1) AS growth_pct
FROM balance_sheet b JOIN companies c ON b.company_id = c.id
GROUP BY c.id HAVING lb_fy21 IS NOT NULL AND lb_fy25 IS NOT NULL
ORDER BY growth_pct DESC""",

        "Microfinance sector stress FY2024→FY2025": """SELECT c.short_name,
  MAX(CASE WHEN k.period='FY2024' THEN k.gnpa_pct END) AS gnpa_fy24,
  MAX(CASE WHEN k.period='FY2025' THEN k.gnpa_pct END) AS gnpa_fy25,
  MAX(CASE WHEN k.period='FY2024' THEN i.pat END) AS pat_fy24,
  MAX(CASE WHEN k.period='FY2025' THEN i.pat END) AS pat_fy25
FROM key_ratios k
JOIN companies c ON k.company_id = c.id
JOIN income_statement i ON i.company_id = k.company_id AND i.period = k.period
WHERE c.sector = 'Microfinance'
GROUP BY c.id ORDER BY gnpa_fy25 DESC""",

        "PAT trend for top 10 companies": """SELECT c.short_name, i.period, i.pat, i.net_interest_income
FROM income_statement i JOIN companies c ON i.company_id = c.id
WHERE c.id IN (
  SELECT company_id FROM balance_sheet WHERE period='FY2025'
  ORDER BY total_assets DESC LIMIT 10
) AND i.period_type = 'annual'
ORDER BY c.short_name, i.period""",

        "Data sources audit": """SELECT c.short_name, c.sector, d.source_type, d.period, d.verified, d.source_url
FROM data_sources d JOIN companies c ON d.company_id = c.id
ORDER BY d.source_type, c.short_name""",

        "Housing finance comparison FY2025": """SELECT c.short_name,
  b.loan_book, b.total_assets, b.total_equity,
  k.roa, k.roe, k.gnpa_pct
FROM balance_sheet b
JOIN companies c ON b.company_id = c.id
JOIN key_ratios k ON k.company_id = c.id AND k.period = b.period
WHERE c.sector IN ('Housing Finance','Affordable Housing') AND b.period = 'FY2025'
ORDER BY b.loan_book DESC""",
    }

    col_ex, col_run = st.columns([3, 1])
    with col_ex:
        selected_example = st.selectbox("Load an example query", ["— write your own —"] + list(EXAMPLES.keys()), label_visibility="collapsed")

    # Generated SQL from plain English takes priority, then example, then default
    if "generated_sql" in st.session_state and selected_example == "— write your own —":
        default_query = st.session_state.pop("generated_sql")
    else:
        default_query = EXAMPLES.get(selected_example, "SELECT c.short_name, c.sector, k.roa, k.roe, k.gnpa_pct\nFROM key_ratios k JOIN companies c ON k.company_id = c.id\nWHERE k.period = 'FY2025'\nORDER BY k.roa DESC\nLIMIT 20")

    query = st.text_area("SQL query", value=default_query, height=160, label_visibility="collapsed")

    run_col, dl_col, _ = st.columns([1, 1, 5])
    run = run_col.button("▶ Run Query", type="primary", use_container_width=True)

    if run or selected_example != "— write your own —":
        q = query.strip()
        if not q.lower().startswith("select"):
            st.error("Only SELECT queries are allowed.")
        else:
            try:
                conn_sql = sqlite3.connect(DB_PATH)
                result_df = pd.read_sql(q, conn_sql)
                conn_sql.close()
                st.caption(f"{len(result_df)} rows returned")
                st.dataframe(result_df, use_container_width=True, height=500)
                dl_col.download_button(
                    "⬇️ CSV", result_df.to_csv(index=False),
                    "query_result.csv", "text/csv", use_container_width=True
                )
            except Exception as e:
                st.error(f"Query error: {e}")
