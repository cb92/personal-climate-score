##from curses import KEY_SAVE
from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
from helper import *
#from retry_requests import retry
import plotly.graph_objects as go
#from datetime import date
#from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
import numpy as np
from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

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
            "This dashboard helps you compare the climate and environmental conditions of up to three US cities based on your personal preferences. To use the tool, enter the names and states of the US cities you want to compare, then adjust the sliders and dropdowns to reflect your ideal weather, natural disaster risk tolerance, and other preferences. When ready, click 'Calculate Climate Scores' to generate personalized climate metrics and visualizations for each city.",
            style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#555', 'marginBottom': '15px'}
        ),
        html.P(
            "The results show how well each city matches your preferences, both historically and in future climate projections. Higher scores indicate a better match to your chosen criteria. Use the graphs to explore seasonal patterns, recent air quality history, and the reasons behind each city's score. Remember, this tool is for informational purposes and uses the best available data, but all climate projections have uncertainty.",
            style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#555', 'marginBottom': '20px'}
        ),
    html.P(
        "For more detailed information about how this dashboard works, including data sources, methodology, and troubleshooting tips, please see the README file on GitHub: ",
        style={'fontSize': '16px', 'lineHeight': '1.6', 'color': '#555', 'marginBottom': '10px', 'display': 'inline'}
    ),
    html.A(
        "View the README",
        href="https://github.com/cb92/personal-climate-score/blob/main/README.md",
        target="_blank",
        style={'fontSize': '16px', 'color': '#007bff', 'textDecoration': 'underline', 'marginLeft': '5px'}
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
            html.Div(
                "Click the button below to calculate your personal climate score metrics for the cities you've selected. Note that if you choose entirely new location/score combinations that the tool has not seen before, it may take a minute to complete. ",
                style={'fontSize': '0.95em', 'color': '#555', 'marginBottom': '10px', 'marginTop': '15px'}
            ),
            dbc.Button('Calculate Climate Scores', id='calculate-btn', n_clicks=0, style={'marginTop': '10px', 'padding': '14px 28px', 'backgroundColor': '#158cba', 'color': 'white', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontSize': '16px', 'fontWeight': 'bold'}),
            html.Div(id='calculation-status', style={'padding': '10px', 'borderRadius': '5px'})
        ], style={'marginTop': '10px', 'marginBottom': '20px', 'padding': '20px', 'border': '1px solid #eee', 'borderRadius': '5px', 'background': '#fafafa'}),
    ], style={'margin': '30px', 'padding': '30px', 'border': '1px solid #ddd', 'borderRadius': '8px', 'background': 'rgb(120 194 173 / 13%)'}),

    # Results section: location-specific Gemini div at the top
    html.Div([
        dcc.Loading(
            id="loading-gemini1",
            type="dot",
            children=html.Div(id='location-gemini-comparison', style={'margin': '30px', 'padding': '25px', 'border': '1px solid #eee', 'borderRadius': '8px', 'background': '#f7faff'})
        ),
        dcc.Loading(
            id="loading-map",
            type="graph",
            children=dcc.Graph(id='city-map', figure={}, style={'margin': '20px 0'})
        ),
        dcc.Loading(
            id="loading-graph1",
            type="graph",
            children=dcc.Graph(
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
        ),
        dcc.Loading(
            id="loading-graph2",
            type="graph",
            children=dcc.Graph(
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
            )
        ),

        dcc.Loading(
            id="loading-graph3",
            type="graph",
            children=dcc.Graph(
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
            )
        ),
        dcc.Loading(
            id="loading-graph4",
            type="graph",
            children=dcc.Graph(
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
            )
        ),
        dcc.Loading(
            id="loading-graph5",
            type="graph",
            children=dcc.Graph(
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
            )
        ),
        dcc.Loading(
            id="loading-gemini2",
            type="dot",
            children=html.Div(id='gemini-suggestions', style={'margin': '30px', 'padding': '25px', 'border': '1px solid #eee', 'borderRadius': '8px', 'background': '#fafaff'})
        ),
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
     Output('monthly-stacked-scores', 'figure'),
     Output('reason-distribution', 'figure'),
     Output('pm25-chart', 'figure'),     
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
    
    # If first load, use default values for all inputs
    
    if n_clicks == 0:
        city1 = 'Phoenix'
        state1 = 'Arizona'
        include1 = ['include']
        city2 = 'Portland'
        state2 = 'Oregon'
        include2 = ['include']
        city3 = 'Boston'
        state3 = 'Massachusetts'
        include3 = ['include']
        ideal_temp_range = [default_score.ideal_temp__min, default_score.ideal_temp__max]
        time_window_range = [8, 20]
        sunny_day_coef = default_score.ideal_sunny_day__coef
        too_cold_still_temp = default_score.too_cold_still__max
        too_cold_still_coef = default_score.too_cold_still__coef
        too_cold_windy_temp = default_score.too_cold_windy__max
        too_cold_windy_coef = default_score.too_cold_windy__coef
        humid_day_max = default_score.humid_day_max
        humid_day_coef = default_score.humid_day_coef
        light_rain_coef = default_score.light_rain__coef
        heavy_rain_coef = default_score.heavy_rain__coef
        snow_coef = default_score.snow_coef
        overcast_coef = default_score.overcast_dry__coef
        dry_heat_min = default_score.dry_heat_day_min
        dry_heat_coef = default_score.dry_heat_day_coef
        flooding_risk = 'ok'
        wildfire_risk = 'ok'
        smoke_risk = 'ok'
        earthquake_risk = 'ok'
        hurricane_risk = 'ok'
        tornado_risk = 'ok'
        additional_preferences = ''

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
                client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
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
    show_legend = False

    j = 1
    for city, state in city_states:
        show_legend = j == len(city_states)
        j += 1
        try:
            lat, lon, timezone, pop = get_city_info(city, state)
            lats.append(lat)
            lons.append(lon)
            labels.append(f"{city}, {state}")
            # Use cache-aware versions of the data retrieval and scoring functions
            historical_daily_df, pm25_df, _, _ = get_historical_and_aqi_data(lat, lon, timezone, city, state)  
            # --- Combined forecasted data (all models) ---
            combined_forecasted_df, _ = get_combined_forecasted_data(
                lat, lon, timezone, city, state,
                models=["EC_Earth3P_HR", "MRI_AGCM3_2_S", "NICAM16_8S"]
            )
            scored_historical_df, reasons_historical = process_historical_for_plotting(
                historical_daily_df, climate_score, city=city, state=state
            )
            scored_combined_forecasted_df, reasons_combined_forecasted = process_combined_forecasted_for_plotting(
                combined_forecasted_df, climate_score,
                models=["EC_Earth3P_HR", "MRI_AGCM3_2_S", "NICAM16_8S"],
                city=city, state=state
            )

            # Safely cast the date columns to datetime for both dataframes
            if 'date' in scored_historical_df.columns:
                scored_historical_df['date'] = pd.to_datetime(scored_historical_df['date'], errors='coerce')
            if 'date' in scored_combined_forecasted_df.columns:
                scored_combined_forecasted_df['date'] = pd.to_datetime(scored_combined_forecasted_df['date'], errors='coerce')
            

            min_forecasted_date = None
            if not scored_combined_forecasted_df.empty:
                min_forecasted_date = scored_combined_forecasted_df["date"].min()
            if min_forecasted_date is not None and hasattr(min_forecasted_date, 'year'):
                min_forecasted_year = min_forecasted_date.year
            else:
                min_forecasted_year = scored_historical_df['year'].max()

            max_historical_date = None
            if not scored_historical_df.empty:
                max_historical_date = scored_historical_df["date"].max()
            if max_historical_date is not None and hasattr(max_historical_date, 'year'):
                max_historical_year = max_historical_date.year
            else:
                max_historical_year = scored_historical_df['year'].max()

            # If the last year of historical == first year of forecasted, Get the number of distinct days in the shared year in both historical and forecasted dataframes
            if max_historical_year == min_forecasted_year:
                shared_year = max_historical_year  # This is the year present in both
                num_days_shared_historical = scored_historical_df[scored_historical_df['year'] == shared_year]['date'].nunique()
                num_days_shared_forecasted = scored_combined_forecasted_df[scored_combined_forecasted_df['year'] == shared_year]['date'].nunique()
                

            # --- Score Distribution ---
            score_percents_historical = {}
            score_percents_combined_forecasted = {}
            all_dates = pd.concat([scored_historical_df[['year', 'date']], scored_combined_forecasted_df[['year', 'date']]])
            dates_per_year = all_dates.drop_duplicates().groupby('year')['date'].nunique()
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            score_percents_by_model = []
            for col in score_cols:
                model_percents = {}
                for score_val in [0, 25, 50, 75, 100]:
                    score_percent = scored_combined_forecasted_df[scored_combined_forecasted_df[col] == score_val].groupby('year').size() / dates_per_year #scored_combined_forecasted_df.groupby('year').size()
                    model_percents[score_val] = 100 * score_percent.fillna(0)
                score_percents_by_model.append(model_percents)

            for score_val in [0, 25, 50, 75, 100]:
                # Calculate the denominator: number of distinct dates per year across both historical and combined forecasted dataframes
                score_percent = scored_historical_df[scored_historical_df['score'] == score_val].groupby('year').size() / dates_per_year
                score_percents_historical[score_val] = 100*score_percent.fillna(0)
                dfs = [model[score_val] for model in score_percents_by_model]
                if dfs:
                    combined = pd.concat(dfs, axis=1).mean(axis=1)
                else:
                    combined = pd.Series(dtype=float)
                score_percents_combined_forecasted[score_val] = combined
            
            score_traces = []
            for score_val, color, score_name in zip([0, 25, 50, 75, 100], ['#ba1535', '#ba6715', '#b7ba15', '#43ba15', '#158cba'], ['Hate', 'Dislike', 'Neutral', 'Like', 'Love']): 
                score_traces.append(
                    go.Bar(
                        x=score_percents_historical[score_val].index,
                        y=score_percents_historical[score_val].values,
                        name=score_name,
                        marker_color=color,
                        showlegend=show_legend,
                        legendgroup = score_name
                    )
                )
                score_traces.append(
                    go.Bar(
                        x=score_percents_combined_forecasted[score_val].index,
                        y=score_percents_combined_forecasted[score_val].values,
                        name=score_name,
                        marker_color=color,
                        opacity=0.7,
                        showlegend=False,
                        legendgroup = score_name
                    )
                )
            score_subplots.append((score_traces, min_forecasted_year, f"{city}, {state}"))
            # --- Score Average ---
            avg_score_historical = scored_historical_df.groupby('year')['score'].mean()
            # Take the average score for each of the score columns, then average across those averages by year
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            avg_scores_per_col = scored_combined_forecasted_df.groupby('year')[score_cols].mean()
            avg_score_forecasted = avg_scores_per_col.mean(axis=1)
            min_score_forecasted = avg_scores_per_col.min(axis=1)
            max_score_forecasted = avg_scores_per_col.max(axis=1)

            # Find the shared year between historical and forecasted
            if shared_year:
                total_days = num_days_shared_historical + num_days_shared_forecasted
                # Weighted average for mean
                hist_avg = avg_score_historical.loc[shared_year]
                fore_avg = avg_score_forecasted.loc[shared_year]
                weighted_avg = (
                    hist_avg * num_days_shared_historical + fore_avg * num_days_shared_forecasted
                ) / total_days
                avg_score_forecasted.loc[shared_year] = weighted_avg

                fore_min = min_score_forecasted.loc[shared_year]
                fore_max = max_score_forecasted.loc[shared_year]
                weighted_min = (
                    hist_avg * (num_days_shared_historical / total_days)
                    + fore_min * (num_days_shared_forecasted / total_days)
                )
                weighted_max = (
                    hist_avg * (num_days_shared_historical / total_days)
                    + fore_max * (num_days_shared_forecasted / total_days)
                )
                min_score_forecasted.loc[shared_year] = weighted_min
                max_score_forecasted.loc[shared_year] = weighted_max

                # Set the avg score historical for the shared year to the forecasted value
                avg_score_historical.loc[shared_year] = avg_score_forecasted.loc[shared_year]

            average_traces = [
                go.Scatter(
                    x=avg_score_historical.index, 
                    y=avg_score_historical.values, 
                    mode='lines', 
                    name='Historical', 
                    line=dict(color='#158cba', width=2),
                    showlegend=show_legend, 
                    legendgroup = 'avg_graphs__h'
                ),
                go.Scatter(
                    x=avg_score_forecasted.index, 
                    y=avg_score_forecasted.values, 
                    mode='lines', 
                    name='Forecasted', 
                    line=dict(color='#ba1535', width=2), 
                    showlegend=show_legend,
                    legendgroup = 'avg_graphs__f'
                ),
                go.Scatter(
                    name='Upper Bound',
                    x=max_score_forecasted.index,
                    y=max_score_forecasted.values,
                    mode='lines',
                    marker=dict(color="#444"),
                    line=dict(width=0),
                    showlegend=False, 
                    legendgroup = 'avg_graphs__f'
                ),
                go.Scatter(
                    name='Lower Bound',
                    x=min_score_forecasted.index,
                    y=min_score_forecasted.values,
                    marker=dict(color="#444"),
                    line=dict(width=0),
                    mode='lines',
                    fillcolor='rgba(68, 68, 68, 0.3)',
                    fill='tonexty',
                    showlegend=False, 
                    legendgroup = 'avg_graphs__f'
                )
            ]
            average_subplots.append((average_traces, f"{city}, {state}"))
            
            # --- Monthly Stacked ---
            scored_historical_df['month'] = scored_historical_df['date'].dt.month
            monthly_avg_hist = scored_historical_df.groupby(['year', 'month'])['score'].mean().reset_index()
            years_hist = sorted(monthly_avg_hist['year'].unique())
            n_hist = len(years_hist)
            hist_traces = []
            for i, year in enumerate(years_hist):
                year_data = monthly_avg_hist[monthly_avg_hist['year'] == year]
                fade = 0.2 + 0.8 * (i + 1) / n_hist
                hist_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'{year}', line=dict(color=f'rgba(21, 140, 186,{fade})', width=2), showlegend=show_legend, legendgroup = f'{year}')
                )
            
            scored_combined_forecasted_df['month'] = scored_combined_forecasted_df['date'].dt.month
            score_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('score_')]
            avg_scores_per_col = scored_combined_forecasted_df.groupby(['year', 'month'])[score_cols].mean()
            monthly_avg_fore = avg_scores_per_col.mean(axis=1).reset_index(name='score')
            years_fore = sorted(monthly_avg_fore['year'].unique())
            n_fore = len(years_fore)
            fore_traces = []
            for i, year in enumerate(years_fore):
                year_data = monthly_avg_fore[monthly_avg_fore['year'] == year]
                fade = 0.2 + 0.8 * (n_fore - i) / n_fore
                fore_traces.append(
                    go.Scatter(x=year_data['month'], y=year_data['score'], mode='lines', name=f'{year}', line=dict(color=f'rgba(186, 21, 53,{fade})', width=2), showlegend=show_legend, legendgroup = f'{year}')
                )
            monthly_stacked_subplots.append((hist_traces + fore_traces, f"{city}, {state}"))
            
            # --- Reason Distribution ---
            all_reasons = list(set(reasons_historical).union(set(reasons_combined_forecasted)))
            reason_counts_historical = {reason: scored_historical_df[scored_historical_df['reason'] == reason].groupby('year').size() for reason in all_reasons}
            
            # For combined forecasted df: get reason count for each reason_* column by year, then average per year for each reason
            reason_cols = [col for col in scored_combined_forecasted_df.columns if col.startswith('reason_')]
            years = scored_combined_forecasted_df['year'].unique()
            reason_counts_forecasted = {}
            reason_mins_forecasted = {}
            reason_maxs_forecasted = {}
            for reason in all_reasons:
                # For each year, count how many times this reason appears in any reason_* column
                yearly_means = []
                yearly_mins = []
                yearly_maxs = []
                for year in sorted(years):
                    df_year = scored_combined_forecasted_df[scored_combined_forecasted_df['year'] == year]
                    # Count occurrences of this reason in all reason_* columns for this year
                    mean_cnt = sum((df_year[col] == reason).sum() for col in reason_cols)  / len(reason_cols)
                    min_cnt = min((df_year[col] == reason).sum() for col in reason_cols) 
                    max_cnt = max((df_year[col] == reason).sum() for col in reason_cols) 
                    # Normalize by number of models (columns) to get average per year
                    yearly_means.append((year, mean_cnt))
                    yearly_mins.append((year, min_cnt))
                    yearly_maxs.append((year, max_cnt))
                # Convert to pandas Series for compatibility with plotting code
                reason_counts_forecasted[reason] = pd.Series(
                    [mean_cnt for year, mean_cnt in yearly_means],
                    index=[year for year, mean_cnt in yearly_means],
                    dtype=float
                )
                reason_mins_forecasted[reason] = pd.Series(
                    [min_cnt for year, min_cnt in yearly_mins],
                    index=[year for year, min_cnt in yearly_mins],
                    dtype=float
                )
                reason_maxs_forecasted[reason] = pd.Series(
                    [max_cnt for year, max_cnt in yearly_maxs],
                    index=[year for year, max_cnt in yearly_maxs],
                    dtype=float
                )

            # Find shared years between historical and forecasted
            if shared_year:
                for reason in all_reasons:
                    hist_series = reason_counts_historical.get(reason)
                    if hist_series is not None:
                        # Add to forecasted series if it exists, else create a new one
                        for forecast_dict in [
                            reason_counts_forecasted,
                            reason_mins_forecasted,
                            reason_maxs_forecasted
                        ]:
                            forecast_series = forecast_dict.get(reason)
                            if forecast_series is not None:
                                # Add historical to forecasted, aligning on index
                                combined_series = forecast_series.add(hist_series.astype(float), fill_value=0)
                            else:
                                # If no forecast data, just use the historical
                                combined_series = hist_series.astype(float).copy()
                            forecast_dict[reason] = combined_series
                    if reason in reason_counts_forecasted:
                        updated_forecast_series = reason_counts_forecasted[reason]
                        if reason in reason_counts_historical:
                            historical_series = reason_counts_historical[reason]
                            # Align and update matching year values only
                            historical_series.update(updated_forecast_series.loc[historical_series.index].astype(float))
                        else:
                            # If the reason wasn't in historical, create a new one with only the years from forecasted
                            reason_counts_historical[reason] = updated_forecast_series.copy()

                
            # Define theme colors for consistent coloring
            reason_to_color = {
                "neutral": "#158cba",
                "too hot, humid": "#3f15ba",
                "too hot, dry": "#7a15ba",
                "too cold, windy": "#ba15a1",
                "too cold, still": "#ba1535",
                "ideal sunny": "#ba6715",
                "ideal overcast": "#b7ba15",
                "light rain": "#43ba15",
                "heavy rain": "#15ba67",
                "snow": "#15b7ba"
            }            
            reason_traces = []
            for reason, color in reason_to_color.items():
                added_trace = False  # Track whether we’ve added at least one visible trace

                # Historical trace (solid line)
                hist_data = reason_counts_historical.get(reason)
                if hist_data is not None and not hist_data.empty:
                    reason_traces.append(
                        go.Scatter(
                            x=hist_data.index,
                            y=hist_data.values,
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=show_legend, 
                            legendgroup = reason
                        )
                    )
                    added_trace = True

                # Forecasted trace (dotted line)
                forecast_data = reason_counts_forecasted.get(reason)
                forecast_mins = reason_mins_forecasted.get(reason)
                forecast_maxs = reason_maxs_forecasted.get(reason)
                if forecast_data is not None and forecast_mins is not None and forecast_maxs is not None and not forecast_data.empty:
                    reason_traces.append(
                        go.Scatter(
                            x=forecast_mins.index,
                            y=forecast_mins.values,
                            mode='lines',
                            name='Lower Bound '+reason,
                            line=dict(width=0),
                            marker=dict(color=color),
                            showlegend=False,  # Only show legend if no historical
                            legendgroup = reason
                        )
                    )
                    reason_traces.append(
                        go.Scatter(
                            name='Upper Bound '+reason,
                            x=forecast_maxs.index,
                            y=forecast_maxs.values,
                            marker=dict(color=color),
                            line=dict(width=0),
                            mode='lines',
                            fillcolor=hex_to_rgba(color, 0.3),
                            fill='tonexty',
                            showlegend=False, 
                            legendgroup = reason
                        )
                    )
                    reason_traces.append(
                        go.Scatter(
                            x=forecast_data.index,
                            y=forecast_data.values,
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=not added_trace and show_legend,  # Only show legend if no historical
                            legendgroup = reason
                        )
                    )
                    added_trace = True

                # If no data at all, add a dummy invisible trace to lock in the color
                else:
                    reason_traces.append(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode='lines',
                            name=reason,
                            line=dict(dash='solid', color=color),
                            marker=dict(color=color),
                            showlegend=show_legend,
                            legendgroup = reason
                        )
                    )
            reason_subplots.append((reason_traces, f"{city}, {state}"))
            
            # --- PM2.5 ---
            pm25_df['year'] = pd.to_datetime(pm25_df['date']).dt.year
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
                    mask = (pm25_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'].notna())
                else:
                    mask = (pm25_df['pm2_5__micrograms_per_cubic_metre'] >= min_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'] < max_val) & (pm25_df['pm2_5__micrograms_per_cubic_metre'].notna())
                yearly_counts = pm25_df[mask].groupby('year').size()
                total_hours_per_year = pm25_df[pm25_df['pm2_5__micrograms_per_cubic_metre'].notna()].groupby('year').size()
                pm25_data[category] = (yearly_counts / total_hours_per_year * 100)

            pm25_traces = []
            for category, color in zip(['Healthy', 'Moderate', 'Unhealthy for Sensitive', 'Unhealthy', 'Hazardous'], ['green', 'yellow', 'orange', 'red', 'purple']):
                pm25_traces.append(
                    go.Bar(
                        x=pm25_data[category].index,
                        y=pm25_data[category].values,
                        name=category,
                        marker_color=color,
                        showlegend=show_legend,
                        legendgroup = category
                    )
                )
            pm25_subplots.append((pm25_traces, f"{city}, {state}"))
            
            
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
    for i, (traces, min_forecasted_year, label) in enumerate(score_subplots):
        for trace in traces:
            score_fig.add_trace(trace, row=1, col=i+1)
        score_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=0, y1=100, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
        score_fig.update_layout(legend_tracegroupgap=2)
    score_fig.update_layout(
        title='Score Distribution by Year', 
        barmode='stack'
    )
    # Apply x/y axis titles to all subplots
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        score_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Percentage of Days'} if i == 1 else {},
        })
    score_fig.update_layout(legend_tracegroupgap=2)

    # Score Average
    avg_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(average_subplots):
        for trace in traces:
            avg_fig.add_trace(trace, row=1, col=i+1)
        avg_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=20, y1=90, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
    avg_fig.update_layout(
        title='Score Average by Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        avg_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Score Average'} if i == 1 else {},
        })
    avg_fig.update_layout(legend_tracegroupgap=2)

    # Monthly Stacked
    monthly_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(monthly_stacked_subplots):
        for trace in traces:
            monthly_fig.add_trace(trace, row=1, col=i+1)
        monthly_fig.add_shape(
            dict(type='line', x0=5, x1=5, y0=0, y1=100, yref='paper', line={'dash': 'dash', 'color': 'rgba(0, 0, 0, 0)'}),
            row=1, col=i+1
        )
    monthly_fig.update_layout(
        title='Monthly Average Stacked Scores by Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        monthly_fig.update_layout({
            xaxis_name: {
                'title': 'Month',
                'tickmode':'array',
                'tickvals':list(range(1, 13)),
                'ticktext':["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            },
            yaxis_name: {'title': 'Average Score'} if i == 1 else {},
        })
    monthly_fig.update_layout(legend_tracegroupgap=2)
    
    monthly_fig.update_layout(
        yaxis_title="Your Y-Axis Label"
    )

    # Reason Distribution
    reason_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(reason_subplots):
        for trace in traces:
            reason_fig.add_trace(trace, row=1, col=i+1)
        reason_fig.add_shape(
            dict(type='line', x0=min_forecasted_year, x1=min_forecasted_year, y0=0, y1=250, yref='paper', line={'dash': 'dash', 'color': 'black'}),
            row=1, col=i+1
        )
    reason_fig.update_layout(
        title='Number of Days by Type (Reason) per Year'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        reason_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Number of Days'} if i == 1 else {},
        })
    reason_fig.update_layout(legend_tracegroupgap=2)

    # PM2.5
    pm25_fig = make_subplots(rows=1, cols=n_cities, subplot_titles=subplot_titles)
    for i, (traces, label) in enumerate(pm25_subplots):
        for trace in traces:
            pm25_fig.add_trace(trace, row=1, col=i+1)
    pm25_fig.update_layout(
        title='PM2.5 Air Quality Distribution by Year', 
        barmode='stack'
    )
    for i in range(1, n_cities + 1):
        xaxis_name = 'xaxis' if i == 1 else f'xaxis{i}'
        yaxis_name = 'yaxis' if i == 1 else f'yaxis{i}'
        pm25_fig.update_layout({
            xaxis_name: {'title': 'Year'},
            yaxis_name: {'title': 'Percentage of Hours'} if i == 1 else {},
        })
    pm25_fig.update_layout(legend_tracegroupgap=2)

    # Build the map
    map_trace = go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers+text',
        marker=go.scattermap.Marker(size=14, color='#158cba'),
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
    return score_fig, avg_fig, monthly_fig, reason_fig, pm25_fig, map_figure, status_children, gemini_text, location_gemini_div

# Run the app
if __name__ == '__main__':
    app.run(debug=True)