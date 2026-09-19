from pydantic import BaseModel
from typing import List

class TimeSlotRating(BaseModel):
    label: str
    rating: str

class ActivitySuitabilityItem(BaseModel):
    activity_type: str
    title: str
    status: str
    time_slots: List[TimeSlotRating]

class PollenCounts(BaseModel):
    tree: str
    grass: str
    ragweed: str

class AirQualityData(BaseModel):
    aqi_level: str
    aqi_score: int
    pollen: PollenCounts

# 🚀 INJECTED TODAY'S MAX AND MIN TEMPERATURE VARIABLES:
class WeatherResponse(BaseModel):
    city_name: str
    temperature_c: float
    max_temp_c: float
    min_temp_c: float
    condition_text: str
    humidity: int
    activities: List[ActivitySuitabilityItem]
    air_quality: AirQualityData

class WeatherPurgeResponse(BaseModel):
    success: bool
    records_deleted: int
