# Setup instructions 
Before setup, do the following:
- Make sure you have Python 3.x installed
- If you want to use AI features, get a [Gemini API key](https://ai.google.dev/gemini-api/docs)

To set up this app on your personal machine, run the following command lines from your desired working directory, replacing your-api-key with the Gemini API key you generated above. 
```
git clone https://github.com/cb92/personal-climate-score
cd personal-climate-score
pip install requirements.txt
echo "GEMINI_API_KEY='your-api-key'" > .env
python3 app.py
```
Once the app is running, put the link into your browser window (something like `http://127.0.0.1:PORTNUMBER/`) to interact with the app

Note that running this app will cause files to be written to a folder called `cache/` in your working directory.

# Motivation
Differs from Weatherspark because ... 

# Data sources

# Score Methodology

## Thresholds (rain, humid, etc.)

# A Note on Models
- link to discussions of the differnet models used
- talk about uncertainty inherent in models
- different assumptions lead to different outcomes
- example: temperature in Miami (density chart for historical + three models)
