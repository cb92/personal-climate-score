from openmeteo_sdk.Unit import Unit
from openmeteo_sdk.Variable import Variable
import pandas as pd
import numpy as np

import datetime as dt
from datetime import date
from dateutil.relativedelta import relativedelta
import requests
import openmeteo_requests
# import requests_cache
# from retry_requests import retry
import os
import hashlib
import json


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
		# The issue is that DatetimeIndex does not have .date() or .time() methods.
		# Instead, use .date and .time attributes of the underlying numpy array.
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
	if (np.max(temperature_arr) > f_to_c(score_obj.humid_day_max) and np.min(dew_point_arr) > f_to_c(70)):
		score = score_obj.humid_day_coef
		reason = "humid"
	elif (np.max(temperature_arr) > f_to_c(score_obj.dry_heat_day_min) and np.min(dew_point_arr) < f_to_c(55)):
		score = score_obj.dry_heat_day_coef
		reason = "dry heat"
	elif (np.max(temperature_arr) < f_to_c(score_obj.too_cold_windy__max) and np.mean(wind_arr) > 30):
		score = score_obj.too_cold_windy__coef
		reason = "too cold windy"
	elif (np.max(temperature_arr) < f_to_c(score_obj.too_cold_still__max) and np.mean(wind_arr) < 30):
		score = score_obj.too_cold_still__coef
		reason = "too cold still"
	elif (np.max(temperature_arr) > f_to_c(score_obj.ideal_temp__min) and np.max(temperature_arr) < f_to_c(score_obj.ideal_temp__max)):
		if (np.mean(cloud_cover_arr) < 60 and np.sum(rain_arr) < 2):
			score = score_obj.ideal_sunny_day__coef
			reason = "ideal sunny"
		elif (np.mean(cloud_cover_arr) >=60 and np.sum(rain_arr) < 2):
			score = score_obj.overcast_dry__coef
			reason = "ideal overcast"
	# Precipitation overrides
	if (np.sum(rain_arr) >=2 and np.sum(rain_arr) < 10):
		prev_score = score
		score = np.min([score, score_obj.light_rain__coef])
		if score == score_obj.light_rain__coef or score < prev_score:
			reason = "light rain"
	elif (np.sum(rain_arr) >=10):
		prev_score = score
		score = np.min([score, score_obj.heavy_rain__coef])
		if score == score_obj.heavy_rain__coef or score < prev_score:
			reason = "heavy rain"
	elif (np.sum(snowfall_arr) > 1):
		prev_score = score
		score = np.min ([score, score_obj.snow_coef])
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
	if (temperature_max > f_to_c(score_obj.humid_day_max) and dew_point_min > f_to_c(70)):
		score = score_obj.humid_day_coef
		reason = "humid"
	elif (temperature_max > f_to_c(score_obj.dry_heat_day_min) and dew_point_min < f_to_c(55)):
		score = score_obj.dry_heat_day_coef
		reason = "dry heat"
	elif (temperature_max < f_to_c(score_obj.too_cold_windy__max) and wind_mean > 30):
		score = score_obj.too_cold_windy__coef
		reason = "too cold windy"
	elif (temperature_max < f_to_c(score_obj.too_cold_still__max) and wind_mean < 30):
		score = score_obj.too_cold_still__coef
		reason = "too cold still"
	elif (temperature_max > f_to_c(score_obj.ideal_temp__min) and temperature_max < f_to_c(score_obj.ideal_temp__max)):
		if (cloud_cover_mean < 60 and scaling_factor*rain_sum < 2):
			score = score_obj.ideal_sunny_day__coef
			reason = "ideal sunny"
		elif (cloud_cover_mean >=60 and scaling_factor*rain_sum < 2):
			score = score_obj.overcast_dry__coef
			reason = "ideal overcast"
	# Precipitation overrides
	if (scaling_factor*rain_sum >=2 and scaling_factor*rain_sum < 10):
		prev_score = score
		score = np.min([score, score_obj.light_rain__coef])
		if score == score_obj.light_rain__coef or score < prev_score:
			reason = "light rain"
	elif (scaling_factor*rain_sum >=10):
		prev_score = score
		score = np.min([score, score_obj.heavy_rain__coef])
		if score == score_obj.heavy_rain__coef or score < prev_score:
			reason = "heavy rain"
	elif (snowfall_sum > 1):
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


