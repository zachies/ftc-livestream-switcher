import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, html, dcc, callback, Input, Output, State, no_update, MATCH
from dash_extensions import WebSocket

import requests, json

import components

app = DashProxy(__name__, external_stylesheets=[dbc.themes.DARKLY])
application = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                components.Jumbotron()
            )
        ),
        dbc.Row(
            dbc.Col(
                [
                    html.Div(
                        [
                            dbc.Label("Scorekeeping Address"),
                            dbc.InputGroup(
                                [
                                    dbc.Button("Refresh", id="scorekeeping-address-btn"),
                                    dbc.Input(id="scorekeeping-address-input", debounce=True),
                                ]
                            ),
                            dbc.FormText("", id="scorekeeping-address-error"),
                        ],
                        className="mb-3"
                    ),
                    
                    html.Div(
                        [
                            dbc.Label("Events"),
                            dbc.InputGroup(
                                [
                                    dbc.Select(id="scorekeeping-events-select"),
                                ]
                            ),
                            dbc.FormText("", id="scorekeeping-events-error"),
                        ],
                        className="mb-3"
                    ),

                    html.Div(
                        [
                            dbc.Label("Scorekeeping Websocket"),
                            html.Div(id="scorekeeping-ws-container")
                        ],
                        className="mb-3"
                    )
                ]
            )
        )
    ]
)


@callback(
    [Output("scorekeeping-events-select", "options"), Output("scorekeeping-address-error", "children")],
    [Input("scorekeeping-address-btn", "n_clicks"), Input("scorekeeping-address-input", "value")]
)
def on_scorekeeping_address_btn_click(n_clicks, address):
    if address is None:
        return no_update

    try:
        response = requests.get(f"http://{address}/api/v1/events")
    except Exception as e:
        return [], f"Could not find the scorekeeping software at the specified address. Exception: {e!r}"  # show error
    
    if response.status_code != 200:
        return [], f"Received error status code. Message: {response.status_code} {response.reason}"

    msg = json.loads(response.text)
    return [{"label": code, "value": code} for code in msg['eventCodes']], ""


@callback(
    Output("scorekeeping-ws-container", "children"),
    Input("scorekeeping-events-select", "value"),
    State("scorekeeping-address-input", "value")
)
def on_scorekeeping_event_select(event, address):
    if address is None or event is None:
        return no_update

    url = f"ws://{address}/api/v2/stream/?code={event}"
    return [
        html.P("Waiting for a message...", id={"type": "scorekeeping-ws-msg", "index": url}, className="text-muted"),
        WebSocket(id={"type": "scorekeeping-ws", "index": url}, url=url)
    ]


@callback(
    Output({"type": "scorekeeping-ws-msg", "index": MATCH}, "children"),
    Input({"type": "scorekeeping-ws", "index": MATCH}, "message"),
)
def on_scorekeeping_ws_msg(message):
    if message is None:
        return no_update

    if message['data'] == 'pong':
        return no_update  # keepalive sent by server

    return str(message['data'])


if __name__ == '__main__':
    app.run(debug=True)
