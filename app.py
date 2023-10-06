from dash import Dash, html

app = Dash(__name__)
application = app.server

app.layout = html.Div([
    html.Div(children='Hello World')
])

if __name__ == '__main__':
    app.run(debug=True)