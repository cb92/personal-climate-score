from openmeteo_sdk.Unit import Unit
from openmeteo_sdk.Variable import Variable
import pandas as pd
import numpy as np

import datetime as dt
from datetime import date
import requests
import openmeteo_requests

import os
import hashlib
import json
import functools
import mysql.connector


class Score:
    """
    A class to manage climate match score parameters and preferences.
    """
    
    # Valid coefficient values
    VALID_COEFFICIENTS = [-2, -1, 0, 1, 2]
    
    def __init__(self):
        # Time window preferences (default: 8 AM to 8 PM)
        # what hours of the day matter the most to you for being outside?
        self.min_time = "08:00:00"
        self.max_time = "20:00:00"
        self._calculate_scaling_factor()
        
        # Temperature preferences
        self.ideal_temp__min = 60
        self.ideal_temp__max = 90
        self.ideal_sunny_day__coef = 2
        
        # Overcast day preferences
        self.overcast_dry__coef = 1  # 0 = neutral
        
        # Cold weather preferences
        self.too_cold_still__max = 30
        self.too_cold_still__coef = -1
        self.too_cold_windy__max = 35
        self.too_cold_windy__coef = -2
        
        # Humidity preferences
        self.humid_day_max = 80
        self.humid_day_coef = -2
        
        # Precipitation preferences
        self.light_rain__coef = 1  # 0 = neutral
        self.heavy_rain__coef = -1  # 0 = neutral
        self.snow_coef = 0
        
        # Dry heat preferences
        self.dry_heat_day_min = 95
        self.dry_heat_day_coef = -1
    
    def _calculate_scaling_factor(self):
        """Calculate scaling factor based on time window."""
        t1 = dt.datetime.strptime(self.min_time, "%H:%M:%S")
        t2 = dt.datetime.strptime(self.max_time, "%H:%M:%S")
        hours_diff = (t2 - t1).seconds / 3600
        self.scaling_factor = hours_diff / 24
    
    def _validate_coefficient(self, value, param_name):
        """Validate that a coefficient is in the allowed range."""
        if value not in self.VALID_COEFFICIENTS:
            raise ValueError(f"{param_name} must be one of {self.VALID_COEFFICIENTS}, got {value}")
        return value
    
    def set_time_window(self, min_time, max_time):
        """Set the time window for scoring and recalculate scaling factor."""
        self.min_time = min_time
        self.max_time = max_time
        self._calculate_scaling_factor()
    
    def set_temperature_preferences(self, ideal_min, ideal_max, sunny_coef):
        """Set ideal temperature range and sunny day coefficient."""
        self.ideal_temp__min = ideal_min
        self.ideal_temp__max = ideal_max
        self.ideal_sunny_day__coef = self._validate_coefficient(sunny_coef, "sunny_coef")
    
    def set_overcast_preference(self, coef):
        """Set preference for overcast but dry days."""
        self.overcast_dry__coef = self._validate_coefficient(coef, "overcast_coef")
    
    def set_cold_weather_preferences(self, too_cold_still_max, too_cold_still_coef, 
                                   too_cold_windy_max, too_cold_windy_coef):
        """Set cold weather thresholds and coefficients."""
        self.too_cold_still__max = too_cold_still_max
        self.too_cold_still__coef = self._validate_coefficient(too_cold_still_coef, "too_cold_still_coef")
        self.too_cold_windy__max = too_cold_windy_max
        self.too_cold_windy__coef = self._validate_coefficient(too_cold_windy_coef, "too_cold_windy_coef")
    
    def set_humidity_preferences(self, humid_max, humid_coef):
        """Set humidity threshold and coefficient."""
        self.humid_day_max = humid_max
        self.humid_day_coef = self._validate_coefficient(humid_coef, "humid_coef")
    
    def set_precipitation_preferences(self, light_rain_coef, heavy_rain_coef, snow_coef):
        """Set precipitation preferences."""
        self.light_rain__coef = self._validate_coefficient(light_rain_coef, "light_rain_coef")
        self.heavy_rain__coef = self._validate_coefficient(heavy_rain_coef, "heavy_rain_coef")
        self.snow_coef = self._validate_coefficient(snow_coef, "snow_coef")
    
    def set_dry_heat_preferences(self, dry_heat_min, dry_heat_coef):
        """Set dry heat preferences."""
        self.dry_heat_day_min = dry_heat_min
        self.dry_heat_day_coef = self._validate_coefficient(dry_heat_coef, "dry_heat_coef")
    
    def get_all_parameters(self):
        """Return all parameters as a dictionary."""
        return {
            'min_time': self.min_time,
            'max_time': self.max_time,
            'scaling_factor': self.scaling_factor,
            'ideal_temp__min': self.ideal_temp__min,
            'ideal_temp__max': self.ideal_temp__max,
            'ideal_sunny_day__coef': self.ideal_sunny_day__coef,
            'overcast_dry__coef': self.overcast_dry__coef,
            'too_cold_still__max': self.too_cold_still__max,
            'too_cold_still__coef': self.too_cold_still__coef,
            'too_cold_windy__max': self.too_cold_windy__max,
            'too_cold_windy__coef': self.too_cold_windy__coef,
            'humid_day_max': self.humid_day_max,
            'humid_day_coef': self.humid_day_coef,
            'light_rain__coef': self.light_rain__coef,
            'heavy_rain__coef': self.heavy_rain__coef,
            'snow_coef': self.snow_coef,
            'dry_heat_day_min': self.dry_heat_day_min,
            'dry_heat_day_coef': self.dry_heat_day_coef
        }
    
    def set_all_parameters(self, params_dict):
        """Set all parameters from a dictionary."""
        for key, value in params_dict.items():
            if hasattr(self, key):
                if key.endswith('_coef'):
                    # Validate coefficients
                    setattr(self, key, self._validate_coefficient(value, key))
                else:
                    setattr(self, key, value)
        
        # Recalculate scaling factor if time window changed
        if 'min_time' in params_dict or 'max_time' in params_dict:
            self._calculate_scaling_factor()


