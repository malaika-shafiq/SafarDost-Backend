import httpx

# 1. Put your actual API key here inside the quotes
API_KEY = "a3ba306afd6e482289b174741263107"

# 2. The official, correct OpenWeather endpoint link
url = f"https://openweathermap.org{API_KEY}&units=metric"

try:
    print("--- TESTING LIVE CONNECTION POST-REBOOT ---")
    response = httpx.get(url, timeout=10.0)
    print("STATUS CODE:", response.status_code)
    print("\n--- SERVER DATA ---")
    print(response.text)
except Exception as e:
    print("Error:", e)
