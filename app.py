"""
NBFC Intelligence Dashboard — India
FY2021–FY2025 | 9,359 NBFCs | 74 with financial data
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

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
MUTED    = "#64748b"   # slate-500
BG_PAGE  = "#ffffff"   # white
BG_CARD  = "#f8fafc"   # slate-50
BORDER   = "#e2e8f0"   # slate-200
TEXT     = "#0f172a"   # slate-900
SUBTEXT  = "#64748b"   # slate-500

GRID_COLOR = "#f1f5f9"  # very light grid lines

PLOT_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color=TEXT, family="Inter, sans-serif", size=12),
    margin=dict(l=10, r=120, t=44, b=10),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=BORDER,
        borderwidth=1,
        font=dict(size=11, color=TEXT),
    ),
    xaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=SUBTEXT)),
    yaxis=dict(gridcolor=GRID_COLOR, linecolor=BORDER, tickcolor=BORDER, tickfont=dict(color=TEXT)),
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
[data-testid="metric-container"] label {{
    color: {SUBTEXT} !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
[data-testid="metric-container"] [data-testid="metric-value"] {{
    color: {TEXT} !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}}
[data-testid="metric-container"] [data-testid="metric-delta"] {{
    font-size: 12px !important;
    color: {SUBTEXT} !important;
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
    border: 1px solid #fde68a;
    border-left: 3px solid {AMBER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #92400e;
    margin-bottom: 16px;
}}

/* ── section label ── */
.section-label {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {SUBTEXT};
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
    color: {SUBTEXT};
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


@st.cache_data(ttl=300)
def compute_metrics(nbfc_df, fins_df):
    rows = []
    for nbfc_id, grp in fins_df.groupby("nbfc_id"):
        grp = grp.sort_values("fiscal_year")
        fys = grp["fiscal_year"].tolist()

        def _cagr(col):
            s = grp[grp[col].notna()]
            if len(s) < 2: return None
            sv, ev, n = s.iloc[0][col], s.iloc[-1][col], len(s)-1
            if sv and sv > 0 and ev and ev > 0:
                return round(((ev/sv)**(1/n)-1)*100, 1)

        lr = grp[grp["total_assets"].notna()]
        latest = lr.iloc[-1] if len(lr) else None
        rows.append({
            "nbfc_id": nbfc_id,
            "aum_cagr":     _cagr("loan_book") or _cagr("total_assets"),
            "asset_cagr":   _cagr("total_assets"),
            "avg_roa":      round(grp["roa"].dropna().mean(), 2)  if grp["roa"].notna().any()  else None,
            "avg_roe":      round(grp["roe"].dropna().mean(), 1)  if grp["roe"].notna().any()  else None,
            "latest_gnpa":  grp[grp["gnpa_pct"].notna()].iloc[-1]["gnpa_pct"] if grp["gnpa_pct"].notna().any() else None,
            "avg_gnpa":     round(grp["gnpa_pct"].dropna().mean(), 2) if grp["gnpa_pct"].notna().any() else None,
            "latest_cl":    grp[grp["credit_cost_pct"].notna()].iloc[-1]["credit_cost_pct"] if grp["credit_cost_pct"].notna().any() else None,
            "fin_latest_assets": latest["total_assets"] if latest is not None else None,
            "latest_pat":   latest["pat"]          if latest is not None else None,
            "latest_fy":    fys[-1] if fys else None,
            "fy_count":     len(fys),
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
<span style="color:{SUBTEXT};font-size:12px;line-height:1.9">
🏦 RBI/FIDC registry — 9,359 NBFCs<br>
📈 Screener.in — listed companies<br>
⭐ CRISIL / ICRA / CARE reports<br>
🗓️ Coverage: FY2021–FY2025
</span>
""", unsafe_allow_html=True)

    est_cnt = has_df[has_df["data_quality"] == "estimated"].shape[0] if "data_quality" in has_df.columns else 0
    st.markdown(f"""
<br>
<span style="color:{SUBTEXT};font-size:12px">
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
st.markdown('<p class="page-subtitle">India\'s Non-Banking Financial Companies · FY2021–FY2025 · RBI/FIDC, Screener.in, Rating Agencies</p>', unsafe_allow_html=True)

# ── KPI ROW ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Total NBFCs", "9,359", "RBI registered")
with k2:
    st.metric("With Financial Data", str(has_df.shape[0]), "FY2021–FY2025")
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Growth", "Profitability", "Asset Quality",
    "Credit Losses", "Trends", "Deep Dive", "Universe", "Data",
])

# helper: consistent chart styling
def style(fig, height=420, legend=True):
    fig.update_layout(**PLOT_LAYOUT, height=height, showlegend=legend)
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)
    return fig

def hbar(df, x, y, title, color_col=None, color_scale="Blues", text_fmt=".1f"):
    """Horizontal bar — height auto-scales to number of rows (32px each)."""
    n = len(df)
    height = max(360, n * 34 + 90)
    kw = dict(color=x, color_continuous_scale=color_scale)
    fig = px.bar(df, x=x, y=y, orientation="h", title=title, **kw,
                 labels={x: x, y: ""})
    layout = {**PLOT_LAYOUT, "margin": dict(l=10, r=140, t=44, b=10)}
    fig.update_layout(**layout, height=height, showlegend=False, coloraxis_showscale=False)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=12, color=TEXT))
    fig.update_xaxes(tickfont=dict(size=11, color=SUBTEXT))
    fig.update_traces(
        texttemplate=f"%{{x:{text_fmt}}}",
        textposition="outside",
        textfont=dict(size=11, color=SUBTEXT),
        cliponaxis=False,
    )
    return fig


# ═══ TAB 1: GROWTH ═══════════════════════════════════════════════════════════
with tab1:
    st.markdown('<p class="section-label">AUM Growth Rankings</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">★ Estimated data for unlisted companies — sourced from CRISIL/ICRA/CARE rating rationales, not audited accounts.</div>', unsafe_allow_html=True)

    df_g = filt_df[filt_df["aum_cagr"].notna()].sort_values("aum_cagr", ascending=False).copy()
    df_g["label"] = df_g["name"].str[:38] + df_g.apply(lambda r: " ★" if r.get("data_quality")=="estimated" else "", axis=1)

    c1, c2 = st.columns(2)
    with c1:
        top = df_g.head(20)
        fig = hbar(top, "aum_cagr", "label", "Fastest Growing", color_scale="Greens", text_fmt=".1f")
        fig.update_traces(marker_color=GREEN, opacity=0.85)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        bot = df_g.tail(20).sort_values("aum_cagr")
        fig2 = hbar(bot, "aum_cagr", "label", "Slowest Growing / Declining", color_scale="Reds", text_fmt=".1f")
        fig2.update_traces(marker_color=RED, opacity=0.85)
        st.plotly_chart(fig2, use_container_width=True)

    # Bubble
    st.markdown('<p class="section-label" style="margin-top:8px">Growth vs Profitability</p>', unsafe_allow_html=True)
    bub = filt_df[filt_df["aum_cagr"].notna() & filt_df["avg_roa"].notna() & filt_df["disp_assets"].notna()].copy()
    bub["sz"] = (bub["disp_assets"].clip(upper=400000)/800).clip(lower=3)
    bub["label"] = bub["name"].str[:30]
    fig3 = px.scatter(bub.head(top_n), x="aum_cagr", y="avg_roa", size="sz",
                      color="category", color_discrete_sequence=PALETTE,
                      hover_name="label",
                      hover_data={"aum_cagr":":.1f","avg_roa":":.2f","sz":False},
                      labels={"aum_cagr":"AUM CAGR (%)","avg_roa":"Avg ROA (%)","category":"Sector"})
    fig3.add_vline(x=bub["aum_cagr"].median(), line_dash="dot", line_color=BORDER, line_width=1)
    fig3.add_hline(y=0, line_dash="dot", line_color=RED, line_width=1, opacity=0.4)
    fig3.add_annotation(x=bub["aum_cagr"].median()+0.5, y=bub["avg_roa"].max()*0.95,
                        text="Median growth", showarrow=False, font=dict(size=10, color=MUTED))
    style(fig3, height=460)
    st.plotly_chart(fig3, use_container_width=True)


# ═══ TAB 2: PROFITABILITY ════════════════════════════════════════════════════
with tab2:
    st.markdown('<p class="section-label">Profitability — ROA & ROE</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        df_roa = filt_df[filt_df["avg_roa"].notna()].sort_values("avg_roa", ascending=False).head(20).copy()
        df_roa["label"] = df_roa["name"].str[:36]
        fig = hbar(df_roa, "avg_roa", "label", "Top 20 by Return on Assets (ROA %)",
                   color_scale="Greens", text_fmt=".2f")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df_roe = filt_df[filt_df["avg_roe"].notna()].sort_values("avg_roe", ascending=False).head(20).copy()
        df_roe["label"] = df_roe["name"].str[:36]
        fig2 = hbar(df_roe, "avg_roe", "label", "Top 20 by Return on Equity (ROE %)",
                    color_scale="Blues", text_fmt=".1f")
        st.plotly_chart(fig2, use_container_width=True)

    # Sector bar
    st.markdown('<p class="section-label" style="margin-top:8px">By Sector</p>', unsafe_allow_html=True)
    sec = filt_df[filt_df["avg_roa"].notna()].groupby("category").agg(
        avg_roa=("avg_roa","mean"), avg_roe=("avg_roe","mean"), n=("name","count")
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
    fig4 = px.line(pat_data, x="fiscal_year", y="pat", color="name",
                   color_discrete_sequence=PALETTE,
                   labels={"pat":"Net Profit (₹ Cr)","fiscal_year":"","name":""})
    fig4.update_traces(line_width=2)
    style(fig4, height=380)
    st.plotly_chart(fig4, use_container_width=True)


# ═══ TAB 3: ASSET QUALITY ════════════════════════════════════════════════════
with tab3:
    st.markdown('<p class="section-label">Asset Quality — GNPA %</p>', unsafe_allow_html=True)

    df_gq = filt_df[filt_df["latest_gnpa"].notna()].sort_values("latest_gnpa").copy()
    df_gq["label"] = df_gq["name"].str[:36]

    c1, c2 = st.columns(2)
    with c1:
        top20 = df_gq.head(20)
        fig = hbar(top20, "latest_gnpa", "label", "Cleanest Loan Books — Lowest GNPA",
                   color_scale="Greens_r", text_fmt=".2f")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        bot20 = df_gq.tail(20).sort_values("latest_gnpa", ascending=False)
        fig2 = hbar(bot20, "latest_gnpa", "label", "Highest NPA Stress",
                    color_scale="Reds", text_fmt=".2f")
        st.plotly_chart(fig2, use_container_width=True)

    # Sector trend
    st.markdown('<p class="section-label" style="margin-top:8px">GNPA Trend by Sector</p>', unsafe_allow_html=True)
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
    piv.index = piv.index.str[:36]
    fig4 = px.imshow(piv, color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels={"color":"GNPA %"})
    fig4.update_layout(**PLOT_LAYOUT, height=680, coloraxis_colorbar=dict(len=0.5))
    st.plotly_chart(fig4, use_container_width=True)


# ═══ TAB 4: CREDIT LOSSES ════════════════════════════════════════════════════
with tab4:
    st.markdown('<p class="section-label">Annualized Credit Loss Rate = Credit Losses / Loan Book</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="note-banner">Credit losses = net provisions + write-offs − recoveries. Measures actual P&L cost of defaults — distinct from GNPA% (balance sheet stock).</div>', unsafe_allow_html=True)

    cl_raw = fins_df[fins_df["credit_cost_pct"].notna()].merge(
        nbfc_df[["id","name","category","data_quality"]], left_on="nbfc_id", right_on="id")
    cl_raw = cl_raw[cl_raw["name"].isin(filt_df["name"])]

    latest_cl = cl_raw.sort_values("fiscal_year").groupby("name", as_index=False).last()
    latest_cl["label"] = latest_cl["name"].str[:36] + latest_cl.apply(
        lambda r: " ★" if r.get("data_quality")=="estimated" else "", axis=1)
    latest_cl = latest_cl.sort_values("credit_cost_pct")

    c1, c2 = st.columns(2)
    with c1:
        fig = hbar(latest_cl.head(20), "credit_cost_pct", "label",
                   "Lowest Credit Loss Rate (Best)", color_scale="Greens_r", text_fmt=".2f")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = hbar(latest_cl.tail(20).sort_values("credit_cost_pct", ascending=False),
                    "credit_cost_pct", "label", "Highest Credit Loss Rate (Worst)",
                    color_scale="Reds", text_fmt=".2f")
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
        delta["label2"] = delta["name"].str[:30]
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
    piv_cl.index = piv_cl.index.str[:36]
    fig6 = px.imshow(piv_cl, color_continuous_scale="RdYlGn_r", aspect="auto",
                     labels={"color":"Credit Loss %"})
    fig6.update_layout(**PLOT_LAYOUT, height=720, coloraxis_colorbar=dict(len=0.5))
    st.plotly_chart(fig6, use_container_width=True)


# ═══ TAB 5: TRENDS ═══════════════════════════════════════════════════════════
with tab5:
    st.markdown('<p class="section-label">Multi-Year Trends</p>', unsafe_allow_html=True)

    top_lb = filt_df[filt_df["disp_assets"].notna()].nlargest(min(10,top_n), "disp_assets")

    # Loan book area
    lb_d = fins_df[fins_df["nbfc_id"].isin(top_lb["id"]) & fins_df["loan_book"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
    fig = px.area(lb_d.sort_values("fiscal_year"), x="fiscal_year", y="loan_book", color="name",
                  color_discrete_sequence=PALETTE,
                  labels={"loan_book":"Loan Book (₹ Cr)","fiscal_year":"","name":""})
    fig.update_traces(line_width=1.5)
    style(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        nii_d = fins_df[fins_df["nbfc_id"].isin(top_lb["id"]) & fins_df["nii"].notna()].merge(nbfc_df[["id","name"]], left_on="nbfc_id", right_on="id")
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
    cfins = fins_df[fins_df["nbfc_id"] == cid].sort_values("fiscal_year")
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


# ═══ TAB 7: UNIVERSE ═════════════════════════════════════════════════════════
with tab7:
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


# ═══ TAB 8: DATA ═════════════════════════════════════════════════════════════
with tab8:
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
