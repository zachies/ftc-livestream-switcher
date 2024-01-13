import dash_bootstrap_components as dbc
from dash_extensions.enrich import DashProxy, NoOutputTransform, html, dcc, callback, Input, Output, State, no_update, MATCH, ALL
from dash_extensions import WebSocket

from dash import DiskcacheManager

import requests, json

import components

import obsws_python as obs

import PyATEMMax
import socket

import diskcache

import time
from datetime import datetime

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = DashProxy(__name__, external_stylesheets=[dbc.themes.DARKLY], background_callback_manager=background_callback_manager, transforms=[NoOutputTransform()])
application = app.server

app.layout = dbc.Container(
    [
        # jumbotron
        dbc.Row(
            [
                dbc.Col(
                    components.Jumbotron(),
                    width=12
                ),
                dbc.Col(
                    [
                        html.P("Scorekeeping State", className="text-center"),
                        html.Div(
                            html.Div("Waiting..."),
                            id="header-scorekeeping-state",
                            className="text-center text-muted"),
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        html.P("OBS State", className="text-center"),
                        html.Div("Waiting...", id="header-obs-state", className="text-center text-muted"),
                    ],
                    width=4
                ),
                dbc.Col(
                    [
                        html.P("ATEM State", className="text-center"),
                        html.Div("Waiting...", id="header-atem-state", className="text-center text-muted"),
                    ],
                    width=4
                ),
                html.Hr(className="my-5")
            ]
        ),
        # scorekeeping row
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
        # obs row
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
                            html.Div(id="obs-ws-status")
                        ],
                        className="mb-3"
                    ),
                ]
            )
        ),
        # atem mini row
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("ATEM Mini Pro"),
                        html.Div(
                            [
                                dbc.Label("ATEM Address"),
                                dbc.InputGroup(
                                    [
                                        dbc.Button("Scan", id="atem-address-btn"),
                                        dbc.Select(id="atem-address-select", disabled=True),
                                    ]
                                ),
                                html.Div(id="atem-address-scanning"),
                                html.Div(id="atem-address-status")
                            ],
                            className="mb-3"
                        ),
                    ],
                    width=12
                ),

                dbc.Col(
                    [
                        html.Div(
                            [
                                dbc.Label("Field 1 Video Source"),
                                dbc.InputGroup(
                                    [
                                        dbc.Select(id="atem-field-1-select", options=[
                                            {"label": i, "value": i} for i in range(1, 5)
                                        ]),
                                    ]
                                )
                            ],
                            
                        ),
                    ],
                    class_name="mb-3",
                    width=6
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                dbc.Label("Field 2 Video Source"),
                                dbc.InputGroup(
                                    [
                                        dbc.Select(id="atem-field-2-select", options=[
                                            {"label": i, "value": i} for i in range(1, 5)
                                        ]),
                                    ]
                                )
                            ],
                            
                        ),
                    ],
                    class_name="mb-3",
                    width=6
                )
            ]
        ),
        # padding
        html.Div(className="mb-5")
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

    return str(message['data']), json.loads(message['data'])