####### Helper functions to extract information from the API response
def get_unit_name(unit_value):
    for name, value in Unit.__dict__.items():
        if value == unit_value and not name.startswith("__"):
            return name
    return f"unknown({unit_value})"


def get_variable_name(var_value):
    for name, value in Variable.__dict__.items():
        if value == var_value and not name.startswith("__"):
            return name
    return f"unknown({var_value})"

def hex_to_rgba(hex_color, alpha):
    """Converts a hex color code to an RGBA string with specified alpha."""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def extract_data_from_api_response(timeseries, cols, hourly = True, timezone = 'America/Los_Angeles'):
	if hourly:
		datetime_index = pd.date_range(
		    start=pd.to_datetime(timeseries.Time(), unit="s", utc=True),
		    end=pd.to_datetime(timeseries.TimeEnd(), unit="s", utc=True),
		    freq=pd.Timedelta(seconds=timeseries.Interval()),
		    inclusive="left"
		)

		# Convert DatetimeIndex to timezone-aware datetime
		datetime_index = datetime_index.tz_convert(timezone)  # e.g., "America/Los_Angeles"

		# Construct DataFrame from converted index
		df_dict = {}
		df_dict["datetime"] = datetime_index
		df_dict["date"] = datetime_index.date
		df_dict["time"] = datetime_index.time
	else: 
		datetime_index = pd.date_range(
		    start=pd.to_datetime(timeseries.Time(), unit="s", utc=True),
		    end=pd.to_datetime(timeseries.TimeEnd(), unit="s", utc=True),
		    freq=pd.Timedelta(seconds=timeseries.Interval()),
		    inclusive="left"
		)
		df_dict = {}
		df_dict["datetime"] = datetime_index
		df_dict["date"] = datetime_index.date

	i = 0
	while True:
		try: 
			col_name = cols[i] + "__" + \
				get_unit_name(timeseries.Variables(i).Unit())
			df_dict[col_name] = timeseries.Variables(i).ValuesAsNumpy()
			i+=1
			continue
		except:
			break
	return pd.DataFrame(data = df_dict)


####### Helper functions to calculate the climate score
def f_to_c(fahrenheit):
	return (fahrenheit - 32)*5/9


