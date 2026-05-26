from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import cot_reports as cot

DATA_PATH = '../../data/pull.xlsx'


# ============================================================
# PRICE DATA
# ============================================================

df_list = []
for i in range(1, 7):
    filename = f'SB{i}'
    column_name = f'SB{i}_Price'

    temp_df = pd.read_excel(DATA_PATH, sheet_name=filename, header=None, names=['Date', column_name])
    temp_df = temp_df.dropna(subset=[column_name])

    # Set Date as the index so pd.concat aligns the six series on Date
    # instead of producing six duplicate Date columns side-by-side.
    temp_df = temp_df.set_index('Date')
    df_list.append(temp_df)

df = pd.concat(df_list, axis=1)
df = df.reset_index()
df = df.sort_values(by='Date').reset_index(drop=True)

# Calendar spread: front month minus second month.
df['SB1_SB2_Spread'] = df['SB1_Price'] - df['SB2_Price']


# ============================================================
# COT DATA
# ============================================================

# Pull each year separately so one bad year doesn't kill the whole load.
cot_list = []
for year in range(2016, 2027):
    print(f"Fetching COT data for {year}...")
    try:
        yearly_df = cot.cot_year(year=year, cot_report_type="disaggregated_fut")
        cot_list.append(yearly_df)
    except Exception as e:
        print(f"Could not fetch {year}: {e}")

raw_cot_df = pd.concat(cot_list, ignore_index=True)

# Filter to ICE Sugar No. 11.
sugar_cot = raw_cot_df[raw_cot_df['Market_and_Exchange_Names'].str.contains('SUGAR NO. 11', case=False)].copy()

sugar_cot['Date'] = pd.to_datetime(sugar_cot['Report_Date_as_YYYY-MM-DD'])

# Managed Money Net = hedge-fund longs minus hedge-fund shorts.
sugar_cot['Managed_Money_Net'] = sugar_cot['M_Money_Positions_Long_All'] - sugar_cot['M_Money_Positions_Short_All']

sugar_cot_clean = sugar_cot[['Date', 'Managed_Money_Net']]

df = pd.merge(df, sugar_cot_clean, on='Date', how='left')

# COT releases Tuesday; ffill carries that value through the rest of the
# week so daily price rows have a non-null COT value to chart.
df['Managed_Money_Net'] = df['Managed_Money_Net'].ffill()


# ============================================================
# DASH APP
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
    dcc.Graph(id='my-cot-chart')
])


@app.callback(
    Output(component_id='my-price-chart', component_property='figure'),
    Output(component_id='my-spread-chart', component_property='figure'),
    Output(component_id='my-cot-chart', component_property='figure'),
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

    return fig, fig_spread, fig_cot


if __name__ == '__main__':
    app.run(debug=True)
