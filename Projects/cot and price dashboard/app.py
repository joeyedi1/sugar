from dash import Dash, html, dcc

# 1. Start the Engine
app = Dash(__name__)

# 2. Define the Layout (The Frontend)
app.layout = html.Div(children=[

    # A title for the app
    html.H1("COT and Price Dashboard"),

    # A text label
    html.Label("Select a Contract"),

    # An interactive dropdown
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
        value='SB1_Price' # This is the default selection           
    )


])

# 3. Run the App
if __name__ == '__main__':
    app.run(debug=True)