def daily_climate_score__hourly(temperature_arr, 
								dew_point_arr, 
								rain_arr, 
								snowfall_arr, 
								wind_arr, 
								cloud_cover_arr,
								score_obj):
	score = 0
	reason = "neutral"
    #this if/elif loop should logically be disjoint
	if (np.max(temperature_arr) > f_to_c(score_obj.humid_day_max) and np.min(dew_point_arr) > f_to_c(60)):
		score = score_obj.humid_day_coef
		reason = "too hot, humid"
	elif (np.max(temperature_arr) > f_to_c(score_obj.dry_heat_day_min) and np.min(dew_point_arr) <= f_to_c(60)):
		score = score_obj.dry_heat_day_coef
		reason = "too hot, dry"
	elif (np.max(temperature_arr) < f_to_c(score_obj.too_cold_windy__max) and np.mean(wind_arr) > 30):
		score = score_obj.too_cold_windy__coef
		reason = "too cold, windy"
	elif (np.max(temperature_arr) < f_to_c(score_obj.too_cold_still__max) and np.mean(wind_arr) < 30):
		score = score_obj.too_cold_still__coef
		reason = "too cold, still"
	elif (np.max(temperature_arr) > f_to_c(score_obj.ideal_temp__min) and np.max(temperature_arr) < f_to_c(score_obj.ideal_temp__max)):
		if (np.mean(cloud_cover_arr) < 60 and np.sum(rain_arr) < 2):
			score = score_obj.ideal_sunny_day__coef
			reason = "ideal sunny"
		elif (np.mean(cloud_cover_arr) >=60 and np.sum(rain_arr) < 2):
			score = score_obj.overcast_dry__coef
			reason = "ideal overcast"
	# Precipitation overrides
	if (np.sum(rain_arr) >= 2 and np.sum(rain_arr) < 10):
		if reason == 'neutral':
			score = score_obj.light_rain__coef
			reason = 'light rain'
		else:
			prev_score = score
			score = np.min([score, score_obj.light_rain__coef])
			if score == score_obj.light_rain__coef or score < prev_score:
				reason = "light rain"
	elif (np.sum(rain_arr) >= 10):
		if reason == 'neutral':
			score = score_obj.heavy_rain__coef
			reason = "heavy rain"
		else:
			prev_score = score
			score = np.min([score, score_obj.heavy_rain__coef])
			if score == score_obj.heavy_rain__coef or score < prev_score:
				reason = "heavy rain"
	elif (np.sum(snowfall_arr) > 1):
		if reason == 'neutral':
			score = score_obj.snow_coef
			reason = "snow"
		else:
			prev_score = score
			score = np.min([score, score_obj.snow_coef])
			if score == score_obj.snow_coef or score < prev_score:
				reason = "snow"
	return (score + 2) * 25, reason

def daily_climate_score__daily(temperature_max, 
								dew_point_min,
								wind_mean,
								cloud_cover_mean,
								rain_sum, 
								snowfall_sum, 
								scaling_factor,
								score_obj):
	score = 0
	reason = "neutral"
	if (temperature_max > f_to_c(score_obj.humid_day_max) and dew_point_min > f_to_c(60)):
		score = score_obj.humid_day_coef
		reason = "too hot, humid"
	elif (temperature_max > f_to_c(score_obj.dry_heat_day_min) and dew_point_min <= f_to_c(60)):
		score = score_obj.dry_heat_day_coef
		reason = "too hot, dry"
	elif (temperature_max < f_to_c(score_obj.too_cold_windy__max) and wind_mean > 30):
		score = score_obj.too_cold_windy__coef
		reason = "too cold, windy"
	elif (temperature_max < f_to_c(score_obj.too_cold_still__max) and wind_mean < 30):
		score = score_obj.too_cold_still__coef
		reason = "too cold, still"
	elif (temperature_max > f_to_c(score_obj.ideal_temp__min) and temperature_max < f_to_c(score_obj.ideal_temp__max)):
		if (cloud_cover_mean < 60 and scaling_factor*rain_sum < 2):
			score = score_obj.ideal_sunny_day__coef
			reason = "ideal sunny"
		elif (cloud_cover_mean >=60 and scaling_factor*rain_sum < 2):
			score = score_obj.overcast_dry__coef
			reason = "ideal overcast"
	# Precipitation overrides
    # Precipitation overrides
	if (scaling_factor*rain_sum >=2 and scaling_factor*rain_sum < 10):
		if reason == 'neutral':
			score = score_obj.light_rain__coef
			reason = 'light rain'
		else:
			prev_score = score
			score = np.min([score, score_obj.light_rain__coef])
			if score == score_obj.light_rain__coef or score < prev_score:
				reason = "light rain"
	elif (scaling_factor*rain_sum >=10):
		if reason == 'neutral':
			score = score_obj.heavy_rain__coef
			reason = "heavy rain"
		else:
			prev_score = score
			score = np.min([score, score_obj.heavy_rain__coef])
			if score == score_obj.heavy_rain__coef or score < prev_score:
				reason = "heavy rain"
	elif (snowfall_sum > 1):
		if reason == 'neutral':
			score = score_obj.snow_coef
			reason = "snow"
		else:
			prev_score = score
			score = np.min([score, score_obj.snow_coef])
			if score == score_obj.snow_coef or score < prev_score:
				reason = "snow"
	return (score + 2) * 25, reason

def get_city_info(city, state):
    url = f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=100'
    response = requests.get(url)
    data = response.json()
    filtered_data = [item for item in data['results'] if item['country_code'] == 'US' and item['admin1'] == state]
    if not filtered_data:
        raise ValueError(f"No results found for {city}, {state}")
    info = filtered_data[0]
    return info['latitude'], info['longitude'], info['timezone'], info.get('population', None)


