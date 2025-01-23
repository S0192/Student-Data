import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import sqlite3
import plotly.io as pio
from dash.exceptions import PreventUpdate
import time

# Database connection (Replace with your actual database connection)
def fetch_student_data():
    conn = sqlite3.connect('graph_data.db')  # Replace with your DB connection details
    query = "SELECT * FROM Student_Data"
    df_students = pd.read_sql(query, conn)
    conn.close()
    return df_students

df_students = fetch_student_data()

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.config.suppress_callback_exceptions = True
page_background_color = '#fff5d1'

def generate_pdf(student, graph_figure):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        spaceAfter=12,
        textColor=colors.cornflowerblue,
    )
    heading_style = ParagraphStyle(
        'Heading1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=6,
        textColor=colors.cornflowerblue,
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=12,
        spaceAfter=6,
        textColor=colors.black,
    )
    # Build content
    title = Paragraph(f"Student Report for {student['First Name']} {student['Last Name']}", title_style)
    center_info = Paragraph(f"Center: {student['Center']}", body_style)
    progress_heading = Paragraph("Course Progress:", heading_style)

    # Build table data
    table_data = [['Course', 'Progress']]
    for course in ['Course A', 'Course B', 'Course C', 'Course D', 'Course E']:
        table_data.append([course, f"{student[course]}%"])

    # Define table style with larger padding and font size
    table_style = TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.steelblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 16),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
        ]
    )

    main_table = Table(table_data, style=table_style)

    if graph_figure:
        # Create a static image of the graph
        static_image_bytes = pio.to_image(graph_figure, format='png', width=800, height=500, scale=2)
        graph_image = Image(BytesIO(static_image_bytes), width=400, height=250)

        content = [title, Spacer(1, 12), center_info, Spacer(1, 12), progress_heading, Spacer(1, 12)]
        content.append(main_table)
        content.append(graph_image)
    else:
        content = [title, Spacer(1, 12), center_info, Spacer(1, 12), progress_heading, Spacer(1, 12), main_table]

    doc.build(content)
    pdf_buffer.seek(0)
    return pdf_buffer

@app.callback(
    [Output('page-content', 'children'),
     Output('chart-type-dropdown', 'style'),
     Output('page-heading', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == "/":
        cards_per_row = 5
        grid_of_cards = [
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.A(
                                    f"{df_students.iloc[j]['First Name']} {df_students.iloc[j]['Last Name']}",
                                    href=f"/student/{j}",
                                    id={"type": "student-link", "index": j},
                                    style={"color": "inherit", "text-decoration": "none", "background-color":"#6873af"},
                                ),
                                style={
                                    "background-color":"#6873af",
                                    "color":"white"
                                }),
                                dbc.CardBody(
                                    [
                                        html.P(f"Center: {df_students.iloc[j]['Center']}"),
                                        html.P("Course Progress:"),
                                        html.Ul(
                                            [html.Li(f"{course}: {df_students.iloc[j][course]}%") for course in
                                             ['Course A', 'Course B', 'Course C', 'Course D', 'Course E']]
                                        ),
                                    ]
                                ),
                            ],
                            style={"width": "15rem", "margin-bottom": "1rem", 'border': '1px solid #dee2e6'},
                        ),
                        width=12 // cards_per_row
                    )
                    for j in range(i, min(i + cards_per_row, len(df_students)))
                ]
            )
            for i in range(0, len(df_students), cards_per_row)
        ]

        return grid_of_cards, {'display': 'none'}, "Student Data Display"

    elif pathname.startswith("/student/"):
        student_index = int(pathname.split("/")[-1])
        if 0 <= student_index < len(df_students):
            student = df_students.iloc[student_index]

            student_card = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(f"{student['First Name']} {student['Last Name']}", className="card-title", style={'font-size': '1.2em'}),
                        style={"background-color": "#6873af", "color": "white"}
                    ),
                    dbc.CardBody(
                        [
                            html.P(f"Center: {student['Center']}", className="card-text", style={'font-size': '1em'}),
                            html.P("Course Progress:", className="card-text", style={'font-size': '1em'}),
                            html.Ul([html.Li(f"{course}: {student[course]}%", className="card-text", style={'font-size': '1em'}) for course in ['Course A', 'Course B', 'Course C', 'Course D', 'Course E']]),
                            html.A(
                                dbc.Button("Download Report", id="download-report-button", color="success", className="mt-3"),
                                href=f"/download-report/{student_index}",
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
                    html.H3(f"Details for {student['First Name']} {student['Last Name']}", style={'text-align': 'center', 'margin-bottom': '20px'}),
                    dbc.Card(
                        children=[
                            dbc.CardHeader(html.H6("Graph", style={'color': '#ffffff', 'padding': '10px'}), style={'border': 'none', 'background-color': '#6873af'}),
                            dbc.CardBody(
                                dcc.Graph(id='chart', style={'width': '100%', 'background-color': '#ffffff'}),
                            ),
                        ],
                    ),
                    html.Div(style={'padding-bottom': '10px'}),
                    dcc.Dropdown(
                        id="chart-type-dropdown",
                        options=[{'label': 'Bar Chart', 'value': 'bar'}, {'label': 'Line Chart', 'value': 'line'}],
                        value='bar',
                        clearable=False,
                        style={'width': '200px', 'color': 'black'}
                    ),
                ]
            )

            return student_card, {
                'display': 'block'}, f"Student Details: {student['First Name']} {student['Last Name']}"

            # If the path doesn't match any valid student or home route
        raise PreventUpdate

        @app.callback(
            Output('chart', 'figure'),
            [Input('chart-type-dropdown', 'value'),
             Input('url', 'pathname')]
        )
        def update_chart(chart_type, pathname):
            student_index = int(pathname.split("/")[-1])
            student = df_students.iloc[student_index]

            # Chart data for the student's courses
            courses = ['Course A', 'Course B', 'Course C', 'Course D', 'Course E']
            progress = [student[course] for course in courses]

            if chart_type == 'bar':
                fig = go.Figure(data=[go.Bar(x=courses, y=progress)])
            else:
                fig = go.Figure(data=[go.Scatter(x=courses, y=progress, mode='lines+markers')])

            fig.update_layout(
                title="Course Progress",
                xaxis_title="Courses",
                yaxis_title="Progress (%)",
                plot_bgcolor='rgba(0, 0, 0, 0)',
                font=dict(color="black")
            )

            return fig

        @app.callback(
            Output('download-link', 'href'),
            [Input('download-report-button', 'n_clicks')],
            [Input('url', 'pathname')]
        )
        def generate_report(n_clicks, pathname):
            if not n_clicks:
                raise PreventUpdate

            student_index = int(pathname.split("/")[-1])
            student = df_students.iloc[student_index]

            # Generate the report PDF
            pdf_buffer = generate_pdf(student, None)

            # Create a downloadable link for the PDF
            return f"data:application/pdf;base64,{pdf_buffer.getvalue().encode('base64')}"

        if __name__ == "__main__":
            app.run_server(debug=True)

