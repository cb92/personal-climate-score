import openmeteo_requests
from openmeteo_sdk.Unit import Unit
from openmeteo_sdk.Model import Model
from openmeteo_sdk.Variable import Variable
import pandas as pd
import numpy as np
import requests_cache
import requests
from retry_requests import retry
import datetime as dt
from datetime import date
from dateutil.relativedelta import relativedelta
import pytz
import matplotlib.pyplot as plt



####### Get lat/long for input city + state
## TODO: move this into main()
city = 'Phoenix'
state = 'Arizona' #TODO: populate this with a dictionary + dropdown
url = f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=100'
response = requests.get(url)
data = response.json()
filtered_data = [item for item in data['results'] if item['country_code'] == 'US' and item['admin1'] == state]
latitude = filtered_data[0]['latitude']
longitude = filtered_data[0]['longitude']
timezone = filtered_data[0]['timezone']
print(timezone)
population = filtered_data[0]['population']

####### Get historical weather data for lat/long
# Define helper functions to match items in class dicts and to extract information from the API response
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

def extract_data_from_api_response(timeseries, cols, contains_model = False, hourly = True, timezone = 'America/Los_Angeles'):
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



#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

#Get historical data
url = "https://archive-api.open-meteo.com/v1/archive"
col_names = ["temperature_2m", 
	#"relative_humidity_2m", 
	"dew_point_2m", 
	#"apparent_temperature", 
	"rain", 
	"snowfall", 
	#"snow_depth", 
	"cloud_cover", 
	"wind_speed_10m"]
params = {
	"latitude": latitude,
	"longitude": longitude,
	"start_date": date.today() - relativedelta(years=10),
	"end_date": date.today(),
	"hourly": col_names,
	"timezone": 'GMT'
}
responses = openmeteo.weather_api(url, params=params)
df_historical_weather = extract_data_from_api_response(responses[0].Hourly(), col_names)

# Get AQI data
url = "https://air-quality-api.open-meteo.com/v1/air-quality"
col_names = ["pm2_5"]
params = {
	"latitude": latitude,
	"longitude": longitude,
	"hourly": col_names,
	"start_date": "2022-01-01",
	"end_date": date.today(),
	"timezone": 'GMT'

}
responses = openmeteo.weather_api(url, params=params)
df_historical_aqi = extract_data_from_api_response(responses[0].Hourly(), col_names)
df_historical = pd.merge(df_historical_aqi, df_historical_weather, on=['datetime', 'date', 'time'], how='outer')
df_historical.sort_values(by='datetime', ascending=True, inplace=True)
df_historical.to_csv('historical_data.csv', index = False)

#Get daily Prediction data for future years
url = "https://climate-api.open-meteo.com/v1/climate"
#all_models = ["CMCC_CM2_VHR4", "FGOALS_f3_H", "HiRAM_SIT_HR", "MRI_AGCM3_2_S", "EC_Earth3P_HR", "MPI_ESM1_2_XR", "NICAM16_8S"]
all_models = ['NICAM16_8S']
col_names = ["temperature_2m_max", 
		#"temperature_2m_mean", 
		#"temperature_2m_min",
		"wind_speed_10m_mean", 
		#"relative_humidity_2m_mean", 
		#"relative_humidity_2m_max", 
		#"relative_humidity_2m_min", 
		#"dew_point_2m_mean", 
		"dew_point_2m_min", 
		#"dew_point_2m_max", 
		"rain_sum", 
		"cloud_cover_mean",
		"snowfall_sum"]

i = 0
for model in all_models:
	params = {
	 	"latitude": latitude,
	 	"longitude": longitude,
		"start_date": date.today(),
		"end_date": date.today() + relativedelta(years=25),
		"models": model,
		"daily": col_names
	}
	responses = openmeteo.weather_api(url, params=params)
	df_single_model = extract_data_from_api_response(responses[0].Daily(), col_names, hourly = False)
	df_single_model.columns = [
	    col if col == 'date' else col + '__' + model
	    for col in df_single_model.columns
	]
	if i == 0:
		df_all_models = df_single_model
	else:
		df_all_models = pd.merge(df_single_model, df_all_models, on='date', how='outer')

	i+=1

df_all_models.to_csv('prediction_data.csv', index = False)

####### Calculate parameters for personal climate match score
# dewpoint > 70 ==> "humid"
min_time = "08:00:00"
max_time = "20:00:00"
t1 = dt.datetime.strptime(min_time, "%H:%M:%S")
t2 = dt.datetime.strptime(max_time, "%H:%M:%S")
hours_diff = (t2 - t1).seconds / 3600
scaling_factor = hours_diff / 24