def get_historical_and_aqi_data(lat, long, city_timezone, city, state, col_names=None, save_todb=True):
    if col_names is None:
        col_names = [
            "temperature_2m_max", "dew_point_2m_min", "rain_sum", "snowfall_sum", "cloud_cover_mean", "wind_speed_10m_mean"
        ]
    # Check database first
    city_id = get_or_create_city_id(city, state, lat, long, city_timezone)
    if city_id is not None:
        db_weather = load_historical_weather(city_id)
        db_pm25 = load_historical_aqi(city_id, city_timezone)
        if db_weather is not None and db_pm25 is not None:
            print(f"Loading historical daily weather and pm2.5 for {city}, {state} from database")
            return db_weather, db_pm25

    print(f"Fetching historical daily weather for {city}, {state} from API...")
    openmeteo = openmeteo_requests.Client()

    # Historical daily weather
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": long,
        "start_date": date(date.today().year - 10, 1, 2),
        "end_date": date.today(),
        "daily": col_names,
        "timezone": 'GMT'
    }
    responses = openmeteo.weather_api(url, params=params)
    df_historical_weather = extract_data_from_api_response(responses[0].Daily(), col_names, hourly=False)

    # AQI (pm2.5, hourly)
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    aqi_col_names = ["pm2_5"]
    params = {
        "latitude": lat,
        "longitude": long,
        "hourly": aqi_col_names,
        "start_date": "2022-01-01",
        "end_date": date.today(),
        "timezone": 'GMT'
    }
    responses = openmeteo.weather_api(url, params=params)
    df_historical_aqi = extract_data_from_api_response(responses[0].Hourly(), aqi_col_names, timezone=city_timezone)

    # Save to database
    if save_todb and city_id is not None:
        save_historical_weather(city_id, df_historical_weather)
        save_historical_aqi(city_id, df_historical_aqi)

    return df_historical_weather, df_historical_aqi


def get_forecasted_data(lat, long, city_timezone, city, state, model, col_names=None, save_todb=True):
    if col_names is None:
        col_names = ["temperature_2m_max", "wind_speed_10m_mean", "dew_point_2m_min", "rain_sum", "cloud_cover_mean", "snowfall_sum"]
    
    # Check database first
    city_id = get_or_create_city_id(city, state, lat, long, city_timezone)
    if city_id is not None:
        db_df = load_forecasted_weather(city_id, [model])
        if db_df is not None:
            print(f"Loading forecasted data for {city}, {state} with model {model} from database")
            return db_df
    
    print(f"Fetching forecasted data for {city}, {state} with model {model} from API...")
    openmeteo = openmeteo_requests.Client()
    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": lat,
        "longitude": long,
        "start_date": date.today(),
        "end_date": date(date.today().year + 7, 12, 31),
        "models": model,
        "daily": col_names
    }
    responses = openmeteo.weather_api(url, params=params)
    df_single_model = extract_data_from_api_response(responses[0].Daily(), col_names, hourly=False, timezone=city_timezone)
    df_single_model.columns = [
        col if col == 'date' else col + f'__{model}'
        for col in df_single_model.columns
    ]
    
    # Save to database
    if save_todb and city_id is not None:
        save_forecasted_weather(city_id, model, df_single_model)
    return df_single_model


def process_historical_for_plotting(df, climate_score, city=None, state=None):
    # Check database first if city and state are provided
    city_id = get_city_id(city, state) if city and state else None
    score_params = climate_score.get_all_parameters()
    if city_id is not None:
        db_df = load_historical_scores(city_id, score_params)
        if db_df is not None:
            print(f"Loading historical score data for {city}, {state} from database")
            return db_df

    print("Processing historical daily data for plotting...")
    df["date"] = df["date"].astype(str)
    scores = []
    for idx, row in df.iterrows():
        # Use daily scoring function
        score, reason = daily_climate_score__daily(
            row["temperature_2m_max__celsius"],
            row["dew_point_2m_min__celsius"],
            row["wind_speed_10m_mean__kilometres_per_hour"],
            row["cloud_cover_mean__percentage"],
            row["rain_sum__millimetre"],
            row["snowfall_sum__centimetre"],
            climate_score.scaling_factor,
            climate_score
        )
        scores.append((row["date"], score, reason))
    score_df = pd.DataFrame(scores, columns=["date", "score", "reason"])
    score_df["date"] = pd.to_datetime(score_df["date"])
    score_df["year"] = score_df["date"].dt.year

    # Save to database if city and state are provided
    if city_id is not None:
        save_historical_scores(city_id, score_params, score_df)

    return score_df


