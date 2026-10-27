import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from helper import *
import pandas as pd
import altair as alt

load_dotenv()
st.set_page_config(page_title="Personalized Climate Score", layout="wide")

US_STATES = [
    'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
    'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
    'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
    'West Virginia', 'Wisconsin', 'Wyoming'
]
MODELS = ["EC_Earth3P_HR", "MRI_AGCM3_2_S", "NICAM16_8S"]
LABELS = {-2: 'Hate', -1: 'Dislike', 0: 'Neutral', 1: 'Like', 2: 'Love'}
RISK = {'ok': 'No preference', 'some': 'Some', 'dealbreaker': 'Dealbreaker'}
DISASTERS = {'Flooding': 'flooding', 'Wildfire (in location)': 'wildfire (direct impacts only)',
             'Smoke (from wildfires)': 'smoke', 'Earthquakes': 'earthquakes',
             'Hurricanes': 'hurricanes', 'Tornados': 'tornados'}
SCORES = {0: 'Hate', 25: 'Dislike', 50: 'Neutral', 75: 'Like', 100: 'Love'}
SCORE_COLORS = ['#ba1535', '#ba6715', '#b7ba15', '#43ba15', '#158cba']
# historical solid, forecast at 70% opacity (as in the original), interleaved per score
DIST_COLORS = [c + a for c in SCORE_COLORS for a in ('', 'b3')]
REASON_COLORS = {
    "neutral": "#158cba", "too hot, humid": "#3f15ba", "too hot, dry": "#7a15ba", "too cold, windy": "#ba15a1",
    "too cold, still": "#ba1535", "ideal sunny": "#ba6715", "ideal overcast": "#b7ba15", "light rain": "#43ba15",
    "heavy rain": "#15ba67", "snow": "#15b7ba",
}
PM25 = {'Healthy': 0, 'Moderate': 12, 'Unhealthy for Sensitive': 35.5, 'Unhealthy': 55.5, 'Hazardous': 150.5}
PM25_COLORS = ['#2ca02c', '#e6d800', '#ff9900', '#d62728', '#800080']
PM_COL = 'pm2_5__micrograms_per_cubic_metre'
ds = Score()

# reusable function for a slider with five input options
def pref(container, label, default):
    return container.select_slider(label, [-2, -1, 0, 1, 2], int(default), format_func=LABELS.get)


def gemini(prompt):
    try:
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        return client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
    except Exception as e:
        return f"Could not get response from Gemini: {e}"


