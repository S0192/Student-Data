import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
import sqlite3
import os
import time

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Student Data Entry Form"
app.config['suppress_callback_exceptions'] = True  # Suppress callback exceptions warning

# Define background color and card header color
card_header_color = '#6873af'
page_background_color = '#fff5d1'

# Function to load center options from SQLite
def load_center_options():
    try:
        conn = sqlite3.connect("graph_data.db", isolation_level=None)
        cursor = conn.cursor()

        # Fetch centers from the Center_Data table
        cursor.execute("SELECT DISTINCT Center FROM Center_Data")
        centers = cursor.fetchall()
        conn.close()

        # Return valid options
        return [{"label": center[0], "value": center[0]} for center in centers]
    except Exception as e:
        # Return an error label if something goes wrong
        return [{"label": f"Error loading centers: {str(e)}", "value": None}]
    except Exception as e:
        return [{"label": f"Error loading centers: {str(e)}", "value": None}]

# Function to load course fields (columns) from SQLite
def load_course_fields():
    try:
        conn = sqlite3.connect("graph_data.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(Student_Data)")  # Get table info for Student_Data
        columns = cursor.fetchall()
        conn.close()
        return [col[1] for col in columns if col[1].startswith("Course")]  # Only return "Course" fields
    except Exception as e:
        print(f"Error loading centers: {e}")  # Debug statement
        return [{"label": f"Error: {e}", "value": None}]

# Function to update dropdown fields dynamically
def update_fields():
    course_fields = load_course_fields()
    children = []
    for field in course_fields:
        children.append(
            dbc.Col(
                [
                    dbc.Label(field),
                    dcc.Dropdown(
                        id=field.lower().replace(" ", "-"),
                        options=[{"label": f"{i}%", "value": i} for i in range(0, 101)] + [{"label": "N.A", "value": "N.A"}],
                        className="dropdown",
                    ),
                ],
                width=6,
            )
        )
    return children

# Callback for handling data entry and updating the database
@app.callback(
    Output("message", "children"),
    [Input("submit-button", "n_clicks")],
    [
        State("first-name", "value"),
        State("last-name", "value"),
        State("center", "value"),
        *[State(field.lower().replace(" ", "-"), "value") for field in load_course_fields()]
    ],
)
def enter_data(n_clicks, first_name, last_name, center, *course_values):
    if n_clicks is None or n_clicks <= 0:
        return ""  # No action if no button click

    if not (first_name and last_name):
        return "First name and last name are required."

    try:
        conn = sqlite3.connect("graph_data.db")
        cursor = conn.cursor()

        # Check if the student already exists
        cursor.execute(
            "SELECT * FROM Student_Data WHERE `First Name` = ? AND `Last Name` = ?",
            (first_name, last_name),
        )
        existing_student = cursor.fetchone()

        course_fields = load_course_fields()

        # Update or Insert Data
        if existing_student:
            # Update existing record
            for i, field in enumerate(course_fields):
                cursor.execute(
                    f"UPDATE Student_Data SET `{field}` = ? WHERE `First Name` = ? AND `Last Name` = ?",
                    (course_values[i], first_name, last_name),
                )
            cursor.execute(
                "UPDATE Student_Data SET Center = ? WHERE `First Name` = ? AND `Last Name` = ?",
                (center, first_name, last_name),
            )
            message = "Data updated successfully!"
        else:
            # Insert new record
            placeholders = ", ".join(["?"] * (3 + len(course_fields)))
            column_names = "`First Name`, `Last Name`, Center, " + ", ".join([f"`{field}`" for field in course_fields])
            query = f"INSERT INTO Student_Data ({column_names}) VALUES ({placeholders})"
            cursor.execute(query, (first_name, last_name, center, *course_values))
            message = "Data saved successfully!"

        conn.commit()
        conn.close()
        return message
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Callback to update dropdown options and fields periodically
@app.callback(
    Output('hidden-div', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_data(n_intervals):
    load_center_options()
    update_fields()
    return time.strftime('%Y-%m-%d %H:%M:%S')

# Define the app layout
app.layout = html.Div([
    html.Div(
        id="main-content",
        style={'background-color': page_background_color, 'height': '100vh', 'margin': '0'}
    ),
    dcc.Interval(id='interval-component', interval=5*60*1000, n_intervals=0),  # Update every 5 minutes
    html.Div(id='hidden-div', style={'display': 'none'})
])

# Update main content with the form layout
@app.callback(
    Output("main-content", "children"),
    [Input('hidden-div', 'children')]
)
def update_main_content(_):
    return dbc.Card(
        children=[
            dbc.CardHeader(
                html.H4("Data Entry Form", className="card-title"),
                style={'background-color': card_header_color, 'color': 'white'}
            ),
            dbc.CardBody(
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("First Name"),
                                    dbc.Input(id="first-name", type="text", className="input-field"),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Last Name"),
                                    dbc.Input(id="last-name", type="text", className="input-field"),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Center"),
                                    dcc.Dropdown(
                                        id="center",
                                        options=load_center_options(),
                                        className="dropdown",
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        update_fields(),
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Enter Data",
                        id="submit-button",
                        n_clicks=0,
                        className="mt-3",
                        style={'background-color': card_header_color, 'color': 'white'}
                    ),
                    html.Div(id="message", className="mt-3"),
                ],
            ),
        ],
        style={
            'background-color': 'white',
            'width': '400px',
            'margin': 'auto',
            'position': 'absolute',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)'
        }
    )

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8051)