def process_forecasted_for_plotting(df, climate_score, model="NICAM16_8S", city=None, state=None):
    # Check database first if city and state are provided
    city_id = get_city_id(city, state) if city and state else None
    score_params = climate_score.get_all_parameters()
    if city_id is not None:
        db_df = load_forecasted_scores(city_id, score_params, [model])
        if db_df is not None:
            print(f"Loading forecasted score data for {city}, {state} with model {model} from database")
            db_df = db_df[["date", "score", "reason", "year"]]
            return db_df, db_df["reason"].tolist()
    
    print(f"Processing forecasted data for plotting with model {model}...")
    df["date"] = df["date"].astype(str)
    scores_forecasted = []
    for index, row in df.iterrows():
        date_val = row['date']
        score, reason = daily_climate_score__daily(
            row[f'temperature_2m_max__celsius__{model}'],
            row[f'dew_point_2m_min__celsius__{model}'],
            row[f'wind_speed_10m_mean__kilometres_per_hour__{model}'],
            row[f'cloud_cover_mean__percentage__{model}'],
            row[f'rain_sum__millimetre__{model}'],
            row[f'snowfall_sum__centimetre__{model}'],
            climate_score.scaling_factor,
            climate_score)
        scores_forecasted.append((date_val, score, reason))
    score_df_forecasted = pd.DataFrame(scores_forecasted, columns=["date", "score", "reason"])
    score_df_forecasted["date"] = pd.to_datetime(score_df_forecasted["date"])
    score_df_forecasted["year"] = score_df_forecasted["date"].dt.year
    
    # Save to database if city and state are provided
    if city_id is not None:
        save_forecasted_scores(city_id, score_params, model, score_df_forecasted)
    
    return score_df_forecasted


def get_combined_forecasted_data(lat, long, city_timezone, city, state, models=None, col_names=None, save_todb=True):
    """
    Fetch forecasted data for multiple models and return a combined dataframe.
    
    Args:
        lat, long: coordinates
        city_timezone: timezone string
        city, state: location identifiers
        models: list of model names to fetch data for
        col_names: list of column names to fetch
        save_csv: whether to save to the database
    
    Returns:
        combined_df: DataFrame with date/year columns and model-specific score/reason columns
        None (kept so the return shape is unchanged)
    """
    if models is None:
        models = ["EC_Earth3P_HR", "MRI_AGCM3_2_S", "NICAM16_8S"]
    if col_names is None:
        col_names = ["temperature_2m_max", "wind_speed_10m_mean", "dew_point_2m_min", "rain_sum", "cloud_cover_mean", "snowfall_sum"]
    
    # Check database first
    city_id = get_or_create_city_id(city, state, lat, long, city_timezone)
    if city_id is not None:
        db_df = load_forecasted_weather(city_id, models)
        if db_df is not None:
            db_df['year'] = pd.to_datetime(db_df['date']).dt.year
            print(f"Loading combined forecasted data for {city}, {state} from database")
            return db_df
    
    print(f"Fetching combined forecasted data for {city}, {state} with models {models} from API...")
    openmeteo = openmeteo_requests.Client()
    
    # Fetch data for each model
    model_dataframes = {}
    for model in models:
        url = "https://climate-api.open-meteo.com/v1/climate"
        params = {
            "latitude": lat,
            "longitude": long,
            "start_date": date.today(),
            "end_date": date(date.today().year + 7, 12, 31),
            "models": model,
            "daily": col_names
        }
        responses = openmeteo.weather_api(url, params=params)
        df_model = extract_data_from_api_response(responses[0].Daily(), col_names, hourly=False, timezone=city_timezone)
        
        # Add model suffix to column names (except date)
        df_model.columns = [
            col if col == 'date' else col + f'__{model}'
            for col in df_model.columns
        ]
        model_dataframes[model] = df_model
    
    # Combine all model dataframes on date
    combined_df = model_dataframes[models[0]].copy()
    for model in models[1:]:
        combined_df = pd.merge(combined_df, model_dataframes[model], on='date', how='outer')
    
    # Add year column
    combined_df['year'] = pd.to_datetime(combined_df['date']).dt.year
    
    # Save to database
    if save_todb and city_id is not None:
        for model in models:
            save_forecasted_weather(city_id, model, combined_df)
    
    return combined_df


