from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from helper import *
from retry_requests import retry
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
import numpy as np
import os
from google import genai

# List of US states (non-abbreviated)
US_STATES = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
    'West Virginia', 'Wisconsin', 'Wyoming'
]

app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])

# Create default Score object for initial values
default_score = Score()

# App layout
app.layout = html.Div([
    html.H1('Climate Score Dashboard', className="bg-primary", style={'padding': '20px', 'marginBottom': '30px'}),
    
    # How to Use section
    html.Div([
        html.H3('How to Use'),
        html.P(
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#555', 'marginBottom': '20px'}
        ),
    ], style={'margin': '30px', 'padding': '25px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#f9f9f9'}),
    
    # City input section
    html.Div([
        html.Div([
            html.H6('City 1:', style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div([
                dcc.Input(id='city1', type='text', value='Phoenix', placeholder='Enter city name', style={'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ccc', 'marginBottom': '10px'}),
                dcc.Dropdown(id='state1', options=[{'label': s, 'value': s} for s in US_STATES], value='Arizona', style={'width': '200px', 'display': 'inline-block', 'marginBottom': '10px'}),
                dcc.Checklist(
                    id='include1',
                    options=[{'label': 'Include', 'value': 'include'}],
                    value=['include'],  # default checked
                    style={'display': 'inline-block', 'marginLeft': '10px'}
                ),
            ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between', 'alignItems': 'center'}),
        ], style={'display': 'inline-block', 'width': '30%', 'verticalAlign': 'top', 'marginRight': '2%'}),
        
        html.Div([
            html.H6('City 2:', style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div([
                dcc.Input(id='city2', type='text', value='Portland', placeholder='Enter city name', style={'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ccc', 'marginBottom': '10px'}),
                dcc.Dropdown(id='state2', options=[{'label': s, 'value': s} for s in US_STATES], value='Oregon', style={'width': '200px', 'display': 'inline-block', 'marginBottom': '10px'}),
                dcc.Checklist(
                    id='include2',
                options=[{'label': 'Include', 'value': 'include'}],
                value=['include'],
                    style={'display': 'inline-block', 'marginLeft': '10px'}
                ),
            ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between', 'alignItems': 'center'}),
        ], style={'display': 'inline-block', 'width': '30%', 'verticalAlign': 'top', 'marginRight': '2%'}),
        
        html.Div([
            html.H6('City 3:', style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div([
                dcc.Input(id='city3', type='text', value='Boston', placeholder='Enter city name', style={'padding': '8px', 'borderRadius': '4px', 'border': '1px solid #ccc', 'marginBottom': '10px'}),
                dcc.Dropdown(id='state3', options=[{'label': s, 'value': s} for s in US_STATES], value='Massachusetts', style={'width': '200px', 'display': 'inline-block', 'marginBottom': '10px'}),
                dcc.Checklist(
                    id='include3',
                options=[{'label': 'Include', 'value': 'include'}],
                value=['include'],
                style={'display': 'inline-block', 'marginLeft': '10px'}
                ),
            ], style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between', 'alignItems': 'center'}),
        ], style={'display': 'inline-block', 'width': '30%', 'verticalAlign': 'top'}),
    ], style={'margin': '30px', 'padding': '25px', 'border': '1px solid #bbb', 'borderRadius': '8px', 'background': 'rgb(120 194 173 / 13%)'}),
    # Input controls section
    html.Div([
        html.H2('Climate Preferences', style={'marginBottom': '25px'}),
        
        # Temperature preferences
        html.Div([
            html.H4('Temperature Preferences', style={'marginBottom': '15px'}),
            html.Div(
                "Let's say it's a sunny or partly cloudy day out. What temperature range do you find ideal and how much do you enjoy it?",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
            ),
            html.Div([
                html.Div([
                    html.Label('Ideal Temperature Range (°F):'),
                    dcc.RangeSlider(
                        id='ideal-temp-range',
                        min=0,
                        max=120,
                        step=5,
                        marks={i: str(i) for i in range(0, 121, 20)},
                        value=[default_score.ideal_temp__min, default_score.ideal_temp__max],
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Label('Sunny Day Preference:'),
                    dcc.Slider(
                        id='sunny-day-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.ideal_sunny_day__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),
        
        # Cold weather preferences
        html.Div([
            html.H4('Cold Weather Preferences', style={'marginBottom': '15px'}),
            html.Div(
                "How cold is too cold if there is no wind and how do you feel about too-cold days?",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
            ),
            html.Div([
                html.Div([
                    html.Label('Too Cold (No Wind) - Temperature (°F):'),
                    dcc.Slider(
                        id='too-cold-still-temp',
                        min=-20,
                        max=60,
                        step=5,
                        marks={i: str(i) for i in range(-20, 61, 20)},
                        value=default_score.too_cold_still__max,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Label('Too Cold (No Wind) Preference:'),
                    dcc.Slider(
                        id='too-cold-still-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.too_cold_still__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
             html.Div(
                "How cold is too cold on a windy day, and how do you feel about cold windy days?",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px', 'marginTop': '20px'}
            ),
            html.Div([
                html.Div([
                    html.Label('Too Cold (Windy) - Temperature (°F):'),
                    dcc.Slider(
                        id='too-cold-windy-temp',
                        min=-20,
                        max=60,
                        step=5,
                        marks={i: str(i) for i in range(-20, 61, 20)},
                        value=default_score.too_cold_windy__max,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Label('Too Cold (Windy) Preference:'),
                    dcc.Slider(
                        id='too-cold-windy-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.too_cold_windy__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),

        # Humidity preferences
        html.Div([
            html.H4('Humidity Preferences', style={'marginBottom': '15px'}),
            html.Div(
                "If it's a noticeably humid day, at what temperature do you start to feel uncomfortable?",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
            ),
            html.Div([
                html.Div([
                    html.Label('Humid Day Max Temperature (°F):'),
                    dcc.Slider(
                        id='humid-day-max',
                        min=50,
                        max=100,
                        step=5,
                        marks={i: str(i) for i in range(50, 101, 10)},
                        value=default_score.humid_day_max,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Label('Hot Humid Day Preference:'),
                    dcc.Slider(
                        id='humid-day-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.humid_day_coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),
        
        # Precipitation preferences
        html.Div([
            html.H4('Precipitation Preferences', style={'marginBottom': '15px'}),
            html.Div(
                "How do you feel about light rain, heavy rain, and snow?",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
            ),
            html.Div([
                html.Div([
                    html.Label('Light Rain Preference:'),
                    dcc.Slider(
                        id='light-rain-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.light_rain__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),


                html.Div([
                    html.Label('Heavy Rain Preference:'),
                    dcc.Slider(
                        id='heavy-rain-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.heavy_rain__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),


                html.Div([
                    html.Label('Snow Preference:'),
                    dcc.Slider(
                        id='snow-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.snow_coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        }
                    ),
                ], style={'flex': '1', 'marginLeft': '20px'}),



            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
        ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),


        # Other preferences
        html.Div([
            html.H4('Other Preferences', style={'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.Div(
                        "How do you feel about overcast (cloudy) days?",
                        style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
                    ),
                    dcc.Slider(
                        id='overcast-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.overcast_dry__coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        },
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Div(
                        "What is the minimum temperature (°F) for a day to feel like 'dry heat' to you?",
                        style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
                    ),
                    dcc.Slider(
                        id='dry-heat-min',
                        min=80,
                        max=120,
                        step=5,
                        marks={i: str(i) for i in range(80, 121, 10)},
                        value=default_score.dry_heat_day_min,
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'flex': '1', 'marginRight': '20px'}),
                html.Div([
                    html.Div(
                        "How do you feel about hot, dry days (above your minimum dry heat temperature)?",
                        style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
                    ),
                    dcc.Slider(
                        id='dry-heat-coef',
                        min=-2,
                        max=2,
                        step=1,
                        value=default_score.dry_heat_day_coef,
                        marks={
                            -2: 'Hate',
                            -1: 'Dislike',
                            0: 'Neutral',
                            1: 'Like',
                            2: 'Love'
                        },
                    ),
                ], style={'flex': '1'}),

            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between', 'marginBottom': '20px'}),

            # Time window preferences
            html.Div([
                html.Div(
                    "What hours of the day matter most to you for being outside? The climate score will focus on weather during these hours.",
                    style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
                ),
                html.Div([
                    html.Div([
                        html.Label('Time Window (24-hour format):'),
                        dcc.RangeSlider(
                            id='time-window-range',
                            min=0,
                            max=23,
                            step=1,
                            marks={i: f"{i:02d}:00" for i in range(0, 24, 3)},
                            value=[8, 20],  # Default 8 AM to 8 PM
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ], style={'flex': '1'}),
                ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
            ], style={'marginBottom': '20px', 'background': '#fafafa'}),
        ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),
        
        # Natural disaster preferences
        html.Div([
            html.H4('Natural Disaster Risk Tolerance', style={'marginBottom': '20px'}),
            html.Div(
                "What is your tolerance for natural disasters in a place to live? For each risk, choose 'No preference' if you don't mind the risk at all, 'Some' if you can tolerate some but not a ton of this risk, or 'Dealbreaker' if having any of this risk is a dealbreaker for you.",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
            ),
            html.Div([
                html.Div([
                    html.Div('Flooding', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='flooding-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
                
                html.Div([
                    html.Div('Wildfire (in location)', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='wildfire-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
                
                html.Div([
                    html.Div('Smoke (from wildfires)', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='smoke-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
                
                html.Div([
                    html.Div('Earthquakes', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='earthquake-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
                
                html.Div([
                    html.Div('Hurricanes', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='hurricane-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
                
                html.Div([
                    html.Div('Tornados', style={'fontWeight': 'bold', 'textAlign': 'center', 'marginBottom': '10px'}),
                    dcc.Dropdown(
                        id='tornado-risk',
                        options=[
                            {'label': "No preference", 'value': 'ok'},
                            {'label': "Some", 'value': 'some'},
                            {'label': "Dealbreaker", 'value': 'dealbreaker'}
                        ],
                        value='ok',
                        style={'width': '100%'}
                    )
                ], style={'flex': '1', 'margin': '10px', 'padding': '8px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': '#fafafa'}),
            ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between', 'flexWrap': 'wrap', 'marginBottom': '30px'}),
           ], style={'marginBottom': '30px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}), 
        # Other preferences input and button
        html.Div([
            html.Div([
                html.H4('Other Preferences for Places to Live:', style={'marginBottom': '15px'}),
                html.Div(
                    "What else matters to you about a place to live? ",
                    style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '15px'}
                ),
                dcc.Input(
                    id='additional-preferences',
                    type='text',
                    placeholder='e.g. low cost of living, good state universities, urban, walkable, near ocean',
                    style={'marginLeft': '0px', 'width': '500px', 'padding': '12px', 'borderRadius': '6px', 'border': '1px solid #ccc', 'fontSize': '14px'}
                )
            ]),
            html.Button('Calculate Climate Scores', id='calculate-btn', n_clicks=0, style={'marginTop': '20px', 'padding': '14px 28px', 'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontSize': '16px', 'fontWeight': 'bold'}),
        ], style={'marginTop': '20px', 'marginBottom': '20px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),
        html.Div(id='calculation-status', style={'padding': '10px', 'borderRadius': '5px'}),
    ], style={'margin': '30px', 'padding': '30px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': 'rgb(120 194 173 / 13%)'}),

    # Results section: location-specific Gemini div at the top
    html.Div([
        html.Div(id='location-gemini-comparison', style={'margin': '30px', 'padding': '25px', 'border': '1px solid #eee', 'borderRadius': '8px', 'background': '#f7faff'}),
        dcc.Graph(id='city-map', figure={}, style={'margin': '20px 0'}),
        dcc.Graph(
            id='score-distribution',
            figure={
                'data': [],
                'layout': go.Layout(
                    title='Score Distribution by Year',
                    xaxis={'title': 'Year'},
                    yaxis={'title': 'Percentage of Days'},
                    shapes=[]
                )
            },
            style={'margin': '20px 0'}
        ),
        dcc.Graph(
            id='score-average',
            figure={
                'data': [],
                'layout': go.Layout(
                    title='Score Average by Year',
                    xaxis={'title': 'Year'},
                    yaxis={'title': 'Score Average'},
                    shapes=[]
                )
            },
            style={'margin': '20px 0'}
        ),
        dcc.Graph(
            id='monthly-stacked-scores',
            figure={
                'data': [],
                'layout': go.Layout(
                    title='Monthly Average Stacked Scores by Year',
                    xaxis={'title': 'Month'},
                    yaxis={'title': 'Average Score'},
                    showlegend=True
                )
            },
            style={'margin': '20px 0'}
        ),
        dcc.Graph(
            id='reason-distribution',
            figure={
                'data': [],
                'layout': go.Layout(
                    title='Number of Days by Type (Reason) per Year',
                    xaxis={'title': 'Year'},
                    yaxis={'title': 'Number of Days'},
                    shapes=[]
                )
            },
            style={'margin': '20px 0'}
        ),
        dcc.Graph(
            id='pm25-chart',
            figure={
                'data': [],
                'layout': go.Layout(
                    title='PM2.5 Air Quality Distribution by Year',
                    xaxis={'title': 'Year'},
                    yaxis={'title': 'Percentage of Hours'},
                    showlegend=True
                )
            },
            style={'margin': '20px 0'}
        ),
        html.Div(id='gemini-suggestions', style={'margin': '30px', 'padding': '25px', 'border': '1px solid #eee', 'borderRadius': '8px', 'background': '#fafaff'}),
    ], style={'margin': '30px', 'padding': '20px'}),
    
    # Footer
    html.Div([
        html.Span("Find a bug? Report it ", style={'color': '#808080'}),
        html.A("here", href="https://github.com/cb92/personal-climate-score", target="_blank", style={'color': '#0066cc', 'textDecoration': 'underline'}),
    ], style={'textAlign': 'left', 'marginTop': '50px', 'marginBottom': '30px', 'fontSize': '14px', 'padding': '20px'}),
], style={'padding': '20px'})

@callback(
    [Output('score-distribution', 'figure'),
     Output('score-average', 'figure'),
     Output('pm25-chart', 'figure'),
     Output('reason-distribution', 'figure'),
     Output('monthly-stacked-scores', 'figure'),
     Output('city-map', 'figure'),
     Output('calculation-status', 'children'),
     Output('gemini-suggestions', 'children'),
     Output('location-gemini-comparison', 'children')],
    [Input('calculate-btn', 'n_clicks')],
    [State('city1', 'value'), State('state1', 'value'), State('include1', 'value'),
     State('city2', 'value'), State('state2', 'value'), State('include2', 'value'),
     State('city3', 'value'), State('state3', 'value'), State('include3', 'value'),
     Input('ideal-temp-range', 'value'),
     Input('time-window-range', 'value'),
     Input('sunny-day-coef', 'value'),
     Input('too-cold-still-temp', 'value'),
     Input('too-cold-still-coef', 'value'),
     Input('too-cold-windy-temp', 'value'),
     Input('too-cold-windy-coef', 'value'),
     Input('humid-day-max', 'value'),
     Input('humid-day-coef', 'value'),
     Input('light-rain-coef', 'value'),
     Input('heavy-rain-coef', 'value'),
     Input('snow-coef', 'value'),
     Input('overcast-coef', 'value'),
     Input('dry-heat-min', 'value'),
     Input('dry-heat-coef', 'value'),
     State('flooding-risk', 'value'),
     State('wildfire-risk', 'value'),
     State('smoke-risk', 'value'),
     State('earthquake-risk', 'value'),
     State('hurricane-risk', 'value'),
     State('tornado-risk', 'value'),
     State('additional-preferences', 'value')]
)
def update_charts(n_clicks, city1, state1, include1, city2, state2, include2, city3, state3, include3,
                  ideal_temp_range, time_window_range, sunny_day_coef, too_cold_still_temp, too_cold_still_coef,
                  too_cold_windy_temp, too_cold_windy_coef, humid_day_max, humid_day_coef,
                  light_rain_coef, heavy_rain_coef, snow_coef, overcast_coef, dry_heat_min, dry_heat_coef,
                  flooding_risk, wildfire_risk, smoke_risk, earthquake_risk, hurricane_risk, tornado_risk,
                  additional_preferences):
    
    if n_clicks == 0:
        empty_figure = {
            'data': [],
            'layout': go.Layout(
                title='Score Distribution by Year',
                xaxis={'title': 'Year'},
                yaxis={'title': 'Percentage of Days'},
                shapes=[]
            )
        }
        empty_average_figure = {
            'data': [],
            'layout': go.Layout(
                title='Score Average by Year',
                xaxis={'title': 'Year'},
                yaxis={'title': 'Score Average'},
                shapes=[]
            )
        }
        empty_pm25_figure = {
            'data': [],
            'layout': go.Layout(
                title='PM2.5 Air Quality Distribution by Year',
                xaxis={'title': 'Year'},
                yaxis={'title': 'Percentage of Hours'},
                showlegend=True
            )
        }
        empty_reason_figure = {
            'data': [],
            'layout': go.Layout(
                title='Number of Days by Type (Reason) per Year',
                xaxis={'title': 'Year'},
                yaxis={'title': 'Number of Days'},
                shapes=[]
            )
        }
        empty_monthly_stacked_figure = {
            'data': [],
            'layout': go.Layout(
                title='Monthly Average Stacked Scores by Year',
                xaxis={'title': 'Month'},
                yaxis={'title': 'Average Score'},
                showlegend=True
            )
        }
        empty_map_figure = {'data': [], 'layout': go.Layout(title='Selected Cities Map')}
        empty_location_gemini = html.Div()
        return empty_figure, empty_average_figure, empty_pm25_figure, empty_reason_figure, empty_monthly_stacked_figure, empty_map_figure, "Click 'Calculate Climate Scores' to generate charts", "", empty_location_gemini

    # Build city/state list using checkboxes
    city_states = []
    if include1 and 'include' in include1 and city1 and state1:
        city_states.append((city1.strip(), state1.strip()))
    if include2 and 'include' in include2 and city2 and state2:
        city_states.append((city2.strip(), state2.strip()))
    if include3 and 'include' in include3 and city3 and state3:
        city_states.append((city3.strip(), state3.strip()))
    city_states = city_states[:3]

    # Create and set climate_score ONCE
    climate_score = Score()
    climate_score.set_temperature_preferences(ideal_temp_range[0], ideal_temp_range[1], sunny_day_coef)
    climate_score.set_cold_weather_preferences(too_cold_still_temp, too_cold_still_coef, 
                                             too_cold_windy_temp, too_cold_windy_coef)
    climate_score.set_humidity_preferences(humid_day_max, humid_day_coef)
    climate_score.set_precipitation_preferences(light_rain_coef, heavy_rain_coef, snow_coef)
    climate_score.set_overcast_preference(overcast_coef)
    climate_score.set_dry_heat_preferences(dry_heat_min, dry_heat_coef)
    
    # Set time window preferences
    if time_window_range and len(time_window_range) == 2:
        min_hour, max_hour = time_window_range
        min_time = f"{min_hour:02d}:00:00"
        max_time = f"{max_hour:02d}:00:00"
        climate_score.set_time_window(min_time, max_time)

    # --- Gemini API integration ---
    disaster_preferences = {
        'flooding': flooding_risk,
        'wildfire (direct impacts only)': wildfire_risk,
        'smoke': smoke_risk,
        'earthquakes': earthquake_risk,
        'hurricanes': hurricane_risk,
        'tornados': tornado_risk
    }
    prompt = build_gemini_prompt(climate_score, additional_preferences, disaster_preferences)
    try:
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        # Format Gemini response as Markdown for nice display
        gemini_text = dcc.Markdown(response.text, style={'background': '#f9f9ff', 'padding': '10px', 'borderRadius': '5px'})
    except Exception as e:
        gemini_text = html.Div(f"Could not get suggestions from Gemini: {e}", style={'color': 'red'})

    # --- Location-specific Gemini comparison ---
    location_gemini_div = html.Div()
    if (additional_preferences or any(v != 'ok' for v in disaster_preferences.values())) and city_states:
        location_gemini_responses = []
        for city, state in city_states:
            try:
                loc_prompt = build_gemini_location_prompt(city, state, additional_preferences, disaster_preferences)
                loc_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=loc_prompt,
                )
                location_gemini_responses.append(
                    html.Div([
                        html.H4(f"{city}, {state}"),
                        dcc.Markdown(loc_response.text, style={'background': '#f9f9ff', 'padding': '10px', 'borderRadius': '5px'})
                    ], style={'flex': '1', 'margin': '10px'})
                )
            except Exception as e:
                location_gemini_responses.append(
                    html.Div([
                        html.H4(f"{city}, {state}"),
                        html.Div(f"Could not get Gemini response: {e}", style={'color': 'red'})
                    ], style={'flex': '1', 'margin': '10px'})
                )
        location_gemini_div = html.Div(
            location_gemini_responses,
            style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}
        )

    # For the map, collect lat/lon and city labels
    lats, lons, labels = [], [], []
    score_subplots = []
    average_subplots = []
    pm25_subplots = []
    reason_subplots = []
    monthly_stacked_subplots = []
    status_msgs = []
    subplot_titles = []

    for city, state in city_states:
        try:
            lat, lon, timezone, pop = get_city_info(city, state)
            lats.append(lat)
            lons.append(lon)
            labels.append(f"{city}, {state}")
            # Use cache-aware versions of the data retrieval and scoring functions
            historical_df, _ = get_historical_and_aqi_data(lat, lon, timezone, city, state)
            forecasted_df, _ = get_forecasted_data(lat, lon, timezone, city, state, model='NICAM16_8S')
            scored_historical_df, reasons_historical = process_historical_for_plotting(
                historical_df, climate_score, city=city, state=state
            )
            scored_forecasted_df, reasons_forecasted = process_forecasted_for_plotting(
                forecasted_df, climate_score, model='NICAM16_8S', city=city, state=state
            )
            # Combine historical and forecasted data with source indicator
            scored_historical_df['source'] = 'historical'
            scored_forecasted_df['source'] = 'forecasted'
            
            # Union the dataframes
            combined_df = pd.concat([scored_historical_df, scored_forecasted_df], ignore_index=True)
            
            # --- Score Distribution ---
            score_percents = {}
            for score_val in [0, 25, 50, 75, 100]:
                score_percents[score_val] = combined_df[combined_df['score'] == score_val].groupby('year').size() / combined_df.groupby('year').size()
            
            min_forecasted_date = None
            if not scored_forecasted_df.empty:
                min_forecasted_date = scored_forecasted_df["date"].min()
            if min_forecasted_date is not None and hasattr(min_forecasted_date, 'year'):
                forecasted_year = min_forecasted_date.year
            else:
                forecasted_year = scored_historical_df['year'].max()
            
            score_traces = []
            for score_val, color in zip([0, 25, 50, 75, 100], ['red', 'orange', 'yellow', 'green', 'blue']):
                score_traces.append(
                    go.Bar(
                        x=score_percents[score_val].index,
                        y=score_percents[score_val].values,
                        name=f'Score {score_val}',
                        marker_color=color,
                        #opacity=opacity_value,
                        showlegend=False,
                    )
                )
            score_subplots.append((score_traces, forecasted_year, f"{city}, {state}"))
            # --- Score Average ---
            avg_score_historical = scored_historical_df.groupby('year')['score'].mean()
            avg_score_forecasted = scored_forecasted_df.groupby('year')['score'].mean()
            average_traces = [
                go.Scatter(x=avg_score_historical.index, y=avg_score_historical.values, mode='lines+markers', name='Historical', line=dict(color='blue', width=2), showlegend=False),
                go.Scatter(x=avg_score_forecasted.index, y=avg_score_forecasted.values, mode='lines+markers', name='Forecasted', line=dict(color='red', width=2), showlegend=False)
            ]
            average_subplots.append((average_traces, f"{city}, {state}"))
            # --- PM2.5 ---
            historical_df['year'] = pd.to_datetime(historical_df['date']).dt.year
            pm25_categories = {
                'Healthy': (0, 12),
                'Moderate': (12, 35.5),
                'Unhealthy for Sensitive': (35.5, 55.5),
                'Unhealthy': (55.5, 150.5),
                'Hazardous': (150.5, float('inf'))
            }
            pm25_data = {}
            for category, (min_val, max_val) in pm25_categories.items():
                if max_val == float('inf'):
                    mask = (historical_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (historical_df['pm2_5__micrograms_per_cubic_metre'].notna())
                else:
                    mask = (historical_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (historical_df['pm2_5__micrograms_per_cubic_metre'] < max_val) & (historical_df['pm2_5__micrograms_per_cubic_metre'].notna())
                yearly_counts = historical_df[mask].groupby('year').size()
                total_hours_per_year = historical_df[historical_df['pm2_5__micrograms_per_cubic_metre'].notna()].groupby('year').size()
                pm25_data[category] = (yearly_counts / total_hours_per_year * 100)

            pm25_traces = []
            for category, color in zip(['Healthy', 'Moderate', 'Unhealthy for Sensitive', 'Unhealthy', 'Hazardous'], ['green', 'yellow', 'orange', 'red', 'purple']):
                pm25_traces.append(
                    go.Bar(
                        x=pm25_data[category].index,
                        y=pm25_data[category].values,
                        name=category,
                        marker_color=color,
                        #opacity=opacity_value,
                        showlegend=False,
                    )
                )
            pm25_subplots.append((pm25_traces, f"{city}, {state}"))
            # --- Reason Distribution ---
            all_reasons = list(set(reasons_historical).union(set(reasons_forecasted)))
            reason_counts_historical = {reason: scored_historical_df[scored_historical_df['reason'] == reason].groupby('year').size() for reason in all_reasons}
            reason_counts_forecasted = {reason: scored_forecasted_df[scored_forecasted_df['reason'] == reason].groupby('year').size() for reason in all_reasons}
            
            # Define theme colors for consistent coloring
            theme_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            reason_traces = []
            for i, reason in enumerate(all_reasons):
                color = theme_colors[i % len(theme_colors)]
                # Historical trace
                reason_traces.append(
                    go.Scatter(
                        x=reason_counts_historical[reason].index, 
                        y=reason_counts_historical[reason].values, 
                        mode='lines+markers', 
                        name=f'{reason} (Hist)', 
                        line=dict(dash='solid', color=color), 
                        marker=dict(color=color),
                        showlegend=False
                    )
                )
                # Forecasted trace (same color, different dash)
                reason_traces.append(
                    go.Scatter(
                        x=reason_counts_forecasted[reason].index, 
                        y=reason_counts_forecasted[reason].values, 
                        mode='lines+markers', 
                        name=f'{reason} (Forecast)', 
                        line=dict(dash='dot', color=color), 
                        marker=dict(color=color),
                        showlegend=False
                    )
                )
            reason_subplots.append((reason_traces, f"{city}, {state}"))
            # --- Monthly Stacked ---
            scored_historical_df['month'] = scored_historical_df['date'].dt.month
            scored_forecasted_df['month'] = scored_forecasted_df['date'].dt.month
            monthly_avg_hist = scored_historical_df.groupby(['year', 'month'])['score'].mean().reset_index()
            years_hist = sorted(monthly_avg_hist['year'].unique())
            n_hist = len(years_hist)
            hist_traces = []
            for i, year in enumerate(years_hist):
                year_data = monthly_avg_hist[monthly_avg_hist['year'] == year]
                fade = 0.2 + 0.8 * (i + 1) / n_hist
                hist_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'Hist {year}', line=dict(color=f'rgba(0,0,255,{fade})', width=2), showlegend=False)
                )
            monthly_avg_fore = scored_forecasted_df.groupby(['year', 'month'])['score'].mean().reset_index()
            years_fore = sorted(monthly_avg_fore['year'].unique())
            n_fore = len(years_fore)
            fore_traces = []
            for i, year in enumerate(years_fore):
                year_data = monthly_avg_fore[monthly_avg_fore['year'] == year]
                fade = 0.2 + 0.8 * (i + 1) / n_fore
                fore_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'Forecast {year}', line=dict(color=f'rgba(255,0,128,{fade})', width=2), showlegend=False)
                )
            monthly_stacked_subplots.append((hist_traces + fore_traces, f"{city}, {state}"))
            status_msgs.append(f"{city}, {state}: Data retrieved successfully")
        except Exception as e:
            status_msgs.append(f"{city}, {state}: Error - {str(e)}")
            # Add empty traces for this city
            score_subplots.append(([], 0, f"{city}, {state}"))
            average_subplots.append(([], f"{city}, {state}"))
            pm25_subplots.append(([], f"{city}, {state}"))
            reason_subplots.append(([], f"{city}, {state}"))
            monthly_stacked_subplots.append(([], f"{city}, {state}"))

    # Build subplots for each plot type
    n_cities = len(city_states)
    # Score Distribution
    # Ensure subplot_titles are strings, not tuples
    subplot_titles = [f"{city}, {state}" for city, state in city_states]

    score_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, forecasted_year, label) in enumerate(score_subplots):
        for trace in traces:
            score_fig.add_trace(trace, row=1, col=i+1)
        score_fig.add_shape(
            dict(type='line', x0=forecasted_year, x1=forecasted_year, y0=0, y1=1, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
    score_fig.update_layout(title='Score Distribution by Year', barmode='stack')
    # Score Average
    avg_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(average_subplots):
        for trace in traces:
            avg_fig.add_trace(trace, row=1, col=i+1)
    avg_fig.update_layout(title='Score Average by Year')
    # PM2.5
    pm25_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(pm25_subplots):
        for trace in traces:
            pm25_fig.add_trace(trace, row=1, col=i+1)
    pm25_fig.update_layout(title='PM2.5 Air Quality Distribution by Year', barmode='stack')
    # Reason Distribution
    reason_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(reason_subplots):
        for trace in traces:
            reason_fig.add_trace(trace, row=1, col=i+1)
    reason_fig.update_layout(title='Number of Days by Type (Reason) per Year')
    # Monthly Stacked
    monthly_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(monthly_stacked_subplots):
        for trace in traces:
            monthly_fig.add_trace(trace, row=1, col=i+1)
    monthly_fig.update_layout(title='Monthly Average Stacked Scores by Year')

    # Build the map
    map_trace = go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers+text',
        marker=go.scattermap.Marker(size=14, color='blue'),
        text=labels,
        textposition='top right',
    )
    map_layout = go.Layout(
        title='Selected Cities Map',
        autosize=True,
        hovermode='closest',
        map=dict(
            bearing=0,
            center=dict(lat=np.mean(lats) if lats else 39, lon=np.mean(lons) if lons else -98),
            pitch=0,
            zoom=3
        )
    )
    map_figure = go.Figure(data=[map_trace], layout=map_layout)

    # Instead of joining with '<br>', use html.Div for each message
    status_children = [html.Div(msg) for msg in status_msgs]
    return score_fig, avg_fig, pm25_fig, reason_fig, monthly_fig, map_figure, status_children, gemini_text, location_gemini_div

# Run the app
if __name__ == '__main__':
    app.run(debug=True)