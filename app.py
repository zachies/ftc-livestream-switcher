from dash import Dash, html
import dash_bootstrap_components as dbc

import components

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
application = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                components.Jumbotron()
            )
        )
    ]
)

if __name__ == '__main__':
    app.run(debug=True)