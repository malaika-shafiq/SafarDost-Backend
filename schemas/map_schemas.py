from pydantic import BaseModel, Field


class CoordinateResponse(BaseModel):
    """ Shapes geocoding lookup parameters for global mobile UI maps """
    address_query: str = Field(..., description="The original location text query provided by the user client")
    latitude: float = Field(..., description="The exact geographic GPS latitude coordinate mapping bound")
    longitude: float = Field(..., description="The exact geographic GPS longitude coordinate mapping bound")
    formatted_address: str = Field(...,
                                   description="The officially verified clean postal/regional location string returned by Google")


class RouteDistanceInput(BaseModel):
    """ Validates target addresses when travelers check distance timelines """
    origin: str = Field(..., min_length=2, description="The starting location or city in Pakistan, e.g., Lahore")
    destination: str = Field(..., min_length=2, description="The ending location or city, e.g., Hunza")


class RouteDistanceResponse(BaseModel):
    """ Unified structural data model returning comprehensive human and numeric routing metrics """
    origin: str = Field(..., description="Verified starting terminal boundary")
    destination: str = Field(..., description="Verified ending arrival terminal boundary")

    distance_text: str = Field(..., description="Human-readable travel distance string (e.g., 612 km)")
    distance_value_meters: int = Field(...,
                                       description="Pure raw distance integer value in meters for calculation logic loops")

    duration_text: str = Field(...,
                               description="Human-readable estimated travel timeframe duration (e.g., 11 hours 45 mins)")
    duration_value_seconds: int = Field(...,
                                        description="Pure raw duration time integer value in seconds for timer modules")
