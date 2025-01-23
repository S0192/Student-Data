import sqlite3
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import flask
import plotly.io as pio
from dash.exceptions import PreventUpdate
import time

# SQLite Database connection and cursor
conn = sqlite3.connect("graph_data.db", check_same_thread=False)
cursor = conn.cursor()

# Fetch all student data and headers
def fetch_students():
    cursor.execute("SELECT * FROM Student_Data")
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]
    return headers, rows

header, students = fetch_students()
page_color_background = '#fff5d1'

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.config.suppress_callback_exceptions = True
page_background_color = '#fff5d1'

# Define layout before running the server
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        dcc.Interval(
            id='interval-component',
            interval=5 * 60 * 1000,  # Update every 5 minutes (in milliseconds)
            n_intervals=0
        ),
        html.H3(
            id="page-heading",
            children="Details for ...",
            style={'text-align': 'center', 'margin': '0', 'padding': '20px', 'position': 'relative', 'margin-top': '0'}
        ),
        html.Div(id="page-content", className="row"),

        # Dropdown for chart type
        dcc.Dropdown(
            id='chart-type-dropdown',
            options=[
                {'label': 'Bar Chart', 'value': 'bar'},
                {'label': 'Line Chart', 'value': 'line'},
            ],
            value='bar',
            clearable=False,
            style={'display': 'none'}
        ),
        html.A(
            dbc.Button(
                "Download PDF",
                id="download-pdf-button",
                color="success",
                className="mt-3",
                style={'display': 'none'}
            ),
            href="#",
            id="download-pdf-link"
        ),
    ], style={'background-color': page_background_color, 'height': '100vh', 'margin': '0', 'padding': '0', 'overflow': 'auto'})
])

# Helper function to filter columns starting with "Course"
def filter_course_columns(headers):
    return [col for col in headers if col.startswith("Course")]

# Define callback to update the page layout
@app.callback(
    [Output('page-content', 'children'),
     Output('chart-type-dropdown', 'style'),
     Output('page-heading', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    header, students = fetch_students()
    if pathname == "/":
        # Display the grid of cards on the first page
        cards_per_row = 5
        grid_of_cards = [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.A(
                                    f"{student[0]} {student[1]}",
                                    href=f"/student/{student[-1]}",
                                    id={"type": "student-link", "index": student[-1]},
                                    style={"color": "inherit", "text-decoration": "none", "background-color": "#6873af"},
                                ),
                                style={
                                    "background-color": "#6873af",
                                    "color": "white"
                                }),
                                dbc.CardBody(
                                    [
                                        html.P(f"Center: {student[2]}"),
                                        html.P("Course Progress:"),
                                        html.Ul(
                                            [html.Li(f"{filter_course_columns(header)[i]}: {student[3 + i]}%") for i in
                                             range(len(filter_course_columns(header)))]
                                        ),
                                    ]
                                ),
                            ],
                            style={"width": "15rem", "margin-bottom": "1rem", 'border': '1px solid #dee2e6'},
                        ),
                        width=12 // cards_per_row
                    )
                    for student in students
                ]
            )
        ]

        return grid_of_cards, {'display': 'none'}, "Student Data Display"

    elif pathname.startswith("/student/"):
        # Display the student details and chart on the second page
        student_id = int(pathname.split("/")[-1])
        cursor.execute("SELECT * FROM Student_Data WHERE ID = ?", (student_id,))
        student = cursor.fetchone()
        if student:
            student_card = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(f"{student[0]} {student[1]}", className="card-title", style={'font-size': '1.2em'}),
                        style={
                            "background-color": "#6873af",
                            "color": "white"
                        }
                    ),
                    dbc.CardBody(
                        [
                            html.P(f"Center: {student[2]}", className="card-text", style={'font-size': '1em'}),
                            html.P("Course Progress:", className="card-text", style={'font-size': '1em'}),
                            html.Ul([html.Li(f"{filter_course_columns(header)[i]}: {student[3 + i]}%", className="card-text",
                                             style={'font-size': '1em'}) for i in range(len(filter_course_columns(header)))],
                                    ),
                            html.A(
                                dbc.Button("Download Report", id="download-report-button", color="success", className="mt-3"),
                                href=f"/download-report/{student_id}",
                                id="download-link"
                            ),
                        ]
                    ),
                ],
                style={"width": "15rem", "margin-bottom": "1rem", 'border': '1px solid #dee2e6'},
            )

            chart_col = dbc.Col(
                id='chart-col',
                children=[
                    html.H3(f"Details for {student[0]} {student[1]}",
                            style={'text-align': 'center', 'margin-bottom': '20px'}),
                    dbc.Card(
                        children=[
                            dbc.CardHeader(html.H6("Graph", style={'color': '#ffffff',
                                                                   'padding': '10px'}),
                                           style={'border': 'none', 'border-radius': '0', 'background-color': '#6873af'}),
                            dbc.CardBody(
                                dcc.Graph(id='chart', style={'width': '100%', 'background-color': '#ffffff'}),
                            ),
                        ],
                    ),
                    html.Div(style={'padding-bottom': '10px'}),
                    # Added a div with padding to create space below the graph
                    dcc.Dropdown(
                        id="chart-type-dropdown",
                        options=[
                            {'label': 'Bar Chart', 'value': 'bar'},
                            {'label': 'Line Chart', 'value': 'line'},
                        ],
                        value='bar',
                        clearable=False,
                        style={'width': '200px', 'color': '#000000', 'margin': 'auto', 'margin-top': '10px',
                               'margin-left': '100px'},
                        # Centered dropdown with top margin
                    ),
                ],
                width=9,
                style={'margin': '10px'}  # Add margin to the entire dbc.Col
            )

            student_col = dbc.Col(
                id='student-card-col',
                children=[student_card],
                width=2
            )

            return [chart_col, student_col], {'width': '50%', 'font-size': '1em', 'display': 'block'}, None

        else:
            return "Invalid student ID.", {'display': 'none'}, None

    else:
        return "404 Page Not Found", {'display': 'none'}, None

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
