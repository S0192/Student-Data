import openpyxl
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
import flask
import plotly.io as pio
from dash.exceptions import PreventUpdate
import time

# Read the Excel file and load the "Student Data" sheet
filepath = 'AAE4B220.xlsx'
workbook = openpyxl.load_workbook(filepath)
sheet = workbook['Student Data']
page_color_background='#fff5d1'
# Get the data from the sheet
data = list(sheet.values)
header = data[0]  # Get the header row
students = data[1:]

# Create a DataFrame from the students' data
df_students = pd.DataFrame(students, columns=header)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Explicitly define the Flask server
app.config.suppress_callback_exceptions = True  # Suppress callback exceptions
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
    title = Paragraph(f"Student Report for {student[0]} {student[1]}", title_style)
    center_info = Paragraph(f"Center: {student[2]}", body_style)
    progress_heading = Paragraph("Course Progress:", heading_style)

    # Build table data
    table_data = [['Course', 'Progress']]
    table_data.extend([(header[i + 3], f"{student[i + 3]}%") for i in range(len(header) - 3)])

    # Define table style with larger padding and font size
    table_style = TableStyle(
        [
            ('BACKGROUND', (0, 0), (-1, 0), colors.steelblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 16),  # Larger padding
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('PADDING', (0, 0), (-1, -1), 10),  # Larger padding
            ('FONTSIZE', (0, 0), (-1, 0), 14),  # Larger font size
            ('FONTSIZE', (0, 1), (-1, -1), 12),  # Larger font size
        ]
    )

    # Build main table
    main_table = Table(table_data, style=table_style)

    # Add graph to PDF content
    if graph_figure:
        # Create a static image of the graph
        static_image_bytes = pio.to_image(graph_figure, format='png', width=800, height=500, scale=2)

        # Add the image to the PDF
        graph_image = Image(BytesIO(static_image_bytes), width=400, height=250)  # Adjust width and height as needed

        # Build the PDF document with the main table and graph image side by side
        content = [title, Spacer(1, 12), center_info, Spacer(1, 12), progress_heading, Spacer(1, 12)]

        # Add main table and graph image side by side
        content.append(main_table)
        content.append(graph_image)

    else:
        # Build the PDF document with only the main table
        content = [title, Spacer(1, 12), center_info, Spacer(1, 12), progress_heading, Spacer(1, 12), main_table]

    doc.build(content)
    pdf_buffer.seek(0)
    return pdf_buffer
# Function to filter out columns starting with "Course"
def filter_course_columns(header):
    return [col for col in header if col.startswith("Course")]

# Update the display_page function
@app.callback(
    [Output('page-content', 'children'),
     Output('chart-type-dropdown', 'style'),
     Output('page-heading', 'children')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
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
                                    f"{students[j][0]} {students[j][1]}",
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
                                        html.P(f"Center: {students[j][2]}"),
                                        html.P("Course Progress:"),
                                        html.Ul(
                                            [html.Li(f"{filter_course_columns(header)[i]}: {students[j][header.index(filter_course_columns(header)[i])]}%") for i in
                                             range(len(filter_course_columns(header)))]
                                        ),
                                    ]
                                ),
                            ],
                            style={"width": "15rem", "margin-bottom": "1rem", 'border': '1px solid #dee2e6'},
                        ),
                        width=12 // cards_per_row
                    )
                    for j in range(i, min(i + cards_per_row, len(students)))
                ]
            )
            for i in range(0, len(students), cards_per_row)
        ]

        return grid_of_cards, {'display': 'none'}, "Student Data Display"

    elif pathname.startswith("/student/"):
        # Display the student details and chart on the second page
        student_index = int(pathname.split("/")[-1])
        if 0 <= student_index < len(students):
            student = students[student_index]

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
                            html.Ul([html.Li(f"{filter_course_columns(header)[i]}: {student[header.index(filter_course_columns(header)[i])]}%", className="card-text",
                                             style={'font-size': '1em'}) for i in range(len(filter_course_columns(header)))],
                                    ),
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
            return "Invalid student index.", {'display': 'none'}, None

    else:
        return "404 Page Not Found", {'display': 'none'}, None

