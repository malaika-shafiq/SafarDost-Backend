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
    # 1. Search local SQLite cache
    local_record = db.query(WeatherCache).filter(WeatherCache.city_name.ilike(f"%{city}%")).first()

    # 2. Cache Validation Layer (30 Mins)
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

    # 3. Environment Variable Retrieval
    RAW_KEY = os.getenv("WEATHER_API_KEY")
    if not RAW_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Railway/Render Environment Configuration Error: WEATHER_API_KEY variable is empty or missing."
        )

    API_KEY = RAW_KEY.strip().replace('"', '').replace("'", "")

    # Clean URL parameters assembly
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    query_params = {
        "q": f"{city},PK",
        "appid": API_KEY,
        "units": "metric"
    }
    encoded_params = urllib.parse.urlencode(query_params)
    SECURE_URL = f"{BASE_URL}?{encoded_params}"

    try:
        # Standard lightweight agent header to bypass platform proxy drops
        headers = {"User-Agent": "SafarDostTravelApp/1.0 Prototype"}
        req = urllib.request.Request(SECURE_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=10.0) as response:
            raw_data = response.read().decode("utf-8")

            # Catch HTML redirects safely
            if raw_data.strip().startswith("<!DOCTYPE") or raw_data.strip().startswith("<html"):
                masked_key = f"{API_KEY[:4]}... (Length: {len(API_KEY)})" if len(API_KEY) > 4 else "Invalid/Too Short"
                raise ValueError(
                    f"OpenWeather firewall redirected this request to their homepage HTML. "
                    f"This usually means your API Key value is invalid or blocked. "
                    f"Your server is currently reading the key as: {masked_key}"
                )

            weather_data = json.loads(raw_data)

    except urllib.error.HTTPError as http_ex:
        error_msg = http_ex.read().decode("utf-8")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenWeather Gateway rejected credentials or parameters (Status {http_ex.code}): {error_msg}"
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Network bridge transport exception: {str(e)}"
        )

    # 4. Extract data keys using official OpenWeather schema array mapping
    try:
        extracted_city = weather_data["name"]
        extracted_temp = float(weather_data["main"]["temp"])

        # FIXED: Access the first element [0] of the weather list block array safely
        extracted_condition = weather_data["weather"][0]["description"]

        extracted_humidity = int(weather_data["main"]["humidity"])
    except (KeyError, IndexError, TypeError) as parse_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Schema mapping structure error on backend parameters: {str(parse_err)}"
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    query = db.query(WeatherCache)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return WeatherPurgeResponse(success=True, records_deleted=deleted_count)
