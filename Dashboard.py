import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import sqlite3


class DashboardComponent:
    def __init__(self, db_file):
        self.db_file = db_file

    def fetch_data(self, query, params=()):
        """Fetch data from the SQLite database."""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
        return data, columns


class BarGraph(DashboardComponent):
    def update(self, course, centers):
        if not course:
            raise dash.exceptions.PreventUpdate

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


class PieLineCharts(DashboardComponent):
    def update(self, centers):
        # Fetch data for selected centers
        query = "SELECT Center, `Course A`, `Course B`, `Course C`, `Course D`, `Course E` FROM Center_Data"
        if centers:
            placeholders = ', '.join(['?'] * len(centers))
            query += f" WHERE Center IN ({placeholders})"
            data, columns = self.fetch_data(query, tuple(centers))
        else:
            data, columns = self.fetch_data(query)

        if not data:
            return px.pie(title="No Data Available"), px.line(title="No Data Available")

        # Pie Chart
        df_pie = {row[0]: sum(row[1:]) for row in data}
        pie_fig = px.pie(
            names=list(df_pie.keys()),
            values=list(df_pie.values()),
            title="Total Progress by Center",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        pie_fig.update_traces(marker=dict(line=dict(color='#ffffff', width=2)))

        # Line Chart
        centers = [row[0] for row in data]
        line_data = {col: [row[i + 1] for row in data] for i, col in enumerate(columns[1:])}
        line_fig = px.line(
            x=centers,
            y=[line_data[col] for col in columns[1:]],
            title="Progress Over Centers",
            labels={"x": "Center", "y": "Progress"},
            markers=True,
        )
        for i, col in enumerate(columns[1:]):
            line_fig.data[i].name = col  # Set legend names

        return pie_fig, line_fig


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
        return [{"label": col, "value": col} for col in course_columns]


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
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    width=6,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(
                                                    html.H6("Pie Chart", style={"color": "#ffffff", "font-weight": "bold"}),
                                                    style={"background-color": "#6873af"},
                                                ),
                                                dbc.CardBody(dcc.Graph(id="pie-chart")),
                                            ],
                                            style={"background-color": "#ffffff", "margin": "10px"},
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    width=6,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(
                                                    html.H6("Line Chart", style={"color": "#ffffff", "font-weight": "bold"}),
                                                    style={"background-color": "#6873af"},
                                                ),
                                                dbc.CardBody(dcc.Graph(id="line-chart")),
                                            ],
                                            style={"background-color": "#ffffff", "margin": "10px"},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
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
        self.pie_line_charts = PieLineCharts(db_file)

        self.app.callback(Output("graph", "figure"), [Input("Course_dropdown", "value"), Input("center-checklist", "value")])(self.bar_graph.update)
        self.app.callback(Output("Course_dropdown", "options"), [Input("center-checklist", "value")])(self.dropdown.update)
        self.app.callback(
            Output("center-checklist", "options"),
            Input("Course_dropdown", "value"),
        )(self.update_center_checklist)

        self.app.callback(
            [Output("pie-chart", "figure"), Output("line-chart", "figure")],
            [Input("center-checklist", "value")],
        )(self.pie_line_charts.update)

        def update_center_checklist(self, _):
            """Fetches and updates the checklist with all available centers from the database."""
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT Center FROM Center_Data")
                centers = cursor.fetchall()
            return [{"label": center[0], "value": center[0]} for center in centers]

    def setup_layout(self):
        self.app.layout = self.layout.container

    def update_center_checklist(self, _):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Center FROM Center_Data")
            centers = cursor.fetchall()
        return [{"label": center[0], "value": center[0]} for center in centers]

    def run_app(self):
        if __name__ == "__main__":
            self.app.run_server(debug=True, port=8050)


# Run the app
dashboard = DashboardApp()
dashboard.run_app()
