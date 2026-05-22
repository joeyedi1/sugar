"""
Step 4 — Forward curves (SB, QW) + 5-year white premium.
Reads the frozen Bloomberg pull, builds three charts, saves PNGs.

The white_premium() function is written to lift straight into the
Project-1 Dash app, so keep it pure (no file I/O, no plotting).
"""

from functools import cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PULL = "data/pull.xlsx"
WP_FACTOR = 22.0462          # cents/lb -> $/tonne


# ---------- data layer (pure, reusable) ----------

def white_premium(sb, qw):
    """White premium in $/tonne: QW - SB * 22.0462. Works on scalars or Series."""
    return qw - sb * WP_FACTOR


@cache
def load_series(tab):
    """Read one BDH tab (no header) -> date-sorted DataFrame[date, price]."""
    df = pd.read_excel(PULL, sheet_name=tab, header=None, names=["date", "price"])
    return df.sort_values("date").reset_index(drop=True)


def latest_curve(prefix):
    """Latest price of prefix1..prefix6 -> list of 6 floats (the forward curve)."""
    return [load_series(f"{prefix}{i}")["price"].iloc[-1] for i in range(1, 7)]


def white_premium_history(years=5):
    """Merge SB1 & QW1 on date, compute WP, return the last `years` of data."""
    merged = pd.merge(load_series("SB1"), load_series("QW1"),
                      on="date", suffixes=("_sb", "_qw"))
    merged["wp"] = white_premium(merged["price_sb"], merged["price_qw"])
    cutoff = merged["date"].max() - pd.DateOffset(years=years)
    return merged[merged["date"] >= cutoff]


def seasonal_index(tab="SB1", years=None):
    """Average within-year seasonal shape: each month expressed as % of that
    year's mean price, then averaged across COMPLETE years. 100 = annual average,
    >100 = seasonally firm, <100 = seasonally soft. Normalising per-year is what
    stops a high-price year (2023) swamping a low one (2020). Pass `years` to
    restrict to the last N complete years."""
    df = load_series(tab).assign(
        year=lambda d: d["date"].dt.year,
        month=lambda d: d["date"].dt.month)
    monthly = df.groupby(["year", "month"])["price"].mean().reset_index()
    # keep only 12-month years so a partial year (2026) doesn't distort the shape
    complete = monthly.groupby("year")["month"].transform("count") == 12
    monthly = monthly[complete].copy()
    if years is not None:
        monthly = monthly[monthly["year"] > monthly["year"].max() - years]
    if monthly.empty:
        raise ValueError(f"no complete years in {tab} — cannot compute seasonal index")
    monthly["annual_mean"] = monthly.groupby("year")["price"].transform("mean")
    monthly["idx"] = monthly["price"] / monthly["annual_mean"] * 100
    result = monthly.groupby("month")["idx"].agg(["mean", "min", "max"]).reset_index()
    result.attrs["n_years"] = int(monthly["year"].nunique())
    return result


def snapshot_date():
    """Latest date across SB1/QW1 formatted "DD Mon YYYY" for chart labels."""
    latest = max(load_series("SB1")["date"].max(), load_series("QW1")["date"].max())
    return latest.strftime("%d %b %Y")


def curve_shape(prices):
    """One-word descriptor for a 6-point forward curve."""
    diff = prices[-1] - prices[0]
    spread = max(prices) - min(prices)
    if spread == 0 or abs(diff) < 0.25 * spread:
        return "flat"
    return "contango" if diff > 0 else "backwardation"


# ---------- chart layer ----------

def plot_forward_curve(prices, product, outfile, label_date):
    fig = go.Figure(go.Scatter(
        x=list(range(1, 7)), y=prices, mode="lines+markers", line=dict(width=2)))
    fig.update_layout(
        title=f"{product} Forward Curve — {label_date} ({curve_shape(prices)})",
        xaxis_title="Contract (1 = front)", yaxis_title="Price",
        template="plotly_white")
    fig.write_image(outfile)
    print("saved", outfile)


def plot_white_premium(df, outfile, label_date):
    latest = df["wp"].iloc[-1]
    fig = go.Figure(go.Scatter(x=df["date"], y=df["wp"], mode="lines", line=dict(width=1.5)))
    fig.update_layout(
        title=f"White Premium (QW - SB x {WP_FACTOR}) — ~${latest:.0f}/t, {label_date}",
        xaxis_title="Date", yaxis_title="White premium ($/tonne)",
        template="plotly_white")
    fig.write_image(outfile)
    print("saved", outfile)


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def plot_seasonal(df, outfile, product="SB raw sugar"):
    n_years = df.attrs.get("n_years", "?")
    fig = go.Figure()
    # min-max band across years (shows how reliable the seasonal pattern is)
    fig.add_trace(go.Scatter(x=df["month"], y=df["max"], mode="lines",
                             line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=df["month"], y=df["min"], mode="lines",
                             line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(99,110,250,0.15)",
                             name="yearly range"))
    # average seasonal line
    fig.add_trace(go.Scatter(x=df["month"], y=df["mean"], mode="lines+markers",
                             line=dict(width=2), name="avg"))
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    fig.update_layout(
        title=f"{product} — {n_years}-yr Seasonal Pattern (monthly avg as % of annual mean)",
        xaxis=dict(title="Month", tickmode="array",
                   tickvals=list(range(1, 13)), ticktext=MONTHS),
        yaxis_title="Index (100 = annual average)",
        template="plotly_white")
    fig.write_image(outfile)
    print("saved", outfile)


# ---------- run (only when executed directly, not on import) ----------

if __name__ == "__main__":
    Path("charts").mkdir(exist_ok=True)
    label = snapshot_date()
    plot_forward_curve(latest_curve("SB"), "SB (raws)", "charts/sb_curve.png", label)
    plot_forward_curve(latest_curve("QW"), "QW (whites)", "charts/qw_curve.png", label)
    plot_white_premium(white_premium_history(years=5), "charts/white_premium_5y.png", label)
    plot_seasonal(seasonal_index("SB1"), "charts/sb_seasonal.png")