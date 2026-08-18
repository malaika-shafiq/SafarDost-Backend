from pydantic import BaseModel, Field

class CoordinateResponse(BaseModel):
    address_query: str = Field(..., description="The original location text query provided by the user client")
    latitude: float = Field(..., description="The exact geographic GPS latitude coordinate mapping bound")
    longitude: float = Field(..., description="The exact geographic GPS longitude coordinate mapping bound")
    formatted_address: str = Field(..., description="The officially verified clean postal/regional location string returned by Google")

class RouteDistanceInput(BaseModel):
    origin: str = Field(..., min_length=2, description="The starting location or city in Pakistan, e.g., Lahore")
    destination: str = Field(..., min_length=2, description="The ending location or city, e.g., Hunza")

class RouteDistanceResponse(BaseModel):
    origin: str = Field(..., description="Verified starting terminal boundary")
    destination: str = Field(..., description="Verified ending arrival terminal boundary")
    distance_text: str = Field(..., description="Human-readable travel distance string (e.g., 612 km)")
    duration_text: str = Field(..., description="Human-readable estimated travel timeframe duration (e.g., 11 hours 45 mins)")
