"""
Step 4 — Forward curves (SB, QW) + 5-year white premium.
Reads the frozen Bloomberg pull, builds three charts, saves PNGs.

The white_premium() function is written to lift straight into the
Project-1 Dash app, so keep it pure (no file I/O, no plotting).
"""

import pandas as pd
import plotly.graph_objects as go

PULL = "data/pull.xlsx"
WP_FACTOR = 22.0462          # cents/lb -> $/tonne
CHART_DATE = "21 May 2026"   # label for the snapshot curves


# ---------- data layer (pure, reusable) ----------

def white_premium(sb, qw):
    """White premium in $/tonne: QW - SB * 22.0462. Works on scalars or Series."""
    return qw - sb * WP_FACTOR


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


# ---------- chart layer ----------

def plot_forward_curve(prices, product, shape, outfile):
    fig = go.Figure(go.Scatter(
        x=list(range(1, 7)), y=prices, mode="lines+markers", line=dict(width=2)))
    fig.update_layout(
        title=f"{product} Forward Curve — {CHART_DATE} ({shape})",
        xaxis_title="Contract (1 = front)", yaxis_title="Price",
        template="plotly_white")
    fig.write_image(outfile)
    print("saved", outfile)


def plot_white_premium(df, outfile):
    latest = df["wp"].iloc[-1]
    fig = go.Figure(go.Scatter(x=df["date"], y=df["wp"], mode="lines", line=dict(width=1.5)))
    fig.update_layout(
        title=f"White Premium (QW - SB x {WP_FACTOR}) — ~${latest:.0f}/t, {CHART_DATE}",
        xaxis_title="Date", yaxis_title="White premium ($/tonne)",
        template="plotly_white")
    fig.write_image(outfile)
    print("saved", outfile)


# ---------- run (only when executed directly, not on import) ----------

if __name__ == "__main__":
    plot_forward_curve(latest_curve("SB"), "SB (raws)", "contango", "charts/sb_curve.png")
    plot_forward_curve(latest_curve("QW"), "QW (whites)", "mild contango", "charts/qw_curve.png")
    plot_white_premium(white_premium_history(years=5), "charts/white_premium_5y.png")