def analyze(lat, lon, tz, city, state, score):
    hist_daily, pm, _, _ = get_historical_and_aqi_data(lat, lon, tz, city, state)
    fc, _ = get_combined_forecasted_data(lat, lon, tz, city, state, models=MODELS)
    hist, _ = process_historical_for_plotting(hist_daily, score, city=city, state=state)
    fore, _ = process_combined_forecasted_for_plotting(fc, score, models=MODELS, city=city, state=state)
    for d in (hist, fore):
        d['date'] = pd.to_datetime(d['date'], errors='coerce')
        d['month'] = d['date'].dt.month
    sc = [c for c in fore.columns if c.startswith('score_')]
    rc = [c for c in fore.columns if c.startswith('reason_')]
    hy = hist['year'].max()
    fy_min = fore['year'].min() if len(fore) else hy

    # Score distribution (% of days per year; historical + forecast share the first forecast year)
    dpy = pd.concat([hist[['year', 'date']], fore[['year', 'date']]]).drop_duplicates().groupby('year')['date'].nunique()
    dist = {}
    for v, name in SCORES.items():
        h = (hist[hist['score'] == v].groupby('year').size() / dpy).fillna(0)
        f = pd.concat([(fore[fore[c] == v].groupby('year').size() / dpy).fillna(0) for c in sc], axis=1).mean(axis=1) if sc else pd.Series(0.0, index=dpy.index)
        # kept as separate stacked series so the overlap year shows its historical and forecast share
        dist[name], dist[f"{name} (forecast)"] = 100 * h, 100 * f

    # Score average with forecast range across models
    ah = hist.groupby('year')['score'].mean()
    per_model = fore.groupby('year')[sc].mean()
    af, lo, hi = per_model.mean(axis=1), per_model.min(axis=1), per_model.max(axis=1)
    if hy == fy_min and len(fore):
        nh = hist.loc[hist['year'] == hy, 'date'].nunique()
        nf = fore.loc[fore['year'] == hy, 'date'].nunique()
        wh, wf = nh / (nh + nf), nf / (nh + nf)
        h = ah[hy]
        af[hy], lo[hy], hi[hy] = h * wh + af[hy] * wf, h * wh + lo[hy] * wf, h * wh + hi[hy] * wf
        ah[hy] = af[hy]
    avg = pd.DataFrame({'Historical': ah, 'Forecasted': af, 'Lower Bound': lo, 'Upper Bound': hi})

    # Monthly average by year
    mh = hist.groupby(['year', 'month'])['score'].mean().unstack(0)
    mf = fore.groupby(['year', 'month'])[sc].mean().mean(axis=1).unstack(0).add_suffix(' (forecast)')
    nh_, nf_ = len(mh.columns), len(mf.columns)
    mcolors = ([f"#158cba{int(255 * (0.2 + 0.8 * (i + 1) / nh_)):02x}" for i in range(nh_)]
               + [f"#ba1535{int(255 * (0.2 + 0.8 * (nf_ - i) / nf_)):02x}" for i in range(nf_)])
    monthly = pd.concat([mh, mf], axis=1)

    # Days per reason per year
    cols = list(REASON_COLORS)
    rh = hist.groupby('year')['reason'].value_counts().unstack(fill_value=0).reindex(columns=cols, fill_value=0)
    g = pd.concat([fore.groupby('year')[c].value_counts().unstack(fill_value=0).reindex(columns=cols, fill_value=0)
                   for c in rc]).groupby(level=0)
    reasons = rh.add(g.mean(), fill_value=0)
    rng = pd.concat({'historical': rh, 'forecast (mean)': g.mean(), 'combined min': rh.add(g.min(), fill_value=0),
                     'combined max': rh.add(g.max(), fill_value=0)}, axis=1)

    # PM2.5 % of hours per year
    pm = pm.dropna(subset=[PM_COL]).assign(year=lambda d: pd.to_datetime(d['date']).dt.year)
    cat = pd.cut(pm[PM_COL], list(PM25.values()) + [float('inf')], right=False, labels=list(PM25))
    pm25 = (pd.crosstab(pm['year'], cat).reindex(columns=list(PM25), fill_value=0)
            .div(pm.groupby('year').size(), axis=0) * 100)

    return dict(dist=pd.DataFrame(dist).fillna(0), avg=avg, monthly=monthly, mcolors=mcolors,
                reasons=reasons, range=rng, pm25=pm25, fy=fy_min)

def css(c):  # '#rrggbbaa' -> rgba() so Vega always parses the alpha
    return f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},{int(c[7:9], 16) / 255:.2f})" if len(c) == 9 else c


def band_df(lo, hi):
    """Wide lo/hi frames (index=x, columns=series) -> long frame for range shading."""
    long = lambda d, n: d.rename_axis('x').reset_index().melt('x', var_name='series', value_name=n)
    b = long(lo, 'lo').merge(long(hi, 'hi'), on=['x', 'series']).dropna()
    b['series'] = b['series'].astype(str)
    return b


