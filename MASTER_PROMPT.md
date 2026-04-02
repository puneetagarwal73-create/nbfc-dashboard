# NBFC Intelligence Dashboard — Master Prompt

This document captures everything needed to build, extend, or hand off this dashboard — every design choice, data rule, and feature — written in plain English.

---

## 1. What We're Building

Build a web app called "NBFC Intelligence" that lets anyone explore India's Non-Banking Financial Companies — how fast they're growing, how profitable they are, the quality of their loan books, and what the market thinks they're worth.

The app covers financial data from FY2021 through FY2026. Use annual data for FY2021–FY2025, and add quarterly data for Q1–Q3 FY2026. The full RBI registry has 9,359 NBFCs. The app is deployed on Streamlit Community Cloud. Start with collecting data for listed companies, then look for available data for unlisted NBFCs.

---

## 2. Where the Data Lives

### The Database

All data is stored in a SQLite file called `nbfc_full.db` with two tables.

The first table, `nbfc`, holds one row per company. It stores the company name, which RBI regulatory layer it belongs to (Upper, Middle, or Base), what sector it operates in (e.g. Housing Finance, Microfinance), whether it's listed on a stock exchange, whether we have financial data for it, its latest known total assets in ₹ Crore, and whether that data is audited or just estimated.

The second table, `financials`, holds one row per company per year (or quarter). Each row stores the fiscal year label, loan book size, total assets, equity capital, net interest income, profit after tax, credit losses, credit loss rate as a percentage, gross NPA percentage, return on assets, and return on equity — all in ₹ Crore where applicable.

### How Fiscal Years Are Labelled

Annual rows are labelled like "FY2025" or "FY2024". Quarterly rows are labelled "FY2026-Q1", "FY2026-Q2", "FY2026-Q3". This distinction matters — when computing multi-year growth rates or average ratios like ROA and ROE, we only use the annual rows. Mixing quarterly and annual rows into the same CAGR calculation gives wrong numbers because a single quarter's profit is not the same as a full year's.

### Where the Data Comes From

The full universe of 9,359 companies comes from the RBI/FIDC registry. For each company, look for financial data in this order of priority:

1. Public databases like Screener.in, Yahoo Finance, or similar — these are the most reliable since they pull from audited exchange filings.
2. The company's own investor relations website — look for annual reports or quarterly financial result PDFs published directly by the NBFC or its parent fintech.
3. CRISIL, ICRA, or CARE rating rationale documents — use these as a last resort for unlisted companies where no other source exists. Flag these rows as "estimated" in the database.

Live stock market data (P/E, P/B, price history) comes from Yahoo Finance via the yfinance Python library.

One important rule: for fintech NBFCs, always use the standalone NBFC entity's numbers, not the consolidated group figures. Rating agency PDFs often report the parent group's consolidated financials, which can be 2x larger than the standalone NBFC. The correct source is the company's own official quarterly filings published on their website.

---

## 3. Visual Design

### Colors

