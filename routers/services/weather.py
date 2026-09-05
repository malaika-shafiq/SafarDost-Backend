import os
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.weather import WeatherCache
from schemas.weather_schemas import WeatherResponse, WeatherPurgeResponse
from utils.auth_utils import get_current_user  # existing security dependency

router = APIRouter(prefix="", tags=["Weather Services"])


@router.get("/weather", response_model=WeatherResponse)
def get_weather(city: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    # 1. Search local SQLite database using case-insensitive partial match pattern
    local_record = db.query(WeatherCache).filter(WeatherCache.city_name.ilike(f"%{city}%")).first()

    # 2. Modern Time Check (Only skipped if the user passes force_refresh=True)
    if local_record and not force_refresh:
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        record_time = local_record.last_updated
        time_passed = current_time - record_time

        # If data is fresher than 30 minutes, return it instantly
        if time_passed < datetime.timedelta(minutes=30):
            return WeatherResponse(
                city_name=local_record.city_name,
                temperature_c=local_record.temperature_c,
                condition_text=local_record.condition_text,
                humidity=local_record.humidity
            )

    # 3. Use built-in urllib engine with correct OpenWeather configurations
    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Weather API key is missing from environment variables."
        )

    # Clean URL assembly to prevent string corruption
    BASE_URL = "https://openweathermap.org"
    query_params = {
        "q": f"{city},PK",  # Defaults to Pakistan for Safar Dost
        "appid": API_KEY,
        "units": "metric"  # For Celsius
    }
    encoded_params = urllib.parse.urlencode(query_params)
    SECURE_URL = f"{BASE_URL}?{encoded_params}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(SECURE_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=10.0) as response:
            raw_data = response.read().decode("utf-8")
            weather_data = json.loads(raw_data)

    except urllib.error.HTTPError as http_ex:
        if http_ex.code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unactivated API Key provided to the engine."
            )
        elif http_ex.code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not retrieve weather details for the specified location."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External backend service returned error status {http_ex.code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External weather service transport failed: {str(e)}"
        )

    # 4. Pull out individual pieces from official OpenWeather response structure
    try:
        extracted_city = weather_data["name"]
        extracted_temp = float(weather_data["main"]["temp"])

        # FIXED: Added [0] index accessor because OpenWeather returns "weather" as a list block
        extracted_condition = weather_data["weather"][0]["description"]

        extracted_humidity = int(weather_data["main"]["humidity"])
    except (KeyError, IndexError, TypeError) as parse_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to process upstream format schema parameters: {str(parse_err)}"
        )

    # 5. Save fresh data using up-to-date time strategy
    current_utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    if local_record:
        local_record.temperature_c = extracted_temp
        local_record.condition_text = extracted_condition
        local_record.humidity = extracted_humidity
        local_record.last_updated = current_utc_now
        db.commit()
        active_record = local_record
    else:
        new_cache_entry = WeatherCache(
            city_name=extracted_city,
            temperature_c=extracted_temp,
            condition_text=extracted_condition,
            humidity=extracted_humidity,
            last_updated=current_utc_now
        )
        db.add(new_cache_entry)
        db.commit()
        active_record = new_cache_entry

    return WeatherResponse(
        city_name=active_record.city_name,
        temperature_c=active_record.temperature_c,
        condition_text=active_record.condition_text,
        humidity=active_record.humidity
    )


@router.post("/admin/weather/purge", response_model=WeatherPurgeResponse)
def purge_weather_cache(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Force-clears all cached data rows from the weather_caches table.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to perform this cache clearance."
        )

    query = db.query(WeatherCache)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return WeatherPurgeResponse(
        success=True,
        records_deleted=deleted_count
    )