# let's say it's a sunny or partly cloudy day out. What temperature range do you really love?
ideal_temp__min = 60
ideal_temp__max = 90
ideal_sunny_day__coef = 2

# how do you feel about overcast but dry days in your preferred temperature range?
overcast_dry__coef = 1 # 0 = neutral

# if there isn't wind, how cold is too cold? And how do you feel about this?
too_cold_still__max = 30
too_cold_still__coef = -1

# if there IS wind, how cold is too cold? And how do you feel about this?
too_cold_windy__max = 35
too_cold_windy__coef = -2

# if it's a noticeably humid day, at what temperature do you start to feel uncomfortable?
humid_day_max = 80
# how much does this affect you?
humid_day_coef = -2

# how do you feel about days with light rain?
light_rain__coef = 1 # 0 = neutral

# how do you feel about days with heavy rain?
heavy_rain__coef = -1 # 0 = neutral

# how do you feel about days with snow
snow_coef = 0

# How hot is too hot in a dry heat
dry_heat_day_min = 95
dry_heat_day_coef = -1


# sum everything up and then truncate to [-2, 2]

def f_to_c(fahrenheit):
	return (fahrenheit - 32)*5/9


def daily_climate_score__hourly(temperature_arr, 
								dew_point_arr, 
								rain_arr, 
								snowfall_arr, 
								wind_arr, 
								cloud_cover_arr):
	score = 0
	# min dewpoint generally coincides with max temp
	if (np.max(temperature_arr) > f_to_c(humid_day_max) and np.min(dew_point_arr) > f_to_c(70)):
		score = humid_day_coef
		#print("humid\n")
	elif (np.max(temperature_arr) > f_to_c(dry_heat_day_min) and np.min(dew_point_arr) < f_to_c(55)):
		score = dry_heat_day_coef
		#print("dry heat\n")
	# >30 km/h is considered "fresh breeze" on the Beaufort scale
	elif (np.max(temperature_arr) < f_to_c(too_cold_windy__max) and np.mean(wind_arr) > 30):
		score = too_cold_windy__coef
		#print("too cold windy\n")
	elif (np.max(temperature_arr) < f_to_c(too_cold_still__max) and np.mean(wind_arr) < 30):
		score = too_cold_still__coef
		#print("too cold still\n")
	elif (np.max(temperature_arr) > f_to_c(ideal_temp__min) and np.max(temperature_arr) < f_to_c(ideal_temp__max)): 
		# NWS refers to 30-60% as "partly cloudy", rainfall < 2mm (very light rain can occur for roughly one hour without affecting score)
		if (np.mean(cloud_cover_arr) < 60 and np.sum(rain_arr) < 2):
			score = ideal_sunny_day__coef
			#print("ideal sunny\n")
		elif (np.mean(cloud_cover_arr) >=60 and np.sum(rain_arr) < 2):
			score = overcast_dry__coef
			#print("ideal overcast\n")

	# for precipitation values, take the min of the previously calculated score and the precipitation based score
	# light rain day is a day with light rain (2.5mm/hr) for <=3h
	#if (np.mean(rain_arr[rain_arr > 0]) <= 2.5 and np.sum(rain_arr) >=2 ): 
	if (np.sum(rain_arr) >=2 and np.sum(rain_arr) < 10):
		score = np.min([score, light_rain__coef])
		#print("light rain\n")
	#elif (np.mean(rain_arr[rain_arr > 0]) > 2.5):
	elif (np.sum(rain_arr) >=10):
		score = np.min([score, heavy_rain__coef])
		#print('heavy rain\n')
	elif (np.sum(snowfall_arr) > 1): # more than 1cm of snow
		score = np.min ([score, snow_coef])
		#print('snow\n')
	return score

