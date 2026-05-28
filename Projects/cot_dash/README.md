# cot_dash

An interactive [Dash](https://dash.plotly.com/) dashboard for **Sugar No. 11** futures
that overlays price action with **CFTC Commitments of Traders (COT)** positioning, so
you can read price alongside what the hedge funds are doing.

The core idea is contrarian: when Managed Money (hedge funds) is crowded into one side
of the trade, that extreme often precedes a reversal. The dashboard surfaces those
extremes with a rolling percentile and shaded signal bands.

## What it shows

The app renders four stacked charts, all filtered by a shared contract selector and date range:

1. **Sugar No. 11 Futures Prices** — the selected contract (SB1–SB6) with a dotted 50-day moving average.
2. **SB1 − SB2 Calendar Spread** — a proxy for physical tightness (backwardation vs. contango).
3. **Managed Money Net Positioning** — weekly hedge-fund net longs minus shorts, green when net long, red when net short.
4. **Managed Money Percentile** — the net position ranked against its trailing ~5-year history. Shaded bands flag extremes:
   - **Green (< 10th pct)** — crowded short → contrarian bullish
   - **Red (> 90th pct)** — crowded long → contrarian bearish

## Data sources

| Source | Provides | Loaded by |
| --- | --- | --- |
| `../../data/pull.xlsx` | Daily SB1–SB6 prices (one sheet per contract) | [load_data.py](load_data.py) |
| CFTC disaggregated futures report (via the `cot_reports` package) | Weekly Managed Money positioning for Sugar No. 11 | [load_cot.py](load_cot.py) |

COT is released weekly (Tuesday); the app forward-fills those values across the daily
price rows so every chart point has a positioning value.

## Files

- [app.py](app.py) — Dash layout and callback (presentation only). Merges prices + COT and builds the four figures.
- [load_data.py](load_data.py) — reads the price workbook, aligns SB1–SB6 on `Date`, and computes the SB1–SB2 spread.
- [load_cot.py](load_cot.py) — pulls the COT report year-by-year, filters to Sugar No. 11, and computes `Managed_Money_Net` and its rolling percentile.
- [analytics.py](analytics.py) — `rolling_percentile()`, the trailing-window percentile rank used for the signal bands.
- [cot.py](cot.py) — scratch script for inspecting COT data outside the app.
- `f_year.txt` — a raw CSV dump of fetched COT rows (scratch output, not used by the app).

## Setup

Dependencies are listed in the repo-root [`requirements.txt`](../../requirements.txt):

```
pip install -r ../../requirements.txt
```

Key packages: `dash`, `plotly`, `pandas`, `openpyxl` (Excel reading), and `cot_reports` (CFTC data).

## Running

`load_data.py` resolves the price workbook at `../../data/pull.xlsx`, relative to this
directory — so run the app from inside `Projects/cot_dash/`:

```
cd Projects/cot_dash
python app.py
```

Then open the dev server URL Dash prints (default <http://127.0.0.1:8050>). The first
run fetches COT data from the CFTC for each year since 2016, so initial startup takes a
few seconds.

## Usage

- **Select a Contract** — switch between front month (SB1) and deferred months (SB2–SB6).
- **Date range** — narrow the window; the 50-day MA recomputes over the visible range.
- Watch the percentile chart: prints into the green band have historically been crowded-short setups, the red band crowded-long.

> Not investment advice — the contrarian bands are a research aid, not a trade signal.