def get_historical_and_aqi_data(lat, long, city_timezone, city, state, col_names=None, save_csv=True):
    if col_names is None:
        col_names = ["temperature_2m", "dew_point_2m", "rain", "snowfall", "cloud_cover", "wind_speed_10m"]
    
    # Check cache first
    cache_filename = get_cache_filename("historical", city, state)
    cached_df = load_cached_data(cache_filename)
    if cached_df is not None:
        print(f"Loading historical data from cache: {cache_filename}")
        return cached_df, cache_filename
    
    print(f"Fetching historical data for {city}, {state} from API...")
    openmeteo = openmeteo_requests.Client()

    # Historical weather
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": long,
        "start_date": date.today() - relativedelta(years=10),
        "end_date": date.today(),
        "hourly": col_names,
        "timezone": 'GMT'
    }
    responses = openmeteo.weather_api(url, params=params)
    df_historical_weather = extract_data_from_api_response(responses[0].Hourly(), col_names)
    # AQI
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
    df_historical = pd.merge(df_historical_aqi, df_historical_weather, on=['datetime', 'date', 'time'], how='outer')
    df_historical.sort_values(by='datetime', ascending=True, inplace=True)
    
    # Save to cache
    if save_csv:
        save_cached_data(df_historical, cache_filename)
    else:
        cache_filename = None
    

    return df_historical, cache_filename


def get_forecasted_data(lat, long, city_timezone, city, state, model, col_names=None, save_csv=True):
    if col_names is None:
        col_names = ["temperature_2m_max", "wind_speed_10m_mean", "dew_point_2m_min", "rain_sum", "cloud_cover_mean", "snowfall_sum"]
    
    # Check cache first
    cache_filename = get_cache_filename("forecasted", city, state, model)
    cached_df = load_cached_data(cache_filename)
    if cached_df is not None:
        print(f"Loading forecasted data from cache: {cache_filename}")
        return cached_df, cache_filename
    
    print(f"Fetching forecasted data for {city}, {state} with model {model} from API...")
    openmeteo = openmeteo_requests.Client()
    url = "https://climate-api.open-meteo.com/v1/climate"
    params = {
        "latitude": lat,
        "longitude": long,
        "start_date": date.today(),
        "end_date": date.today() + relativedelta(years=25),
        "models": model,
        "daily": col_names
    }
    responses = openmeteo.weather_api(url, params=params)
    df_single_model = extract_data_from_api_response(responses[0].Daily(), col_names, hourly=False, timezone=city_timezone)
    df_single_model.columns = [
        col if col == 'date' else col + f'__{model}'
        for col in df_single_model.columns
    ]
    
    # Save to cache
    if save_csv:
        save_cached_data(df_single_model, cache_filename)
    else:   
        cache_filename = None
    return df_single_model, cache_filename


def process_historical_for_plotting(df, climate_score, city=None, state=None):
    # Check cache first if city and state are provided
    if city and state:
        score_params = climate_score.get_all_parameters()
        cache_filename = get_cache_filename("historical_score", city, state, score_params=score_params)
        cached_df = load_cached_data(cache_filename)
        if cached_df is not None:
            print(f"Loading historical score data from cache: {cache_filename}")
            # Extract reasons from the cached data (assuming they're stored in a separate column or we can reconstruct them)
            reasons = cached_df["reason"].tolist() if "reason" in cached_df.columns else []
            return cached_df, reasons
    
    print("Processing historical data for plotting...")
    df["date"] = df["date"].astype(str)
    df["time"] = df["time"].astype(str)
    unique_dates = df["date"].unique()
    scores = []
    reasons = []
    for date_val in sorted(unique_dates):
        df_subset = df[
            (df["date"] == date_val) &
            (df["time"] >= climate_score.min_time) &
            (df["time"] <= climate_score.max_time)
        ]
        if not df_subset.empty:
            score, reason = daily_climate_score__hourly(
                df_subset["temperature_2m__celsius"],
                df_subset["dew_point_2m__celsius"],
                df_subset["rain__millimetre"],
                df_subset["snowfall__centimetre"],
                df_subset["wind_speed_10m__kilometres_per_hour"],
                df_subset["cloud_cover__percentage"],
                climate_score
            )
            scores.append((date_val, score, reason))
            reasons.append(reason)
    score_df = pd.DataFrame(scores, columns=["date", "score", "reason"])
    score_df["date"] = pd.to_datetime(score_df["date"])
    score_df["score_30d_ma"] = score_df["score"].rolling(window=30).mean()
    score_df["year"] = score_df["date"].dt.year
    
    # Save to cache if city and state are provided
    if city and state:
        score_params = climate_score.get_all_parameters()
        cache_filename = get_cache_filename("historical_score", city, state, score_params=score_params)
        save_cached_data(score_df, cache_filename)
    
    return score_df, reasons


