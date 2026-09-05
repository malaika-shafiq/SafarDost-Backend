import httpx

# 1. Paste your key inside these quotes
API_KEY = "a3ba306afd6e482289b174741263107"

# 2. Leave this exactly as it is (ensure api. is at the start!)
base_url = "https://openweathermap.org"

query_params = {
    "q": "lahore,PK",
    "appid": API_KEY,
    "units": "metric"
}

try:
    response = httpx.get(base_url, params=query_params, timeout=10.0)

    print("\n================== DEBUG PATH ==================")
    print("THE EXACT URL PYTHON CALLED IS:")
    print(response.url)
    print("================================================\n")

    print("STATUS CODE:", response.status_code)
    # Only printing the first 150 characters to prevent terminal clutter
    print("RESPONSE PREVIEW:", response.text[:150])
except Exception as e:
    print("System Error:", e)