def chart(df, kind, colors, x_label, y_label, rule=None, bands=None):
    """Altair chart: axis titles, bottom legend that wraps, optional forecast-start rule and min/max range shading."""
    d = df.rename_axis('x').reset_index().melt('x', var_name='series', value_name='y').dropna(subset=['y'])
    d['series'] = d['series'].astype(str)
    names = [str(c) for c in df.columns]
    scale = alt.Scale(domain=names, range=[css(c) for c in colors])
    legend = alt.Legend(title=None, orient='bottom', columns=min(len(names), 4), labelLimit=300, symbolLimit=0, symbolOpacity=1)
    if kind == 'bar':
        x = alt.X('x:O', title=x_label, axis=alt.Axis(labelAngle=0))
        main = alt.Chart(d).mark_bar()
    else:
        x = alt.X('x:Q', title=x_label, axis=alt.Axis(format='d', tickMinStep=1))
        main = alt.Chart(d).mark_line()
    main = main.encode(x=x, y=alt.Y('y:Q', title=y_label), color=alt.Color('series:N', scale=scale, legend=legend),
                       tooltip=[alt.Tooltip('x:O', title=x_label), alt.Tooltip('series:N', title='Series'),
                                alt.Tooltip('y:Q', title=y_label, format='.2f')])
    layers = []
    if bands is not None and len(bands):
        layers.append(alt.Chart(bands).mark_area(opacity=0.2).encode(
            x=x, y='lo:Q', y2='hi:Q', color=alt.Color('series:N', scale=scale, legend=legend),
            tooltip=[alt.Tooltip('x:O', title=x_label), alt.Tooltip('series:N', title='Series'),
                     alt.Tooltip('lo:Q', title='Forecast min', format='.2f'),
                     alt.Tooltip('hi:Q', title='Forecast max', format='.2f')]))
    layers.append(main)
    if rule is not None:
        layers.append(alt.Chart(pd.DataFrame({'x': [rule], 'label': [f'Forecast begins {rule}']}))
                      .mark_rule(strokeDash=[6, 4], color='#888888', strokeWidth=2)
                      .encode(x=x, tooltip=['label:N']))
    st.altair_chart(alt.layer(*layers), use_container_width=True)


def avg_chart(r):
    a = r['avg']
    bands = band_df(a[['Lower Bound']].set_axis(['Forecasted'], axis=1), a[['Upper Bound']].set_axis(['Forecasted'], axis=1))
    chart(a[['Historical', 'Forecasted']], 'line', ['#158cba', '#ba1535'], 'Year', 'Score Average', r['fy'], bands)


def reasons_chart(r):
    rg = r['range']
    chart(r['reasons'], 'line', list(REASON_COLORS.values()), 'Year', 'Number of Days', r['fy'],
          band_df(rg['combined min'], rg['combined max']))
    with st.expander("Historical vs forecast split and forecast range"):
        st.dataframe(rg)


# ---------------- UI ----------------
st.title("Personalized Climate Score Dashboard")
st.write(
    "This dashboard helps you compare the climate and environmental conditions of up to three US cities based on your "
    "personal preferences. Enter the names and states of the US cities you want to compare, then adjust the sidebar controls to "
    "reflect your ideal weather, natural disaster risk tolerance, and other preferences. When ready, click 'Calculate "
    "Climate Scores' to generate personalized climate metrics and visualizations for each city.")
st.write(
    "The results show how well each city matches your preferences, both historically and in future climate projections. "
    "Higher scores indicate a better match. Use the graphs to explore seasonal patterns, recent air quality history, and "
    "the reasons behind each city's score. This tool is informational and uses the best available data, but all climate "
    "projections have uncertainty.")
st.markdown("For more detail on data sources, methodology, and troubleshooting, see the "
            "[README file on Github](https://github.com/cb92/personal-climate-score/blob/main/README.md).")

city_states = []
for i, (col, (c0, s0)) in enumerate(zip(st.columns(3), [('Phoenix', 'Arizona'), ('Portland', 'Oregon'),
                                                         ('Boston', 'Massachusetts')]), 1):
    with col:
        st.markdown(f"**City {i}**")
        city = st.text_input("City", c0, key=f"city{i}")
        state = st.selectbox("State", US_STATES, US_STATES.index(s0), key=f"state{i}")
        if st.checkbox("Include", True, key=f"inc{i}") and city:
            city_states.append((city.strip(), state))

