import os
import json
import datetime
import urllib.request
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

    # 3. Use built-in urllib engine if missing, old, or forcefully refreshed
    API_KEY = os.getenv("WEATHER_API_KEY")
    SECURE_URL = f"https://weatherapi.com{API_KEY}&q={city}"

    try:
        with urllib.request.urlopen(SECURE_URL) as response:
            raw_data = response.read().decode("utf-8")
            weather_data = json.loads(raw_data)

    except urllib.error.HTTPError as http_ex:
        if http_ex.code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve weather details for the specified location."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="External communication barrier encountered."
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External weather service is temporarily offline."
        )

    # 4. Pull out individual pieces from response dictionary
    extracted_city = weather_data["location"]["name"]
    extracted_temp = weather_data["current"]["temp_c"]
    extracted_condition = weather_data["current"]["condition"]["text"]
    extracted_humidity = weather_data["current"]["humidity"]

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
    Protected Admin Endpoint: Force-clears all cached data rows from the weather_caches SQLite table.
    """
    # Safety switch: Verify if user dictionary role maps explicitly to admin [1, 2]
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to perform this cache clearance."
        )

    # Target the cache table and execute a delete operation [3]
    query = db.query(WeatherCache)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return WeatherPurgeResponse(
        success=True,
        records_deleted=deleted_count
    )
