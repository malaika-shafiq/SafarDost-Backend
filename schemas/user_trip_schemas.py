from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from models.user_trip import TripScopeEnum

class UserTripCreate(BaseModel):
    """ Validates incoming payloads when creating a trip manually or from an AI prompt response """
    trip_title: str = Field(..., min_length=2, max_length=150, description="e.g., Autumn Trip to Gilgit")
    destination: str = Field(..., min_length=2, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    itinerary_details: str = Field(..., description="Daily scheduling texts blocks")
    scope: TripScopeEnum = Field(default=TripScopeEnum.current)


class UserTripUpdate(BaseModel):
    """ Handles partial or complete structural itinerary modifications cleanly via traveler inputs """
    trip_title: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    itinerary_details: Optional[str] = None
    scope: Optional[TripScopeEnum] = None


class UserTripResponse(BaseModel):
    """ Shapes the structured output JSON payload returned to mobile grids and timelines """
    id: int
    user_id: int
    trip_title: str
    destination: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    itinerary_details: str
    scope: TripScopeEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
