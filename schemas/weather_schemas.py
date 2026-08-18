from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    city_name: str = Field(..., description="Target city name returned by the weather service")
    temperature_c: float = Field(..., description="Current temperature recorded in Celsius")
    condition_text: str = Field(..., description="Atmospheric condition text description")
    humidity: int = Field(..., description="Atmospheric humidity percentage level")


# Purge mean saaf karna
class WeatherPurgeResponse(BaseModel):
    success: bool = Field(..., description="Status flag indicating if the database purge completed")
    records_deleted: int = Field(..., description="The total number of cached weather rows removed from SQLite")