with st.sidebar:
    st.header("Climate Preferences")

    st.subheader("Temperature Preferences")
    st.caption("Let's say it's a sunny or partly cloudy day out. What temperature range do you find ideal and how much do you enjoy it?")
    ideal = st.slider("Ideal Temperature Range (°F)", 0, 120, (int(ds.ideal_temp__min), int(ds.ideal_temp__max)), 5)
    sunny = pref(st, "Sunny Day Preference", ds.ideal_sunny_day__coef)

    st.subheader("Cold Weather Preferences")
    st.caption("How cold is too cold if there is no wind and how do you feel about too-cold days?")
    cold_still_t = st.slider("Too Cold (No Wind) - Temperature (°F)", -20, 60, int(ds.too_cold_still__max), 5)
    cold_still_c = pref(st, "Too Cold (No Wind) Preference", ds.too_cold_still__coef)
    st.caption("How cold is too cold on a windy day, and how do you feel about cold windy days?")
    cold_wind_t = st.slider("Too Cold (Windy) - Temperature (°F)", -20, 60, int(ds.too_cold_windy__max), 5)
    cold_wind_c = pref(st, "Too Cold (Windy) Preference", ds.too_cold_windy__coef)

    st.subheader("Humidity Preferences")
    st.caption("If it's a noticeably humid day, at what temperature do you start to feel uncomfortable?")
    humid_t = st.slider("Humid Day Max Temperature (°F)", 50, 100, int(ds.humid_day_max), 5)
    humid_c = pref(st, "Hot Humid Day Preference", ds.humid_day_coef)

    st.subheader("Precipitation Preferences")
    st.caption("How do you feel about light rain, heavy rain, and snow?")
    light_c = pref(st, "Light Rain Preference", ds.light_rain__coef)
    heavy_c = pref(st, "Heavy Rain Preference", ds.heavy_rain__coef)
    snow_c = pref(st, "Snow Preference", ds.snow_coef)

    st.subheader("Other Preferences")
    st.caption("How do you feel about overcast (cloudy) days?")
    overcast_c = pref(st, "Overcast Preference", ds.overcast_dry__coef)
    st.caption("What is the minimum temperature (°F) for a day to feel like 'dry heat' to you?")
    dry_t = st.slider("Dry Heat Minimum Temperature (°F)", 80, 120, int(ds.dry_heat_day_min), 5)
    st.caption("How do you feel about hot, dry days (above your minimum dry heat temperature)?")
    dry_c = pref(st, "Dry Heat Preference", ds.dry_heat_day_coef)
    st.caption("What hours of the day matter most to you for being outside? The climate score will focus on these hours.")
    window = st.slider("Time Window (24-hour format)", 0, 23, (8, 20), format="%02d:00")

    st.subheader("Natural Disaster Risk Tolerance")
    st.caption("For each risk, choose 'No preference' if you don't mind the risk at all, 'Some' if you can tolerate some but "
            "not a ton of this risk, or 'Dealbreaker' if having any of this risk is a dealbreaker for you.")
    disaster_prefs = {k: st.selectbox(l, list(RISK), format_func=RISK.get)
                    for (l, k) in DISASTERS.items()}

    st.subheader("Other Preferences for Places to Live")
    extra = st.text_input("What else matters to you about a place to live?",
                        placeholder="e.g. low cost of living, good state universities, urban, walkable, near ocean")
    st.caption("Choosing entirely new location/score combinations the tool has not seen before may take up to one minute.")
    run = st.button("Calculate Climate Scores", type="primary")