def process_forecasted_for_plotting(df, climate_score, model="NICAM16_8S", city=None, state=None):
    # Check cache first if city and state are provided
    if city and state: 
        score_params = climate_score.get_all_parameters()
        cache_filename = get_cache_filename("forecasted_score", city, state, model, score_params)
        cached_df = load_cached_data(cache_filename)
        if cached_df is not None:
            print(f"Loading forecasted score data from cache: {cache_filename}")
            # Extract reasons from the cached data
            reasons = cached_df["reason"].tolist() if "reason" in cached_df.columns else []
            return cached_df, reasons
    
    print(f"Processing forecasted data for plotting with model {model}...")
    df["date"] = df["date"].astype(str)
    scores_forecasted = []
    reasons_forecasted = []
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
        reasons_forecasted.append(reason)
    score_df_forecasted = pd.DataFrame(scores_forecasted, columns=["date", "score", "reason"])
    score_df_forecasted["date"] = pd.to_datetime(score_df_forecasted["date"])
    score_df_forecasted["score_30d_ma"] = score_df_forecasted["score"].rolling(window=30).mean()
    score_df_forecasted["year"] = score_df_forecasted["date"].dt.year
    
    # Save to cache if city and state are provided
    if city and state:
        score_params = climate_score.get_all_parameters()
        cache_filename = get_cache_filename("forecasted_score", city, state, model, score_params)
        save_cached_data(score_df_forecasted, cache_filename)
    
    return score_df_forecasted, reasons_forecasted


def get_cache_filename(data_type, city, state, model=None, score_params=None):
    """
    Generate cache filename based on data type and parameters.
    
    Args:
        data_type: 'historical', 'forecasted', 'historical_score', 'forecasted_score'
        city: city name
        state: state name
        model: model name (for forecasted data)
        score_params: score parameters dict (for score data)
    
    Returns:
        cache filename string
    """
    # Create cache directory if it doesn't exist
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    if data_type == "historical":
        return os.path.join(cache_dir, f"{city}_{state}_historical_data.csv")
    elif data_type == "forecasted":
        return os.path.join(cache_dir, f"{city}_{state}_{model}_forecasted_data.csv")
    elif data_type == "historical_score":
        # Create hash of score parameters for filename
        score_hash = hashlib.md5(json.dumps(score_params, sort_keys=True).encode()).hexdigest()[:8]
        return os.path.join(cache_dir, f"{city}_{state}_historical_score_{score_hash}.csv")
    elif data_type == "forecasted_score":
        # Create hash of score parameters for filename
        score_hash = hashlib.md5(json.dumps(score_params, sort_keys=True).encode()).hexdigest()[:8]
        return os.path.join(cache_dir, f"{city}_{state}_{model}_forecasted_score_{score_hash}.csv")
    else:
        raise ValueError(f"Unknown data_type: {data_type}")


def load_cached_data(filename):
    """
    Load data from cache file if it exists.
    
    Args:
        filename: cache filename
    
    Returns:
        DataFrame if file exists, None otherwise
    """
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            # Convert date columns back to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error loading cached data from {filename}: {e}")
            return None
    return None


def save_cached_data(df, filename):
    """
    Save data to cache file.
    
    Args:
        df: DataFrame to save
        filename: cache filename
    """
    try:
        df.to_csv(filename, index=False)
        print(f"Data cached to {filename}")
    except Exception as e:
        print(f"Error saving cached data to {filename}: {e}")

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