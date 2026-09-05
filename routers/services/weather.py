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
from utils.auth_utils import get_current_user

router = APIRouter(prefix="", tags=["Weather Services"])


@router.get("/weather", response_model=WeatherResponse)
def get_weather(city: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    # 1. Search local SQLite database
    local_record = db.query(WeatherCache).filter(WeatherCache.city_name.ilike(f"%{city}%")).first()

    # 2. Cache Check (30 Mins)
    if local_record and not force_refresh:
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        record_time = local_record.last_updated
        time_passed = current_time - record_time

        if time_passed < datetime.timedelta(minutes=30):
            return WeatherResponse(
                city_name=local_record.city_name,
                temperature_c=local_record.temperature_c,
                condition_text=local_record.condition_text,
                humidity=local_record.humidity
            )

    # 3. Fetch from External Provider
    API_KEY = os.getenv("WEATHER_API_KEY")
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Environment configuration error: WEATHER_API_KEY token is missing."
        )

    BASE_URL = "https://openweathermap.org"
    query_params = {
        "q": f"{city},PK",
        "appid": API_KEY.strip(),  # Added .strip() to remove accidental spaces
        "units": "metric"
    }
    encoded_params = urllib.parse.urlencode(query_params)
    SECURE_URL = f"{BASE_URL}?{encoded_params}"

    raw_data = ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(SECURE_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=12.0) as response:
            raw_data = response.read().decode("utf-8")

            # Diagnostic trap: Check if the server sneaked back an HTML page instead of JSON
            if raw_data.strip().startswith("<!DOCTYPE") or raw_data.strip().startswith("<html"):
                raise ValueError(
                    f"HTML webpage intercepted instead of JSON data data stream. Snippet: {raw_data[:160]}")

            weather_data = json.loads(raw_data)

    except urllib.error.HTTPError as http_ex:
        error_body = http_ex.read().decode("utf-8")[:100]
        if http_ex.code == 401:
            raise HTTPException(status_code=401, detail=f"Unauthorized API credentials. Details: {error_body}")
        elif http_ex.code == 404:
            raise HTTPException(status_code=404, detail="The requested tourism city was not found.")
        raise HTTPException(status_code=502, detail=f"Upstream server responded with status code {http_ex.code}")

    except ValueError as val_err:
        # This catches our custom HTML intercept trap and returns it safely to your screen
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network bridge exception failure: {str(e)}. Raw snapshot: {raw_data[:80]}"
        )

    # 4. Extract data keys safely
    try:
        extracted_city = weather_data["name"]
        extracted_temp = float(weather_data["main"]["temp"])
        extracted_condition = weather_data["weather"][0]["description"]  # Safe index mapping
        extracted_humidity = int(weather_data["main"]["humidity"])
    except (KeyError, IndexError, TypeError) as parse_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Schema mapping mismatch on backend keys: {str(parse_err)}"
        )

    # 5. Commit to database cache
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
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required."
        )

    query = db.query(WeatherCache)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return WeatherPurgeResponse(success=True, records_deleted=deleted_count)
