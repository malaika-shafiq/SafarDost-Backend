import requests

API_KEY = "6c0f18f295ac42ba9ba145645263107"
CITY = "Lahore"

# This long pattern is the exact path required by WeatherAPI's servers
SECURE_URL = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}"

print("Sending direct query to:", SECURE_URL)

api_response = requests.get(SECURE_URL)

print("Response Status Code:", api_response.status_code)
print("Raw Response Text Snippet:\n", api_response.text[:300])
