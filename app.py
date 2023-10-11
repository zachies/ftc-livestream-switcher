import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, html, dcc, callback, Input, Output, State, no_update, MATCH
from dash_extensions import WebSocket

import requests, json

import components

import obsws_python as obs

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
                    html.H2("Scorekeeping Software"),
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
                            dbc.Label("Scorekeeping Events"),
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
                            html.Div([
                                html.P("Waiting for a message...", className="text-muted"),
                            ],id="scorekeeping-ws-container")
                        ],
                        className="mb-3"
                    )
                ]
            )
        ),
        dbc.Row(
            dbc.Col(
                [
                    html.H2("OBS"),
                    html.Div(
                        [
                            dbc.Label("OBS Websocket Address"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(id="obs-address-input", debounce=True),
                                ]
                            ),
                            dbc.FormText("", id="obs-address-error"),
                        ],
                        className="mb-3"
                    ),

                    html.Div(
                        [
                            dbc.Label("OBS Websocket Port"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(id="obs-port-input", debounce=True, type="number"),
                                ]
                            ),
                            dbc.FormText("", id="obs-port-error"),
                        ],
                        className="mb-3"
                    ),

                    html.Div(
                        [
                            dbc.Label("OBS Websocket Password"),
                            dbc.InputGroup(
                                [
                                    dbc.Input(id="obs-password-input", debounce=True, type="password"),
                                ]
                            ),
                            dbc.FormText("", id="obs-password-error"),
                        ],
                        className="mb-3"
                    ),

                    html.Div(
                        [
                            dbc.Label("OBS Websocket"),
                            dcc.Store(id="obs-ws-store", data=None),
                            html.Div(id="obs-ws-status")
                        ],
                        className="mb-3"
                    ),
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
        WebSocket(id={"type": "scorekeeping-ws", "index": url}, url=url),
        dcc.Store(id={"type": "scorekeeping-state", "index": url}),
        dcc.Interval(id={"type": "scorekeeping-interval", "index": url}, interval=15000, max_intervals=-1, disabled=True)
    ]


@callback(
    [Output({"type": "scorekeeping-ws-msg", "index": MATCH}, "children"), Output({"type": "scorekeeping-state", "index": MATCH}, "data")],
    Input({"type": "scorekeeping-ws", "index": MATCH}, "message"),
)
def on_scorekeeping_ws_msg(message):
    if message is None:
        return no_update

    if message['data'] == 'pong':
        return no_update  # keepalive sent by server

    return str(message['data']), json.loads(message['data'])['updateType']


@callback(
    Output({"type": "scorekeeping-interval", "index": MATCH}, "interval"),
    Input({"type": "scorekeeping-state", "index": MATCH}, "data"),
    [State("scorekeeping-address-input", "value"), State("scorekeeping-events-select", "value")]
)
def on_scorekeeping_state_change(state, address, event):
    if state is None:
        return no_update
    
    # get upcoming match
    next_match = json.loads(
        requests.get(f"http://{address}/api/v1/events/{event}/matches/active/").text
    )
    

    if state == "MATCH_START":
        # cancel interval
        # stop recording
        # switch fields
        # set filename
        # start recording
        pass
    elif state == "MATCH_ABORT" or state == "MATCH_POST":
        # enable interval
        pass



@callback(
    Output("obs-ws-status", "children"),
    [Input("obs-address-input", "value"), Input("obs-port-input", "value"), Input("obs-password-input", "value")]
)
def on_obs_conn_input_change(address, port, pw):
    if address is None or port is None:
        return [html.P("Waiting for a connection...", className="text-muted")]
    
    try:
        # client is not serializable, so needs to be created each time we interact with OBS
        obs.ReqClient(host=address, port=port, password=pw)
    except Exception as e:
        return [html.P(f"Could not connect to OBS. Exception: {e!r}", className="text-danger")]
    
    return [html.P(f"Connected to OBS.", className="text-success")]


if __name__ == '__main__':
    app.run(debug=True)