def daily_climate_score__daily(temperature_max, 
								dew_point_min,
								wind_mean,
								cloud_cover_mean,
								rain_sum, 
								snowfall_sum, 
								scaling_factor):
	score = 0
	# min dewpoint generally coincides with max temp
	if (temperature_max > f_to_c(humid_day_max) and dew_point_min > f_to_c(70)):
		score = humid_day_coef
		#print("humid\n")
	elif (temperature_max > f_to_c(dry_heat_day_min) and dew_point_min < f_to_c(55)):
		score = dry_heat_day_coef
		#print("dry heat\n")
	# >30 km/h is considered "fresh breeze" on the Beaufort scale
	elif (temperature_max < f_to_c(too_cold_windy__max) and wind_mean > 30):
		score = too_cold_windy__coef
		#print("too cold windy\n")
	elif (temperature_max < f_to_c(too_cold_still__max) and wind_mean < 30):
		score = too_cold_still__coef
		#print("too cold still\n")
	elif (temperature_max > f_to_c(ideal_temp__min) and temperature_max < f_to_c(ideal_temp__max)): 
		# NWS refers to 30-60% as "partly cloudy", rainfall < 2mm (very light rain can occur for roughly one hour without affecting score)
		if (cloud_cover_mean < 60 and scaling_factor*rain_sum < 2):
			score = ideal_sunny_day__coef
			#print("ideal sunny\n")
		elif (cloud_cover_mean >=60 and scaling_factor*rain_sum < 2):
			score = overcast_dry__coef
			#print("ideal overcast\n")

	# for precipitation values, take the min of the previously calculated score and the precipitation based score
	if (scaling_factor*rain_sum >=2 and scaling_factor*rain_sum < 10):
		score = np.min([score, light_rain__coef])
		#print("light rain\n")
	elif (scaling_factor*rain_sum >=10):
		score = np.min([score, heavy_rain__coef])
		#print('heavy rain\n')
	elif (snowfall_sum > 1): # more than 1cm of snow
		score = np.min([score, snow_coef])
		#print('snow\n')


	return score



df = pd.read_csv("historical_data.csv")
# Ensure 'date' and 'time' columns are strings
df["date"] = df["date"].astype(str)
df["time"] = df["time"].astype(str)
unique_dates = df["date"].unique()
scores = []

for date in sorted(unique_dates):
    df_subset = df[
        (df["date"] == date) &
        (df["time"] >= min_time) &
        (df["time"] <= max_time)
    ]
    
    if not df_subset.empty:
        score = daily_climate_score__hourly(
            df_subset["temperature_2m__celsius"],
            df_subset["dew_point_2m__celsius"],
            df_subset["rain__millimetre"],
            df_subset["snowfall__centimetre"],
            df_subset["wind_speed_10m__kilometres_per_hour"],
            df_subset["cloud_cover__percentage"]
        )
        scores.append((date, score))

# Convert to DataFrame for plotting
score_df = pd.DataFrame(scores, columns=["date", "score"])
score_df["date"] = pd.to_datetime(score_df["date"])
score_df["score_30d_ma"] = score_df["score"].rolling(window=30).mean()





df_forecasted = pd.read_csv("prediction_data.csv")
df_forecasted["date"] = df_forecasted["date"].astype(str)
scores_forecasted = []

for index, row in df_forecasted.iterrows():
	date = row['date']    
	score = daily_climate_score__daily(row['temperature_2m_max__celsius__NICAM16_8S'],
		row['dew_point_2m_min__celsius__NICAM16_8S'],
		row['wind_speed_10m_mean__kilometres_per_hour__NICAM16_8S'],
		row['cloud_cover_mean__percentage__NICAM16_8S'],
		row['rain_sum__millimetre__NICAM16_8S'], 
		row['snowfall_sum__centimetre__NICAM16_8S'], 
		scaling_factor)
	scores_forecasted.append((date, score))

# Convert to DataFrame for plotting
score_df_forecasted = pd.DataFrame(scores_forecasted, columns=["date", "score"])
score_df_forecasted["date"] = pd.to_datetime(score_df_forecasted["date"])
score_df_forecasted["score_30d_ma"] = score_df_forecasted["score"].rolling(window=30).mean()




min_forecasted_date = score_df_forecasted["date"].min()

# Plot
plt.figure(figsize=(12, 6))

# Historical scores
plt.plot(score_df["date"], score_df["score"], marker='o', label='Observed Score')
plt.plot(score_df["date"], score_df["score_30d_ma"], color='red', linewidth=2, label='Observed 30-Day MA')

# Forecasted scores
plt.plot(score_df_forecasted["date"], score_df_forecasted["score"], marker='x', color='green', label='Forecasted Score')
plt.plot(score_df_forecasted["date"], score_df_forecasted["score_30d_ma"], color='orange', linewidth=2, label='Forecasted 30-Day MA')

# Vertical line at start of forecast
plt.axvline(x=min_forecasted_date, color='gray', linestyle=':', linewidth=2, label='Forecast Start')

# Labels and layout
plt.title("Daily Climate Score Over Time")
plt.xlabel("Date")
plt.ylabel("Climate Score")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
