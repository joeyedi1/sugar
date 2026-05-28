"""Dash dashboard: Sugar No. 11 prices, calendar spread, and Managed Money Net.

Presentation layer only. Data loading lives in load_data.py / load_cot.py;
this module imports them, merges weekly COT onto the daily price panel, and
defines the layout + callback.
"""
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd

from load_data import load_prices
from load_cot import load_cot

# ============================================================
# HELPERS
# ============================================================

def pct_color(x):
    if pd.isna(x):
        return 'lightgray'
    if x < 10:
        return 'limegreen'      # crowded short -> contrarian bullish
    if x > 90:
        return 'crimson'        # crowded long
    return 'lightgray'      # mid-range, no signal

# ============================================================
# DATA
# ============================================================

prices = load_prices()
cot_data = load_cot()

df = pd.merge(prices, cot_data, on='Date', how='left')

# COT releases Tuesday; ffill carries that value through the rest of the
# week so daily price rows have a non-null COT value to chart.
df[['Managed_Money_Net', 'MM_pct']] = df[['Managed_Money_Net', 'MM_pct']].ffill()


# ============================================================
# LAYOUT
# ============================================================

app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1("COT and Price Dashboard"),
    html.Label("Select a Contract"),

    dcc.Dropdown(
        id='my-sugar-dropdown',
        options=[
            {'label': 'Front Month (SB1)', 'value': 'SB1_Price'},
            {'label': 'Second Month (SB2)', 'value': 'SB2_Price'},
            {'label': 'Third Month (SB3)', 'value': 'SB3_Price'},
            {'label': 'Fourth Month (SB4)', 'value': 'SB4_Price'},
            {'label': 'Fifth Month (SB5)', 'value': 'SB5_Price'},
            {'label': 'Sixth Month (SB6)', 'value': 'SB6_Price'}
        ],
        value='SB1_Price'
    ),

    dcc.Graph(id='my-price-chart'),
    dcc.Graph(id='my-spread-chart'),
    dcc.Graph(id='my-cot-chart'),
    dcc.Graph(id='my-pct-chart')
])


# ============================================================
# CALLBACK
# ============================================================

@app.callback(
    Output(component_id='my-price-chart', component_property='figure'),
    Output(component_id='my-spread-chart', component_property='figure'),
    Output(component_id='my-cot-chart', component_property='figure'),
    Output(component_id='my-pct-chart', component_property='figure'),
    Input(component_id='my-sugar-dropdown', component_property='value')
)
def update_graph(selected_contracts):
    fig = px.line(
        df,
        x='Date',
        y=selected_contracts,
        title="Sugar No.11 Futures Prices"
    )

    fig_spread = px.line(
        df,
        x='Date',
        y='SB1_SB2_Spread',
        title="SB1 - SB2 Calendar Spread (Physical Tightness)"
    )

    # Bind the chart's data to a single frame so the colour list cannot
    # desync from the bars when a date-range filter is added later.
    cot_df = df
    fig_cot = px.bar(
        data_frame=cot_df,
        x="Date",
        y="Managed_Money_Net",
        title="Managed Money Net Positioning (CFTC)"
    )
    fig_cot.update_traces(marker_color=['green' if val > 0 else 'red' for val in cot_df['Managed_Money_Net']])

    fig_pct = px.line(
        cot_df,
        x='Date',
        y='MM_pct',
        title="Managed Money Percentile (5y rolling; low = crowded short / contrarian-bullish)"
    )

    # signal bands: green = crowded short (<10), red = crowded long (>90)      
    fig_pct.add_hrect(y0=0,  y1=10,  fillcolor="green", opacity=0.12, line_width=0)
    fig_pct.add_hrect(y0=90, y1=100, fillcolor="red",   opacity=0.12, line_width=0)

    return fig, fig_spread, fig_cot, fig_pct


if __name__ == '__main__':
    app.run(debug=True)
