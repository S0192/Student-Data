import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import sqlite3
from dash.exceptions import PreventUpdate


class DashboardComponent:
    def __init__(self, db_file):
        self.db_file = db_file

    def fetch_data(self, query, params=()):
        """Fetch data from the database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
        return data, columns


class BarGraph(DashboardComponent):
    def update(self, course, centers):
        if not course:
            raise PreventUpdate

        query = f"SELECT Center, `{course}` FROM Center_Data"
        if centers:
            placeholders = ', '.join(['?'] * len(centers))
            query += f" WHERE Center IN ({placeholders})"
            data, columns = self.fetch_data(query, tuple(centers))
        else:
            data, columns = self.fetch_data(query)

        if not data:
            return px.bar(title="No Data Available")

        centers, values = zip(*data)
        fig = px.bar(
            x=centers,
            y=values,
            labels={"x": "Center", "y": course},
            title=f"{course} Progress by Center",
            color=values,
            color_continuous_scale=px.colors.diverging.Armyrose,
        )
        return fig


class DropdownComponent(DashboardComponent):
    def update(self, centers):
        query = "SELECT * FROM Center_Data"
        if centers:
            placeholders = ', '.join(['?'] * len(centers))
            query += f" WHERE Center IN ({placeholders})"
            data, columns = self.fetch_data(query, tuple(centers))
        else:
            data, columns = self.fetch_data(query)

        course_columns = [col for col in columns if col != "Center"]
        course_options = [{"label": col, "value": col} for col in course_columns]
        return course_options


class LayoutComponent:
    def __init__(self, db_file):
        self.db_file = db_file
        self.container = dbc.Container(
            fluid=True,
            style={"background-color": "#fff5d1", "color": "#000000", "font-family": "Georgia"},
            children=[
                html.H2("Dashboard", style={"text-align": "center", "padding-top": "20px"}),
                dbc.Container(
                    fluid=True,
                    children=[
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    width=8,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(
                                                    html.H6("Bar Graph", style={"color": "#ffffff", "font-weight": "bold"}),
                                                    style={"background-color": "#6873af"},
                                                ),
                                                dbc.CardBody(dcc.Graph(id="graph")),
                                            ],
                                            style={"background-color": "#ffffff", "margin": "10px"},
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    width=4,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(
                                                    html.H6("Center Name", style={"color": "#ffffff", "font-weight": "bold"}),
                                                    style={"background-color": "#6873af"},
                                                ),
                                                dbc.CardBody(
                                                    dcc.Checklist(
                                                        id="center-checklist",
                                                        options=[],
                                                        value=[],
                                                        labelStyle={"display": "block"},
                                                        style={"height": "150px", "overflow": "auto"},
                                                    ),
                                                ),
                                            ],
                                            style={"background-color": "#ffffff", "margin": "10px"},
                                        ),
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(
                                                    html.H6("Course Selection", style={"color": "#ffffff", "font-weight": "bold"}),
                                                    style={"background-color": "#6873af"},
                                                ),
                                                dbc.CardBody(
                                                    dcc.Dropdown(
                                                        id="Course_dropdown",
                                                        options=[],
                                                        value=None,
                                                        placeholder="Select a course",
                                                        clearable=False,
                                                        style={"width": "100%"},
                                                    ),
                                                ),
                                            ],
                                            style={"background-color": "#ffffff", "margin": "10px"},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                dcc.Interval(id="interval-component", interval=5 * 60 * 1000, n_intervals=0),
            ],
        )


class DashboardApp:
    def __init__(self, db_file="graph_data.db"):
        self.db_file = db_file
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.layout = LayoutComponent(db_file)
        self.setup_layout()

        self.bar_graph = BarGraph(db_file)
        self.dropdown = DropdownComponent(db_file)

        self.app.callback(Output("graph", "figure"), [Input("Course_dropdown", "value"), Input("center-checklist", "value")])(self.bar_graph.update)
        self.app.callback(Output("Course_dropdown", "options"), [Input("center-checklist", "value")])(self.dropdown.update)
        self.app.callback(Output("center-checklist", "options"), Input("interval-component", "n_intervals"))(self.update_center_checklist)

    def setup_layout(self):
        self.app.layout = self.layout.container

    def update_center_checklist(self, _):
        """Update the Center Checklist with fresh data."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Center FROM Center_Data")
            centers = cursor.fetchall()

        return [{"label": center[0], "value": center[0]} for center in centers]

    def run_app(self):
        if __name__ == "__main__":
            self.app.run_server(debug=True, port=8050)


# Run the application
dashboard = DashboardApp()
dashboard.run_app()
