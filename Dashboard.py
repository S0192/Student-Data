import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from collections import deque
from dash.exceptions import PreventUpdate
import time

class DashboardComponent:
    def __init__(self, df):
        self.df = df

    def update(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement the 'update' method.")

class BarGraph(DashboardComponent):
    def update(self, course, centers):
        if course is None:
            return px.bar()

        filtered_df = self.df[self.df['Number_of_Students'].notnull()]

        if len(centers) > 0:
            filtered_df = filtered_df[filtered_df['Center Name'].isin(centers)]

        fig_bar = px.bar(
            filtered_df,
            x='Center Name',
            y=course,
            color='Number_of_Students',
            range_y=[0, 100],
            color_continuous_scale=px.colors.diverging.Armyrose,
            #alternative is fall
            labels={'Number of Students': 'Progress (in percent)'},
        )
        return fig_bar

class DropdownComponent(DashboardComponent):
    def update(self, centers):
        filtered_df = self.df[self.df['Number_of_Students'].notnull()]

        if len(centers) > 0:
            filtered_df = filtered_df[filtered_df['Center Name'].isin(centers)]

        course_columns = [column for column in filtered_df.columns if column.startswith("Progress_")]
        course_options = [{"label": f"Course {column.split('_')[1]}", "value": column} for column in course_columns]

        return course_options

class LayoutComponent:
    def __init__(self, df):
        self.df = df
        self.container = dbc.Container(
            fluid=True,
            style={'background-color': '#fff5d1', 'color': '#000000', 'font-family': 'Georgia'},
            children=[
                html.H2("Dashboard", style={'text-align': 'center', 'padding-top': '20px', 'font-family': 'Georgia'}),
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
                                                dbc.CardHeader(html.H6("Bar Graph", style={'color': '#ffffff',
                                                                                           'font-weight': 'bold'}),
                                                               style={'background-color': '#6873af',
                                                                      'padding': '10px'}),
                                                dbc.CardBody(
                                                    dcc.Graph(id='graph')
                                                ),
                                            ],
                                            style={'background-color': '#ffffff', 'margin': '10px', 'padding': '10px'}
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    width=4,
                                    children=[
                                        dbc.Card(
                                            className="checklist-container",
                                            children=[
                                                dbc.CardHeader(html.H6("Center Name", style={'color': '#ffffff',
                                                                                             'font-weight': 'bold'}),
                                                               style={'background-color': '#6873af',
                                                                      'padding': '10px'}),
                                                dbc.CardBody(
                                                    dcc.Checklist(
                                                        id='center-checklist',
                                                        options=[{'label': center, 'value': center} for center in
                                                                 self.df['Center Name'].unique()],
                                                        value=[],
                                                        labelStyle={'display': 'block'},
                                                        style={
                                                            'height': '100px',
                                                            'overflow': 'auto',
                                                            'background-color': '#ffffff',
                                                            'padding': '2px',
                                                            'color': '#000000',
                                                            'margin': '5px',
                                                            'font-family': 'Times New Roman, serif',  # Change font here
                                                            'fontSize': '17px',
                                                            'marginLeft': '2px'
                                                        }
                                                    ),
                                                ),
                                            ],
                                            style={'background-color': '#ffffff', 'margin': '10px', 'padding': '10px'}
                                        ),
                                        html.Br(),
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(html.H6("Course Selection", style={'color': '#ffffff',
                                                                                                  'font-weight': 'bold'}),
                                                               style={'background-color': '#6873af',
                                                                      'padding': '10px'}),
                                                dbc.CardBody(
                                                    dcc.Dropdown(
                                                        id="Course_dropdown",
                                                        clearable=False,
                                                        multi=False,
                                                        value=None,
                                                        options=[{"label": col, "value": col} for col in self.df.columns if
                                                                 col.startswith('Progress')],
                                                        placeholder="Courses available",
                                                        style={'width': '200px', 'color': '#000000'}
                                                    ),
                                                ),
                                            ],
                                            style={'background-color': '#ffffff', 'margin': '10px', 'padding': '10px'}
                                        ),
                                    ]
                                )
                            ]
                        ),
                        dbc.Row(
                            children=[
                                dbc.Col(
                                    width=6,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(html.H6("Pie Chart", style={'color': '#ffffff',
                                                                                           'font-weight': 'bold'}),
                                                               style={'background-color': '#6873af',
                                                                      'padding': '10px'}),
                                                dbc.CardBody(
                                                    dcc.Graph(id='pie-chart')
                                                ),
                                            ],
                                            style={'background-color': '#f8f9fa', 'margin': '10px', 'padding': '10px'}
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    width=6,
                                    children=[
                                        dbc.Card(
                                            children=[
                                                dbc.CardHeader(html.H6("Line Chart", style={'color': '#ffffff',
                                                                                            'font-weight': 'bold'}),
                                                               style={'background-color': '#6873af',
                                                                      'padding': '10px'}),
                                                dbc.CardBody(
                                                    dcc.Graph(id='line-chart')
                                                ),
                                            ],
                                            style={'background-color': '#f8f9fa', 'margin': '10px', 'padding': '10px'}
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ]
                ),
                # Add Interval component for data update
                dcc.Interval(
                    id='interval-component',
                    interval=5*60*1000,  # in milliseconds, update every 5 minutes
                    n_intervals=0
                ),
                # Add hidden div for storing updated data
                html.Div(id='hidden-div', style={'display': 'none'})
            ]
        )