# ---------------- Compute ----------------
if run or 'res' not in st.session_state:
    score = Score()
    score.set_temperature_preferences(ideal[0], ideal[1], sunny)
    score.set_cold_weather_preferences(cold_still_t, cold_still_c, cold_wind_t, cold_wind_c)
    score.set_humidity_preferences(humid_t, humid_c)
    score.set_precipitation_preferences(light_c, heavy_c, snow_c)
    score.set_overcast_preference(overcast_c)
    score.set_dry_heat_preferences(dry_t, dry_c)
    score.set_time_window(f"{window[0]:02d}:00:00", f"{window[1]:02d}:00:00")

    with st.spinner("Calculating..."):
        suggestions = gemini(build_gemini_prompt(score, extra, disaster_prefs))
        loc = []
        if extra or any(v != 'ok' for v in disaster_prefs.values()):
            loc = [(f"{c}, {s}", gemini(build_gemini_location_prompt(c, s, extra, disaster_prefs)))
                   for c, s in city_states]
        cities, pts = [], []
        for city, state in city_states:
            label = f"{city}, {state}"
            try:
                lat, lon, tz, _ = get_city_info(city, state)
                pts.append({'lat': lat, 'lon': lon, 'city_state': label})
                cities.append((label, analyze(lat, lon, tz, city, state, score)))
            except Exception as e:
                cities.append((label, {'error': str(e)}))
    st.session_state.res = dict(cities=cities, pts=pts, loc=loc, suggestions=suggestions)

# ---------------- Results ----------------
res = st.session_state.res
if not res['cities']:
    st.warning("Select at least one city.")
    st.stop()

if res['loc']:
    for col, (label, text) in zip(st.columns(len(res['loc'])), res['loc']):
        col.subheader(label)
        col.markdown(text)

st.subheader("Selected Cities Map")
if res['pts']:
    pts_df = pd.DataFrame(res["pts"])

    # Create map feature layers (US states backdrop)
    states = alt.topo_feature(
        "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json", "states"
    )

    background = (
        alt.Chart(states)
        .mark_geoshape(fill="lightgray", stroke="white")
        .properties(width=700, height=400)
        .project("albersUsa")
    )

    # Plot point markers
    points = (
        alt.Chart(pts_df)
        .mark_circle(size=100, color="red")
        .encode(
            latitude="lat:Q",
            longitude="lon:Q",
            tooltip=[alt.Tooltip("city_state:N", title="City")],
        )
    )

    # Plot text labels offset slightly from points
    labels = (
        alt.Chart(pts_df)
        .mark_text(
            align="left",
            dx=8,  # Offset label horizontally from the point
            dy=-3,  # Offset label vertically
            fontSize=11,
            fontWeight="bold",
        )
        .encode(
            latitude="lat:Q",
            longitude="lon:Q",
            text="city_state:N",
        )
    )

    # Combine layers and render in Streamlit
    map_chart = alt.layer(background, points, labels).properties(
        title="Selected Cities"
    )

    st.altair_chart(map_chart, use_container_width=True)

CHARTS = [
    ("Score Distribution by Year (% of days)",
     lambda r: chart(r['dist'], 'bar', DIST_COLORS, 'Year', 'Percentage of Days', r['fy'])),
    ("Score Average by Year", avg_chart),
    ("Monthly Average Scores by Year", lambda r: chart(r['monthly'], 'line', r['mcolors'], 'Month', 'Average Score')),
    ("Number of Days by Type (Reason) per Year", reasons_chart),
    ("PM2.5 Air Quality Distribution by Year (% of hours)", lambda r: chart(r['pm25'], 'bar', PM25_COLORS, 'Year', 'Percentage of Hours')),
]
for title, draw in CHARTS:
    st.subheader(title)
    for col, (label, r) in zip(st.columns(len(res['cities'])), res['cities']):
        with col:
            if 'error' in r:
                st.error(f"{label}: {r['error']}")
            else:
                st.caption(f"{label}")
                draw(r)

st.markdown(res['suggestions'])
st.caption("Find a bug? Report it [here](https://github.com/cb92/personal-climate-score).")