# Personal Climate Score Dashboard

## Table of Contents
[Overview](#overview)

[Motivation](#motivation)

[Key Features](#key-features) 

[How It Works](#how-it-works)

&nbsp;&nbsp;&nbsp;&nbsp;[Data sources](#data-sources) 

&nbsp;&nbsp;&nbsp;&nbsp;[Personalized Scoring Algorithm](#personalized-scoring-algorithm)

&nbsp;&nbsp;&nbsp;&nbsp;[Data Visualization](#data-visualization) 

&nbsp;&nbsp;&nbsp;&nbsp;[Caching System](#caching-system)

&nbsp;&nbsp;&nbsp;&nbsp;[AI Integration](#ai-integration)

&nbsp;&nbsp;&nbsp;&nbsp;[User Interface](#user-interface)

[Technical Architecture](#technical-architecture)

[Limitations](#limitations)

[Setup instructions](#setup-instructions) 


## Overview
The **Personal Climate Score Dashboard** is an interactive web application that helps users compare the climate and environmental conditions of up to three US cities based on their personal weather preferences. It provides personalized climate scoring that takes into account both historical weather patterns and future climate projections, helping users make informed decisions about where they might want to live based on their climate preferences.

## Motivation
This work is motivated by a desire to move beyond broad descriptions of locations and to look at weather conditions through the lens of personal preference. This application organizes several data sources and processes them to enable key use cases: 
- **Relocation Planning and Decision-making**: Understanding climate differences between potential new cities and finding locations that match individual preferences
- **Climate Adaptation**: Seeing how weather patterns might change in the future in current location to drive adaptation decisions (like installing heating, cooling, or insulation)
- **Research**: Analyzing historical climate trends and future projections

In the face of a changing climate, questions about where to live, buy property, and adapt our lifestyles are increasingly pressing. Hopefully this tool enables users to face them with more confidence.

## Key Features

- **Multi-City Comparison**: Compare up to three US cities simultaneously
- **Personalized Scoring**: Customizable weather preferences with 5-point scale ratings (Hate to Love)
- **Historical Analysis**: 10+ years of historical weather data for each city
- **Future Projections**: Climate model forecasts up to 25 years into the future
- **Air Quality Tracking**: PM2.5 air quality data and trends
- **Natural Disaster Risk Assessment**: Consideration of flooding, wildfire, smoke, earthquake, hurricane, and tornado risks
- **AI-Powered Recommendations**: Integration with Google Gemini AI for location suggestions and analysis

## How It Works

### Data sources
This app pulls data from four different OpenMeteo APIs: 
- [Geocoding API](https://open-meteo.com/en/docs/geocoding-api) is used to get the latitude/longitude from user-provided input so that other API's (which depend on lat/long) can be used
- [Climate Change API](https://open-meteo.com/en/docs/climate-api) which returns predicted weather conditions in the future on day-level granularity for several different climate models. Based on the requirements of the personalized climate score model, which requires information about humidity and snowfall, there are three models that can be used: MRI-AGCM3-2-S, EC_Earth3P_HR and NICAM16_8S. Predictions are retrieved from all three.
- [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) which returns historical observed weather data for a given latitude/longitude either on an hourly or daily scale. In this application, we use daily data.
- [Air Quality API](https://open-meteo.com/en/docs/air-quality-api) which returns historical PM 2.5 

### Personalized Scoring Algorithm
The app uses a scoring system that evaluates daily weather conditions based on a user's personal preferences:

**Temperature Preferences:**
- Ideal temperature range (default: 60-90°F)
- Sunny day enjoyment level
- Cold weather tolerance (with and without wind)
- Hot humid day tolerance (defined as a dewpoint at or above 60°F, commonly recognized in meteorology at the point at which it feels "humid")
- Dry heat tolerance (dewpoint below 60°F)

**Weather Condition Preferences:**
- Light rain, heavy rain, and snow preferences
- Overcast day preferences
- Time window weighting (default: 8 AM to 8 PM)

**Scoring Logic:**
Each day receives a score from 0-100 based on:
- Primary weather conditions (temperature, humidity, wind)
- Secondary factors (precipitation, cloud cover)
- User preference coefficients (-2 to +2 scale)
- Time window scaling factor

### Data Visualization
The app generates multiple interactive charts for each city:
- **Geographic Map**: Visual representation of selected cities
- **Score Distribution**: Percentage of days with each score each year (both historical and predicted)
- **Score Averages**: Annual average climate scores over time, with possible ranges based on several forward-looking models
- **Monthly Patterns**: Seasonal climate score variations, with historical and forecasted years both displayed
- **Reason Analysis**: Breakdown of why days received specific scores
- **Air Quality Trends**: PM2.5 concentration patterns over time

### Caching System
To improve performance and reduce API calls, the app implements a comprehensive caching system:
- Weather data cached locally with city/state/model-specific filenames
- Score calculations cached based on parameter hashes
- Automatic cache invalidation when parameters change

### AI Integration
The app leverages Google Gemini AI to provide:
- **Location Recommendations**: Suggests 3-5 cities that match user preferences
- **Location Analysis**: Detailed analysis of how specific cities align with user preferences
- **Natural Language Explanations**: Conversational insights about climate suitability

### User Interface
Built with Dash and Bootstrap, the interface provides:
- Intuitive sliders and dropdowns for preference setting
- Real-time parameter validation
- Responsive design for different screen sizes
- Clear visual feedback and status updates

## Technical Architecture

- **Frontend**: Dash (Python web framework) with Plotly for interactive visualizations
- **Backend**: Python with pandas for data processing
- **Data Sources**: Open-Meteo APIs for weather and climate data
- **AI**: Google Gemini API for intelligent recommendations
- **Caching**: Local file-based caching system
- **Deployment**: Flask server with Bootstrap styling

## Limitations

- Climate projections have inherent uncertainty and should be used as guidance rather than predictions
- Air quality data availability varies by location and time period
- The app focuses on US cities only
- Natural disaster risk assessment is qualitative and should be supplemented with additional research

## Setup instructions 
Before setup, do the following:
- Make sure you have Python 3.x installed
- If you want to use AI features, get a [Gemini API key](https://ai.google.dev/gemini-api/docs)

To set up this app on your personal machine, run the following command lines from your desired working directory, replacing your-api-key with the Gemini API key you generated above. 
```
git clone https://github.com/cb92/personal-climate-score
cd personal-climate-score
pip install -r requirements.txt
echo "GEMINI_API_KEY='your-api-key'" > .env
python app.py
```
Once the app is running, put the link into your browser window (something like `http://127.0.0.1:PORTNUMBER/`) to interact with the app

Note that running this app will cause files to be written to a folder called `cache/` in your working directory.