class DashboardApp:
    def __init__(self, data_file='AAE4B220.xlsx'):
        self.data_file = data_file
        self.df = pd.read_excel(data_file)

        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.layout = LayoutComponent(self.df)
        self.setup_layout()

        # Instantiate objects for components
        self.bar_graph = BarGraph(self.df)
        self.dropdown = DropdownComponent(self.df)

        # Use deque for linked list (data buffer)
        self.data_buffer = deque(maxlen=20)

        # Define callback functions to update the graphs
        self.app.callback(
            Output("graph", "figure"),
            [Input("Course_dropdown", "value"), Input("center-checklist", "value")]
        )(self.bar_graph.update)

        self.app.callback(
            Output("Course_dropdown", "options"),
            [Input("center-checklist", "value")]
        )(self.dropdown.update)

        self.app.callback(
            [Output("pie-chart", "figure"), Output("line-chart", "figure")],
            [Input("center-checklist", "value")]
        )(self.update_pie_line_chart)

        # Run periodic data update
        self.update_data_interval()

    def setup_layout(self):
        self.app.layout = self.layout.container

    def update_data_interval(self):
        @self.app.callback(Output('hidden-div', 'children'), Input('interval-component', 'n_intervals'))
        def update_data(n):
            self.df = pd.read_excel(self.data_file)
            return time.strftime('%Y-%m-%d %H:%M:%S')

    def update_pie_line_chart(self, centers):
        filtered_df = self.df[self.df['Number_of_Students'].notnull()]

        if len(centers) > 0:
            filtered_df = filtered_df[filtered_df['Center Name'].isin(centers)]

        fig_pie = px.pie(
            filtered_df,
            values='Number_of_Students',
            names='Center Name',
            title='Center wise number of Students',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_pie.update_layout(
            title_text='Center wise percentage of students',
            title_x=0.5
        )
        fig_pie.update_traces(marker=dict(line=dict(color='#ffffff', width=0)))

        fig_line = px.line(
            filtered_df,
            x='Center Name',
            y=[col for col in filtered_df.columns if col.startswith("Progress_")],
            title='Comparison of Course Progress',
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        for data in fig_line.data:
            data.visible = True

        return fig_pie, fig_line

    def run_app(self):
        if __name__ == '__main__':
            self.app.run_server(debug=True, port='8050')

# Instantiate and run the app
dashboard = DashboardApp()
dashboard.run_app()