@callback(
    Output("header-scorekeeping-state", "children"),
    Input({"type": "scorekeeping-state", "index": ALL}, "data"),
    [State("scorekeeping-address-input", "value"), State("scorekeeping-events-select", "value")]
)
def on_scorekeeping_state_change(state, address, event):
    if not any(state):
        return no_update
    
    # get upcoming match
    next_match = json.loads(
        requests.get(f"http://{address}/api/v1/events/{event}/matches/active/").text
    )

    state = state[0]

    return html.Div([f"Update Type: {state['updateType']}", html.Br(), f"Match Number: {state['payload']['shortName']}", html.Br(), f"Field: {state['payload']['field']}"])

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
    Output("header-obs-state", "children"),
    Input({"type": "scorekeeping-state", "index": ALL}, "data"),
    [State("obs-address-input", "value"), State("obs-port-input", "value"), State("obs-password-input", "value"), State("scorekeeping-events-select", "value")]
)
def on_scorekeeping_state_change_obs(state, address, port, pw, event):
    if not any(state) or address is None:
        return no_update
    state = state[0]

    try:
        # client is not serializable, so needs to be created each time we interact with OBS
        client = obs.ReqClient(host=address, port=port, password=pw)
    except Exception as e:
        return [html.Div(f"Could not connect to OBS", className="text-warning")]

    if state['updateType'] == "MATCH_START":
        # stop recording
        if client.get_record_status().output_active == True:
            client.stop_record()
        # set filename
        filename = f"{event}_{state['payload']['shortName']}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        client.set_profile_parameter("Output", "FilenameFormatting", filename)
        # start recording
        client.start_record()
        return [html.Div("Started recording")]
    elif state['updateType'] == "MATCH_ABORT" or state['updateType'] == "MATCH_POST" or state['updateType'] == "MATCH_COMMIT":
        time.sleep(10)
        if client.get_record_status().output_active == True:
            client.stop_record()
        return [html.Div("Stopped recording")]



@callback(
    Output("header-atem-state", "children"),
    Input({"type": "scorekeeping-state", "index": ALL}, "data"),
    [State("atem-address-select", "value"), State("atem-field-1-select", "value"), State("atem-field-2-select", "value")]
)
def on_scorekeeping_state_change_atem(state, address, field_1, field_2):
    if not any(state) or address is None:
        return no_update
    state = state[0]
    field = state['payload']['field']

    if address is None:
        return html.Div("No ATEM Mini Pro is selected.", className="text-warning")
    
    if (field == 1 and field_1 is None) or (field == 2 and field_2 is None):
        return html.Div(f"No video source is selected for field {field}", className="text-warning")

    field_map = {
        1: field_1,
        2: field_2
    }

    if state['updateType'] == "SHOW_PREVIEW":
        # switch fields
        switcher = PyATEMMax.ATEMMax()
        switcher.connect(address)
        if not switcher.waitForConnection(infinite=False, timeout=2):
            switcher.disconnect()
            return html.Div("Could not connect to ATEM Mini Pro at selected address!", className="text-danger")
        if field not in field_map:
            return html.Div(f"Could not find field {field} in mapping! Not performing a switch.", className="text-warning")
        else:
            switcher.setProgramInputVideoSource(PyATEMMax.ATEMMixEffects.mixEffect1, int(field_map[field]))
            switcher.disconnect()
            return html.Div(f"Set input video source to {int(field_map[field])}")
    
    return no_update


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


@callback(
    [Output("atem-address-select", "options"), Output("atem-address-select", "disabled"), Output("atem-address-status", "children")],
    Input("atem-address-btn", "n_clicks"),
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("atem-address-scanning", "children"), [dbc.FormText("Scanning...", class_name="text-muted")], []),
    ],
)
def on_atem_refresh_click(n_clicks):
    hostname = socket.gethostname()
    ip_addr = socket.gethostbyname(hostname)

    # assumes a netmask of 255.255.255.0
    ip_base = '.'.join(ip_addr.split('.')[0:3])

    switcher = PyATEMMax.ATEMMax()
    matches = []
    for i in range(1, 255):
        ip = f"{ip_base}.{i}"
        print(f"Testing {ip}")
        switcher.ping(ip, timeout=0.1)
        if switcher.waitForConnection():
            matches.append({"label": ip, "value": ip})
        switcher.disconnect()

    matches_found = len(matches) != 0
    if not matches_found:
        matches_text = f"No ATEM Mini Pros found after scanning from {ip_base}.1 to {ip_base}.255."
        class_name = "text-danger"
    else:
        matches_text = f"Found {len(matches)} ATEM Mini Pros."
        class_name = "text-muted"

    return matches, not matches_found, [dbc.FormText(matches_text, class_name=class_name)]


if __name__ == '__main__':
    app.run(debug=True)