def process_combined_forecasted_for_plotting(df, climate_score, models=None, city=None, state=None):
    """
    Process combined forecasted data for plotting, generating scores for all models.
    
    Args:
        df: combined forecasted dataframe with model-specific columns
        climate_score: Score object with preferences
        models: list of model names
        city, state: location identifiers for database storage
    
    Returns:
        processed_df: DataFrame with date, year, and model-specific score/reason columns
    """
    if models is None:
        models = ["EC_Earth3P_HR", "MRI_AGCM3_2_S", "NICAM16_8S"]
    
    # Check database first if city and state are provided
    city_id = get_city_id(city, state) if city and state else None
    score_params = climate_score.get_all_parameters()
    if city_id is not None:
        db_long = load_forecasted_scores(city_id, score_params, models)
        if db_long is not None:
            print(f"Loading combined forecasted score data for {city}, {state} from database")
            combined_db_df = db_long[['date', 'year']].drop_duplicates('date').reset_index(drop=True)
            for model in models:
                by_date = db_long[db_long['model_name'] == model].set_index('date')
                combined_db_df[f'score_{model}'] = combined_db_df['date'].map(by_date['score'])
                combined_db_df[f'reason_{model}'] = combined_db_df['date'].map(by_date['reason'])
            return combined_db_df
    
    print(f"Processing combined forecasted data for plotting with models {models}...")
    
    # Initialize result dataframe with date and year
    result_df = df[['date', 'year']].copy()
    
    # Process each model
    for model in models:
        scores_model = []
        reasons_model = []
        
        for idx, row in df.iterrows():
            # Use daily scoring function for each model
            score, reason = daily_climate_score__daily(
                row[f'temperature_2m_max__celsius__{model}'],
                row[f'dew_point_2m_min__celsius__{model}'],
                row[f'wind_speed_10m_mean__kilometres_per_hour__{model}'],
                row[f'cloud_cover_mean__percentage__{model}'],
                row[f'rain_sum__millimetre__{model}'],
                row[f'snowfall_sum__centimetre__{model}'],
                climate_score.scaling_factor,
                climate_score
            )
            scores_model.append(score)
            reasons_model.append(reason)
        
        # Add model-specific columns
        result_df[f'score_{model}'] = scores_model
        result_df[f'reason_{model}'] = reasons_model
        
    # Save to database if city and state are provided
    if city_id is not None:
        for model in models:
            model_df = pd.DataFrame({
                'date': result_df['date'], 'year': result_df['year'],
                'score': result_df[f'score_{model}'], 'reason': result_df[f'reason_{model}']
            })
            save_forecasted_scores(city_id, score_params, model, model_df)
    
    return result_df


####### Database access (schema in setup.sql)
# Connection settings come from RAILWAY_DB_HOST / _PORT / _USER / _PASSWORD / _NAME in the environment (.env).
# Every value is passed to MySQL as a bound %s parameter. The only text that is ever formatted into a query is
# module constants (table/column names) and "%s" placeholder lists, never user input.
WEATHER_COLS = [
    "temperature_2m_max__celsius", "dew_point_2m_min__celsius", "rain_sum__millimetre",
    "snowfall_sum__centimetre", "cloud_cover_mean__percentage", "wind_speed_10m_mean__kilometres_per_hour"
]
AQI_COL = "pm2_5__micrograms_per_cubic_metre"


def _db_safe(fn):
    """On any database error, print it and return None so callers fall back to the API."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"Database error in {fn.__name__}: {e}")
            return None
    return wrapper


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("RAILWAY_DB_HOST"),
        port=int(os.getenv("RAILWAY_DB_PORT", "3306")),
        user=os.getenv("RAILWAY_DB_USER"),
        password=os.getenv("RAILWAY_DB_PASSWORD"),
        database=os.getenv("RAILWAY_DB_NAME"),
    )


def _query_df(sql, params=()):
    """Run a parameterized SELECT and return the rows as a DataFrame."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return pd.DataFrame(cur.fetchall(), columns=cur.column_names)
    finally:
        conn.close()


