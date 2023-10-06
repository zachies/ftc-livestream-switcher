from dash import html
import dash_bootstrap_components as dbc

def get_jumbotron():
    return html.Div(
        [
            html.H1("AZFTC Livestream Switcher", className="display-3"),
            html.P(
                "This tool configures livestreaming for Arizona FIRST Tech Challenge events.",
                className="lead",
            ),
            html.Hr(className="my-2")
        ],
        className="py-3"
    )