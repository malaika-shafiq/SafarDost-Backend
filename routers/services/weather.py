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
    # 1. Standardize and clean the input city query parameters
    clean_city = city.replace("\n", "").replace("\r", "").strip()

    # 2. Search local SQLite cache using case-insensitive mapping
    local_record = db.query(WeatherCache).filter(WeatherCache.city_name.ilike(f"%{clean_city}%")).first()

    # 3. Cache Validation Check (30 Minute window)
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

    # 4. Environment Key Isolation and Deep Sanitation
    RAW_KEY = os.getenv("WEATHER_API_KEY")
    if not RAW_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration missing: WEATHER_API_KEY environment variable is not defined."
        )

    # Completely cleans hidden carriage returns (\r) and newlines (\n) injected by cloud copy-pastes
    API_KEY = RAW_KEY.replace("\n", "").replace("\r", "").strip().replace('"', '').replace("'", "")

    # Clean URL parameter mapping for WeatherAPI.com
    BASE_URL = "https://api.weatherapi.com/v1/current.json"
    query_params = {
        "key": API_KEY,
        "q": clean_city,
        "aqi": "no"
    }
    encoded_params = urllib.parse.urlencode(query_params)
    SECURE_URL = f"{BASE_URL}?{encoded_params}"

    raw_data = ""
    try:
        headers = {"User-Agent": "SafarDostTravelApp/1.0 Prototype"}
        req = urllib.request.Request(SECURE_URL, headers=headers)

        with urllib.request.urlopen(req, timeout=10.0) as response:
            raw_data = response.read().decode("utf-8")

            # Check for HTML structural leaks
            if raw_data.strip().startswith("<!DOCTYPE") or raw_data.strip().startswith("<html"):
                raise ValueError("WeatherAPI engine redirected to the homepage HTML instead of data.")

            weather_data = json.loads(raw_data)

    except urllib.error.HTTPError as http_ex:
        error_body = http_ex.read().decode("utf-8")
        try:
            parsed_error = json.loads(error_body)
            error_message = parsed_error.get("error", {}).get("message", "Unknown API error")
        except Exception:
            error_message = error_body

        if http_ex.code in [400, 401, 403]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WeatherAPI Validation Failure (Status {http_ex.code}): {error_message}"
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"External gateway returned unexpected server error status: {http_ex.code}"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"The server is receiving an HTML webpage instead of JSON. This confirms your "
                f"WEATHER_API_KEY environment variable token is corrupt or invalid. "
                f"Please re-paste your key cleanly into your deployment dashboard settings."
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"External weather service transport failed: {str(e)}"
        )

    # 5. Extract attributes safely from verified WeatherAPI data schemas
    try:
        extracted_city = weather_data["location"]["name"]
        extracted_temp = float(weather_data["current"]["temp_c"])
        extracted_condition = weather_data["current"]["condition"]["text"]
        extracted_humidity = int(weather_data["current"]["humidity"])
    except (KeyError, IndexError, TypeError) as parse_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Schema mapping structure mismatch on API parameters: {str(parse_err)}"
        )

    # 6. Synchronize and update local database cache table rows
    current_utc_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    if local_record:
        local_record.city_name = extracted_city
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
            detail="Administrative privileges are required to perform this cache clearance."
        )

    query = db.query(WeatherCache)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return WeatherPurgeResponse(success=True, records_deleted=deleted_count)