def _execute_many(statements):
    """Run [(parameterized_sql, list_of_row_tuples), ...] in a single transaction."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        for sql, rows in statements:
            cur.executemany(sql, rows)
        conn.commit()
        return True
    finally:
        conn.close()


def _py(v):
    """numpy/pandas scalar -> plain Python value (NaN -> None) so MySQL accepts it."""
    if v is None or pd.isna(v):
        return None
    return v.item() if hasattr(v, "item") else v


def _config_hash(score_params):
    return hashlib.md5(json.dumps(score_params, sort_keys=True).encode()).hexdigest()


def _config_statement(score_params):
    p = score_params
    return (
        "INSERT INTO score_configurations (config_hash, parameters_json, min_time, max_time, scaling_factor, "
        "ideal_temp_min, ideal_temp_max) VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE config_hash = config_hash",
        [(_config_hash(p), json.dumps(p, sort_keys=True), p["min_time"], p["max_time"], p["scaling_factor"],
          p["ideal_temp__min"], p["ideal_temp__max"])]
    )


@_db_safe
def get_city_id(city, state):
    """city_id for an existing city, or None."""
    df = _query_df("SELECT city_id FROM cities WHERE city_name = %s AND state_name = %s", (city, state))
    return int(df.iloc[0, 0]) if not df.empty else None


@_db_safe
def get_or_create_city_id(city, state, lat, long, timezone):
    _execute_many([(
        "INSERT INTO cities (city_name, state_name, latitude, longitude, timezone) VALUES (%s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE latitude = VALUES(latitude), longitude = VALUES(longitude), timezone = VALUES(timezone)",
        [(city, state, float(lat), float(long), timezone)]
    )])
    return get_city_id(city, state)


# ---- historical daily weather ----
@_db_safe
def save_historical_weather(city_id, df):
    days = pd.to_datetime(df["date"]).dt.date
    rows = [(city_id, day) + tuple(_py(v) for v in vals)
            for day, vals in zip(days, df[WEATHER_COLS].itertuples(index=False, name=None))]
    marks = ", ".join(["%s"] * (len(WEATHER_COLS) + 2))
    updates = ", ".join(f"{c} = VALUES({c})" for c in WEATHER_COLS)
    return _execute_many([(
        f"INSERT INTO historical_daily_weather (city_id, date, {', '.join(WEATHER_COLS)}) VALUES ({marks}) "
        f"ON DUPLICATE KEY UPDATE {updates}", rows
    )])


@_db_safe
def load_historical_weather(city_id):
    df = _query_df(f"SELECT date, {', '.join(WEATHER_COLS)} FROM historical_daily_weather "
                   "WHERE city_id = %s ORDER BY date", (city_id,))
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---- historical hourly pm2.5 (datetime stored in UTC so DST repeats can't collide; date is the local date) ----
@_db_safe
def save_historical_aqi(city_id, df):
    utc = pd.to_datetime(df["datetime"], utc=True)
    days = pd.to_datetime(df["date"]).dt.date
    rows = [(city_id, ts.to_pydatetime().replace(tzinfo=None), day, _py(v))
            for ts, day, v in zip(utc, days, df[AQI_COL])]
    return _execute_many([(
        f"INSERT INTO historical_hourly_aqi (city_id, datetime, date, {AQI_COL}) VALUES (%s, %s, %s, %s) "
        f"ON DUPLICATE KEY UPDATE date = VALUES(date), {AQI_COL} = VALUES({AQI_COL})", rows
    )])


@_db_safe
def load_historical_aqi(city_id, timezone):
    df = _query_df(f"SELECT datetime, date, {AQI_COL} FROM historical_hourly_aqi "
                   "WHERE city_id = %s ORDER BY datetime", (city_id,))
    if df.empty:
        return None
    df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("UTC").dt.tz_convert(timezone)
    df["date"] = pd.to_datetime(df["date"])
    df.insert(2, "time", df["datetime"].dt.time)
    return df


# ---- forecasted daily weather (one row per model per day; df columns are "<var>__<model>") ----
@_db_safe
def save_forecasted_weather(city_id, model, df):
    cols = [f"{c}__{model}" for c in WEATHER_COLS]
    sub = df[["date"] + cols].dropna(subset=cols, how="all")
    days = pd.to_datetime(sub["date"])
    rows = [(city_id, model, ts.date(), ts.year) + tuple(_py(v) for v in vals)
            for ts, vals in zip(days, sub[cols].itertuples(index=False, name=None))]
    marks = ", ".join(["%s"] * (len(WEATHER_COLS) + 4))
    updates = ", ".join(f"{c} = VALUES({c})" for c in ["year"] + WEATHER_COLS)
    return _execute_many([(
        f"INSERT INTO forecasted_daily_weather (city_id, model_name, date, year, {', '.join(WEATHER_COLS)}) "
        f"VALUES ({marks}) ON DUPLICATE KEY UPDATE {updates}", rows
    )])


@_db_safe
def load_forecasted_weather(city_id, models):
    """Wide frame (date + "<var>__<model>" columns) or None unless every requested model is stored."""
    marks = ", ".join(["%s"] * len(models))
    df = _query_df(f"SELECT model_name, date, {', '.join(WEATHER_COLS)} FROM forecasted_daily_weather "
                   f"WHERE city_id = %s AND model_name IN ({marks}) ORDER BY date", (city_id, *models))
    if df.empty or set(df["model_name"]) != set(models):
        return None
    out = None
    for model in models:
        part = df[df["model_name"] == model].drop(columns="model_name")
        part = part.rename(columns={c: f"{c}__{model}" for c in WEATHER_COLS})
        out = part if out is None else pd.merge(out, part, on="date", how="outer")
    out["date"] = pd.to_datetime(out["date"])
    return out.sort_values("date").reset_index(drop=True)


# ---- computed scores (keyed by city + hash of the Score parameters) ----
@_db_safe
def save_historical_scores(city_id, score_params, df):
    h = _config_hash(score_params)
    days = pd.to_datetime(df["date"])
    rows = [(city_id, h, ts.date(), ts.year, _py(sc), rs) for ts, sc, rs in zip(days, df["score"], df["reason"])]
    return _execute_many([_config_statement(score_params), (
        "INSERT INTO computed_historical_scores (city_id, config_hash, date, year, score, reason) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE year = VALUES(year), score = VALUES(score), reason = VALUES(reason)", rows
    )])


@_db_safe
def load_historical_scores(city_id, score_params):
    df = _query_df("SELECT date, score, reason, year FROM computed_historical_scores "
                   "WHERE city_id = %s AND config_hash = %s ORDER BY date", (city_id, _config_hash(score_params)))
    if df.empty:
        return None
    df["date"] = pd.to_datetime(df["date"])
    return df


@_db_safe
def save_forecasted_scores(city_id, score_params, model, df):
    """df has columns date, year, score, reason for a single model."""
    h = _config_hash(score_params)
    days = pd.to_datetime(df["date"])
    rows = [(city_id, h, model, ts.date(), ts.year, _py(sc), rs)
            for ts, sc, rs in zip(days, df["score"], df["reason"])]
    return _execute_many([_config_statement(score_params), (
        "INSERT INTO computed_forecasted_scores (city_id, config_hash, model_name, date, year, score, reason) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE year = VALUES(year), score = VALUES(score), reason = VALUES(reason)", rows
    )])


@_db_safe
def load_forecasted_scores(city_id, score_params, models):
    """Long frame (model_name, date, year, score, reason) or None unless every requested model is stored."""
    marks = ", ".join(["%s"] * len(models))
    df = _query_df("SELECT model_name, date, year, score, reason FROM computed_forecasted_scores "
                   f"WHERE city_id = %s AND config_hash = %s AND model_name IN ({marks}) ORDER BY date",
                   (city_id, _config_hash(score_params), *models))
    if df.empty or set(df["model_name"]) != set(models):
        return None
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_gemini_prompt(score: Score, additional_preferences=None, disaster_preferences=None):
    params = score.get_all_parameters()
    prompt = (
        "Based on your climate preferences below, suggest 3-5 locations (cities or regions, in the United States) "
        "that you might love, and 1-2 that you might dislike based on current information as well as any future projections. "
        "Be specific and explain your reasoning for each suggestion, using natural, conversational language. "
        "Avoid technical jargon, mentions of variable names, or phrases like 'the dry heat penalty would be triggered'; instead, say things like 'you'll experience few dry heat days' or 'there are many humid days'. "
        "Here are your preferences:\n"
    )
    for k, v in params.items():
        prompt += f"- {k}: {v}\n"
    if additional_preferences:
        prompt += ("\nYou also mentioned these additional preferences for places to live: "
                   f"{additional_preferences}\n")
    if disaster_preferences:
        prompt += "\nNatural disaster risk tolerance:\n"
        for disaster, tolerance in disaster_preferences.items():
            prompt += f"- {disaster}: {tolerance}\n"
    prompt += (
        "\nReturn your answer as a Markdown-formatted list, using bold headings for each location. For each, include a short explanation (1-3 sentences) of why it matches or does not match your preferences. "
        "Group your answer into two sections: 'Locations You Might Love' and 'Locations You Might Dislike'. "
        "Use clear bullet points and keep the language friendly, concise, and addressed directly to 'you'. "
        "Do not include locations outside the United States."
    )
    return prompt

def build_gemini_location_prompt(city, state, user_features=None, disaster_preferences=None):
    prompt = f"You are considering moving to {city}, {state}. Here are your preferences for places to live: "
    if user_features:
        prompt += f"{user_features}.\n"
    else:
        prompt += "climate preferences only.\n"
    
    if disaster_preferences:
        prompt += f"\nNatural disaster risk tolerance:\n"
        for disaster, tolerance in disaster_preferences.items():
            prompt += f"- {disaster}: {tolerance}\n"
    
    prompt += (
        f"\nAnalyze how well the location {city}, {state} matches these preferences currently and in the future. "
        "Be specific and concise. List which features are a good match, which are not, and any relevant context. "
        "If information is not available, say so. "
        "Return your answer as a Markdown-formatted list with bolded feature names and a short explanation for each, using language addressed directly to 'you'. "
        "Conclude with a brief summary (1-2 sentences) about the overall fit for you."
    )
    return prompt