The app uses a consistent set of colors throughout. Indigo (#4f46e5) is the primary brand color used for active tabs and key accents. Emerald green (#059669) signals positive or good metrics. Red (#dc2626) signals risk or negative values. Amber (#d97706) is used for warnings and estimated data. The main text color is near-black (#0f172a), secondary labels use a dark slate (#334155) which is clearly readable on white backgrounds. Card backgrounds are off-white (#f8fafc), borders are light gray (#cbd5e1).

### Typography

The font is Inter, loaded from Google Fonts. Page titles are large and bold (30px, weight 700). Section headings inside tabs are small, uppercase, and widely spaced — they act as visual dividers rather than prominent headers. Chart axis labels use the secondary text color so they're visible but don't compete with the data.

### Charts

Every chart uses a white background. Chart titles must be explicitly set to the dark text color — Streamlit's default theme makes them pale and hard to read, so we override this. Horizontal bar charts automatically adjust their height based on how many rows they show: roughly 26 pixels per row, with a minimum of 300px and a maximum of 680px. All horizontal bar charts flip the y-axis so the highest value appears at the top — this means you must sort the data descending before passing it to the chart function.

All company names in charts are truncated to 20 characters. NBFC legal names are very long and overflow chart labels.

### Metric Cards

Streamlit's default theme makes metric card values appear faded and light. We override this aggressively with CSS that forces full opacity and dark text on all metric card elements. This must be done both in the CSS block in the app and in the Streamlit theme config file at `.streamlit/config.toml`.

---

## 4. App Structure

### Sidebar

The sidebar has five filters that apply across the whole app: RBI Layer (Upper / Middle / Base / All), Sector (all distinct categories in the data), Listing Status (All / Listed Only / Unlisted Only), a slider for how many companies to show in rankings (default 40, max 80), and a checkbox to include or exclude estimated data (on by default).

### Top of the Page

Just below the title, show five summary numbers side by side: total NBFCs in the registry (9,359), how many have financial data, their combined total assets in ₹ Lakh Crore, the average AUM growth rate (CAGR), and the average latest GNPA percentage.

### Nine Tabs

The app has nine tabs: Growth, Profitability, Asset Quality, Credit Losses, Trends, Deep Dive, Valuation, Universe, and Data.

---

## 5. What Each Tab Shows

### Growth

Two bar charts side by side — the 20 fastest-growing NBFCs on the left (green bars) and the 20 slowest or shrinking on the right (red bars). Growth is measured as AUM CAGR. Estimated data companies get a star symbol next to their name. Below these, a bubble chart plots growth rate against profitability, with bubble size representing company size and color representing sector. A vertical dotted line marks the median growth rate.

### Profitability

Two bar charts at the top — top 20 by average ROA and top 20 by average ROE, both sorted highest to lowest. Below that, a grouped bar chart shows average ROA and ROE broken down by sector. At the bottom, a line chart shows profit after tax over time for the top 10 companies.

### Asset Quality

Two bar charts — the companies with the cleanest loan books (lowest GNPA) on the left and the most stressed (highest GNPA) on the right. Below that, trend lines showing how average GNPA has moved over time for each sector. Finally, a heatmap showing GNPA percentages across the top 35 most stressed companies over the years, using a red-yellow-green color scale.

### Credit Losses

This tab opens with a note explaining that credit loss rate = net provisions plus write-offs minus recoveries, divided by the loan book. It's different from GNPA — it's the actual P&L cost of defaults. Two bar charts show the lowest and highest credit loss rates. Below that, trend lines for the 12 highest-loss companies, with a 2% reference line. A scatter plot compares credit loss rate against GNPA percentage with bubble size for company size. A waterfall chart shows which companies have improved or worsened their credit loss rate over time (green = improved, red = deteriorated). A heatmap covers the top 40 companies.

### Trends

A stacked area chart shows loan book growth over time for the top 10 companies. Below that, two charts side by side: net interest income trends (left) and total industry assets stacked by RBI layer (right). Then a return on assets trend chart for the top companies.

### Deep Dive

A dropdown to pick any company with financial data. Once selected, it shows colored badges for the company's RBI layer, data quality, listing status, and sector. A warning banner appears if the data is estimated or if quarterly data is present. Five key metrics are shown in a row. Then six charts: assets and loan book over time, revenue and profit over time, GNPA trend, ROA and ROE trend, credit loss rate over time. At the bottom, a transposed financial table with fiscal years as columns.

### Valuation

Described fully in Section 6 below.

### Universe

A donut chart showing how 9,359 NBFCs are split across RBI layers, with a table. A horizontal bar chart showing how many companies we have financial data for by sector. A full sortable table of the top companies by assets with all key metrics.

### Data

A search box that filters the tables below. A full metrics table for all companies with a CSV download button. A raw financials table showing every row in the database.

---

## 6. Valuation Tab

This tab shows live stock market data for all listed NBFCs. The data must always be fetched live from Yahoo Finance — never use static or pre-loaded values.

### The Company-to-Ticker Mapping

We maintain a dictionary mapping each company's full name to its Yahoo Finance ticker symbol (which ends in ".NS" for NSE-listed stocks). This covers 47 listed NBFCs. Three tickers that were initially wrong have been corrected: L&T Finance uses "LTF.NS" (not "LTFH.NS"), Fusion Micro Finance uses "FUSION.NS" (not "FUSIONMICRO.NS"), and SK Finance uses "SKFIN.NS" (not "SKFINANCE.NS").

### How We Fetch the Data

We cache the results for one hour so the app doesn't hammer Yahoo Finance on every page load. The cache decorator must not use the `show_spinner` parameter — that parameter breaks on Streamlit Cloud.

For price history, we download all 47 tickers in a single batch call going back 12 months with monthly intervals. This is much faster than calling each ticker individually and avoids rate limiting.

For P/E and P/B ratios, we first try Yahoo Finance's "fast_info" object which returns quickly. If it doesn't have the ratio, we fall back to the slower but more complete "info" dictionary. The 12-month price change is calculated as the percentage difference between today's price and the price 12 months ago from the batch download.

### Layout of the Tab

A note banner at the top explains the data is live, P/E is trailing twelve months, and it refreshes hourly.

Three summary numbers: median P/E across all listed NBFCs, median P/B, and median 12-month stock price change.

Two charts side by side: P/E ratio for all companies sorted highest to lowest (blue bars), and P/B ratio sorted highest to lowest (purple bars).

A full-width chart showing 12-month price change for each company — green bars for positive returns, red for negative. This is sorted so the best performers appear at the top.

A summary table with ticker, company name, current price, P/E, P/B, market cap in ₹ Crore, and 12-month change — sorted by market cap. Do not use background color gradients on the table — that feature requires matplotlib which is not available on Streamlit Cloud.

---

## 7. Tricky Rules to Remember

**Sort direction in horizontal bar charts:** The chart function reverses the y-axis so the first row of data appears at the top. This means you must sort your data in descending order before passing it to the chart. If you sort ascending, the highest value ends up at the bottom.

**CAGR uses annual data only:** Never include quarterly rows (FY2026-Q1 etc.) when computing multi-year growth rates or average ratios. Filter them out first.

**Metric card colors:** Streamlit's default theme makes metric values appear faded. Override with CSS targeting `[data-testid="stMetricValue"]` with `opacity: 1 !important` and explicit dark color and font weight.

**No matplotlib:** Streamlit Cloud's free tier does not have matplotlib installed. Avoid any feature that depends on it, including pandas' `.background_gradient()` method on dataframes.

**Standalone vs consolidated for fintechs:** When adding data for fintech NBFCs from rating agency PDFs, check whether the figures are for the parent group or the standalone NBFC entity. Use standalone only. The difference can be 2x on key metrics like PAT.

**Cache decorator:** `@st.cache_data(ttl=3600)` is correct. Do not add `show_spinner=False` — that parameter causes errors on Streamlit Cloud.

---

## 8. Packages Required

streamlit 1.55.0, pandas 2.3.3, plotly 6.6.0, numpy 2.4.4, openpyxl 3.1.5, yfinance 0.2.54 or higher. No matplotlib.

---

## 9. What Still Needs to Be Done

**Fibe (EarlySalary):** FY2026 Q2 and Q3 quarterly data hasn't been added yet. The PDFs on their website return a 403 error when accessed programmatically. Share the direct PDF URLs to unblock this.

**WhizDM Finance:** FY2025 data was estimated using sector growth rates. Should be verified against their official filings.

**Piramal Enterprises and Piramal Capital & Housing Finance:** FY2025 data was added manually (not from yfinance — their tickers return no financial data). Values should be verified against official BSE filings.

**Annapurna Finance, Arohan, Asirvad, Axis Finance:** These previously had audited historical data but FY2025 was estimated using sector growth rates (now marked "estimated"). Should be updated once official FY2025 figures are available.

**Resolved:** FY2025 data is now complete for all 74 companies (49 listed + 25 unlisted). All 7 previously missing listed companies have been filled in using yfinance (audited financials from exchange filings).

---

## 10. Data Quality Standards

Never use training data or static snapshots. All data in the app must come from live, verifiable sources.

When adding or updating any data point, confirm the source and recency before inserting it into the database. If you cannot verify a number from a primary source (company filing, stock exchange disclosure, or a reliable public database like Screener.in), do not add it silently — flag it as estimated instead.

Spot-check every chart and table after adding new data. Look for values that seem out of range for the company's size or sector, sudden jumps between years that aren't explained by a known event, and any company showing data for a year that hasn't actually been reported yet.

Clearly mark unverified data in the UI. Any row in the database with `data_quality = "estimated"` should display a star symbol next to the company name in charts and a visible amber banner in the Deep Dive tab. The sidebar filter to exclude estimated data must work correctly so users can opt out entirely.

For listed companies, the data on Screener.in reflects audited accounts filed with the stock exchange — treat this as ground truth. For unlisted companies, the bar is lower by necessity, but still prefer company-published PDFs over rating agency summaries.

---

## 11. Why We Made Certain Choices

We use SQLite instead of CSVs because it handles joins cleanly, filters efficiently, and makes it easy to add new data without restructuring everything.

We cache database reads for 5 minutes and valuation data for 1 hour. The database doesn't change while the app is running, and yfinance calls are slow enough that hitting them on every interaction would make the app feel broken.

We fetch price history for all 47 tickers in one batch Yahoo Finance call rather than 47 individual calls. Individual calls get rate-limited quickly and are much slower.

We truncate company names to 20 characters in all charts because NBFC legal names are very long and will always overflow chart labels at any reasonable font size.

We always source standalone entity figures for fintech NBFCs because rating agency PDFs default to consolidated group numbers, which include subsidiaries and are not comparable to the pure NBFC figures we use for every other company in the dataset.