# Define the callback to update the chart based on the dropdown value and selected student
# Modify the update_chart callback function
@app.callback(
    [Output('chart', 'figure'),
     Output('download-link', 'href')],
    [Input('url', 'pathname'),
     Input('chart-type-dropdown', 'value')]
)
def update_chart(pathname, selected_chart_type):
    fig = go.Figure()

    if selected_chart_type and pathname.startswith("/student/"):
        student_index = int(pathname.split("/")[-1])
        student = df_students.iloc[student_index]

        try:
            if selected_chart_type == 'bar':
                # Bar Chart
                course_columns = filter_course_columns(header)
                fig.add_trace(go.Bar(
                    x=course_columns,
                    y=student[header.index(course_columns[0]): header.index(course_columns[-1]) + 1],
                    name=f"{student['First Name']} {student['Last Name']}",
                ))
            elif selected_chart_type == 'line':
                # Line Chart
                course_columns = filter_course_columns(header)
                fig.add_trace(go.Scatter(
                    x=course_columns,
                    y=student[header.index(course_columns[0]): header.index(course_columns[-1]) + 1],
                    mode='lines',
                    name=f"{student['First Name']} {student['Last Name']}",
                ))

            # Update the download link with the current student's PDF
            pdf_buffer = generate_pdf(student, fig)
            download_link = f"/download-report/{student_index}?chart=true"

            return fig, download_link

        except Exception as e:
            print(f"Error generating chart: {e}")
            return fig, ""

    return fig, ""

# Define the callback to handle the download link with chart option
@app.server.route("/download-report/<int:student_index>")
def download_report(student_index):
    if 0 <= student_index < len(students):
        student = students[student_index]
        include_chart = flask.request.args.get('chart') == 'true'

        try:
            # Generate the Plotly figure for the selected student
            fig = go.Figure()
            student_data = student
            fig.add_trace(go.Bar(x=header[3:], y=student_data[2:], name=f"{student_data[0]} {student_data[1]}"))

            # Generate the PDF with the selected student's details and chart
            pdf_buffer = generate_pdf(student, fig if include_chart else None)

            # Create a downloadable file
            return send_file(
                pdf_buffer,
                download_name=f"{student[0]}_{student[1]}_report.pdf",
                mimetype="application/pdf",
            )
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return "Error generating PDF. Please try again."

    else:
        return "Invalid student index."
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        dcc.Interval(
            id='interval-component',
            interval=5 * 60 * 1000,  # Update every 5 minutes (in milliseconds)
            n_intervals=0
        ),
        html.H3(id="page-heading", children="Details for ...", style={'text-align': 'center', 'margin': '0', 'padding': '20px', 'position': 'relative', 'margin-top': '0'}),
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
            dbc.Button("Download PDF", id="download-pdf-button", color="success", className="mt-3", style={'display': 'none'}),
            href="#",
            id="download-pdf-link"
        ),
    ], style={'background-color': page_background_color, 'height': '100vh', 'margin': '0', 'padding': '0', 'overflow': 'auto'})
])


# Define the callback to update the download link and make it visible
@app.callback(
    Output('download-pdf-link', 'href'),
    [Input('url', 'pathname'),
     Input('chart-type-dropdown', 'value')]
)
def update_pdf_link(pathname, selected_chart_type):
    if selected_chart_type and pathname.startswith("/student/"):
        student_index = int(pathname.split("/")[-1])
        download_link = f"/download-report/{student_index}?chart=true"
        return download_link

    raise PreventUpdate  # This prevents the callback from updating the download link on initial page load
@app.callback(
    Output('hidden-div', 'children'),
    [Input('interval-component', 'n_intervals')],
    allow_duplicate=True
)
def update_data(n_intervals):
    # Update your data here
    return time.strftime('%Y-%m-%d %H:%M:%S')

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port='8052')
