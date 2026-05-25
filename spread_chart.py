"""
Calendar-spread analysis for SB (ICE 11).
- Loads frozen leg pairs from nv_spread_frozen.xlsx
- Computes deferred - nearby spreads (pure, reusable -> dashboard)
- N/V seasonal overlay aligned by days-to-nearby(July)-expiry
- Current-curve read: today's N/V, V/H, H/K

Pure functions (load_spread_pair, season_spread) carry no plotting/IO assumptions
so they lift into the Dash app like white_premium().
"""

import datetime as dt
import pandas as pd
import plotly.graph_objects as go

XLSX = "data/nv_spread_frozen.xlsx"


# ---------- data layer (pure, reusable) ----------

def load_spread_pair(sheet, path=XLSX):
    """Read a 4-col sheet [Date, nearby, Date, deferred] -> merged on date.
    Returns DataFrame[date, nearby, deferred, spread] where spread = deferred - nearby."""
    raw = pd.read_excel(path, sheet_name=sheet, header=0)
    nearby = raw.iloc[:, [0, 1]].dropna()
    nearby.columns = ["date", "nearby"]
    deferred = raw.iloc[:, [2, 3]].dropna()
    deferred.columns = ["date", "deferred"]
    m = pd.merge(nearby, deferred, on="date").sort_values("date")
    m["spread"] = m["deferred"] - m["nearby"]          # deferred - nearby (contango +)
    return m.reset_index(drop=True)


def season_spread(sheet, expiry_year, nearby_expiry=(6, 30)):
    """N/V spread for one season, with days-to-nearby-expiry for seasonal alignment."""
    df = load_spread_pair(sheet)
    exp = pd.Timestamp(year=expiry_year, month=nearby_expiry[0], day=nearby_expiry[1])
    df["days_to_exp"] = (exp - df["date"]).dt.days
    return df


# ---------- current-curve read ----------

def latest(sheet, col_idx):
    """Latest non-null price from a sheet column (1=nearby, 3=deferred)."""
    raw = pd.read_excel(XLSX, sheet_name=sheet, header=0).iloc[:, [col_idx - 1, col_idx]].dropna()
    raw.columns = ["date", "px"]
    row = raw.sort_values("date").iloc[-1]
    return row["date"], row["px"]


def current_curve():
    _, n26 = latest("NV26", 1)
    _, v26 = latest("NV26", 3)
    _, h27 = latest("VH_HK27", 1)
    _, k27 = latest("VH_HK27", 3)
    return {
        "N/V (Jul26-Oct26)": v26 - n26,
        "V/H (Oct26-Mar27)": h27 - v26,
        "H/K (Mar27-May27)": k27 - h27,
    }, {"N26": n26, "V26": v26, "H27": h27, "K27": k27}


# ---------- charts ----------

SEASONS = {"NV26": 2026, "NV25": 2025, "NV24": 2024, "NV23": 2023}


def plot_seasonal_overlay(outfile):
    fig = go.Figure()
    for sheet, yr in SEASONS.items():
        df = season_spread(sheet, yr)
        df = df[(df["days_to_exp"] >= 0) & (df["days_to_exp"] <= 420)]
        fig.add_trace(go.Scatter(x=df["days_to_exp"], y=df["spread"],
                                 mode="lines", name=str(yr), line=dict(width=2 if yr == 2026 else 1.3)))
    # today marker on the 2026 line
    cur = season_spread("NV26", 2026)
    last = cur.sort_values("date").iloc[-1]
    fig.add_trace(go.Scatter(x=[last["days_to_exp"]], y=[last["spread"]], mode="markers+text",
                             marker=dict(size=10, color="black"), text=["today"],
                             textposition="top center", showlegend=False))
    fig.update_layout(
        title="SB N/V calendar spread (Oct - Jul) - seasonal overlay",
        xaxis_title="Days to July (nearby) expiry  -  expiry at right",
        yaxis_title="Spread (c/lb), deferred - nearby",
        template="plotly_white")
    fig.update_xaxes(autorange="reversed")
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.write_image(outfile)
    print("saved", outfile)


def plot_calendar_timeseries(outfile):
    fig = go.Figure()
    for sheet, yr in SEASONS.items():
        df = load_spread_pair(sheet)
        fig.add_trace(go.Scatter(x=df["date"], y=df["spread"], mode="lines",
                                 name=str(yr), line=dict(width=1.4)))
    fig.update_layout(
        title="SB N/V spread by calendar date (each season's life)",
        xaxis_title="Date", yaxis_title="Spread (c/lb)",
        template="plotly_white")
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.write_image(outfile)
    print("saved", outfile)


if __name__ == "__main__":
    spreads, legs = current_curve()
    print("Current legs:", {k: round(v, 2) for k, v in legs.items()})
    print("Current curve spreads (c/lb):")
    for k, v in spreads.items():
        print(f"  {k}: {v:+.2f}")
    plot_seasonal_overlay("charts/sb_nv_seasonal_overlay.png")
    plot_calendar_timeseries("charts/sb_nv_calendar.png")