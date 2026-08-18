from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

class TripCreateInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The custom traveler-defined name for this trip container")
    destination_town: str = Field(..., min_length=2, max_length=100, description="Target city or district query string inside Pakistan")
    start_date: date = Field(..., description="The planned start date of the travel itinerary")
    end_date: date = Field(..., description="The planned end date of the travel itinerary")
    hotel_id: Optional[int] = Field(None, gt=0, description="Optional primary key reference to an accommodation spot")
    restaurant_ids: List[int] = Field(default_factory=list, description="Array collection of manually saved restaurant IDs")
    place_ids: List[int] = Field(default_factory=list, description="Array collection of manually saved tourist place IDs")

class TripContainerResponse(BaseModel):
    id: int = Field(..., description="Unique structural primary key identifier for this trip container portfolio")
    user_id: int = Field(..., description="The identity token tracking identifier matching the folder owner user profile")
    title: str = Field(..., description="The custom folder name text metadata")
    destination_town: str = Field(..., description="The validated geopolitical destination name")
    start_date: date = Field(..., description="The absolute structural start date tracking window bound")
    end_date: date = Field(..., description="The absolute structural end date tracking window bound")
    hotel_id: Optional[int] = Field(None, description="Linked accommodation primary identifier match")
    restaurant_ids: List[int] = Field(..., description="Array collection of all saved restaurant IDs")
    place_ids: List[int] = Field(..., description="Array collection of all saved tourist place IDs")
