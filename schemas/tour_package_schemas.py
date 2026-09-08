from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.tour_package import PackageStatusEnum


class TourPackageCreate(BaseModel):
    """ Validates incoming payloads sent from the admin tour package publishing panel. """
    name: str = Field(..., min_length=2, max_length=150, description="The name of the tour package")
    description: str = Field(..., min_length=10, description="Detailed package summary overview")
    duration: str = Field(..., description="e.g., 5 Days / 4 Nights")
    price: float = Field(..., gt=0, description="Price rate per single traveler head")
    available_slots: int = Field(..., ge=1, description="Total traveler slot capacities allowed")

    start_date: datetime = Field(..., description="Tour group departure start date timestamp")
    end_date: datetime = Field(..., description="Tour group arrival end date timestamp")

    activities: Optional[str] = Field(None, description="Itinerary timeline layout text explanations")
    transportation_information: Optional[str] = Field(None, description="Included travel mode descriptions")
    included_services: Optional[str] = Field(None, description="Services overview items listing details")

    # 🖼️ MULTI-IMAGE HANDLER ARRAY
    images: List[str] = Field(..., min_length=1, description="List containing hosted tour photo URL string fields")

    # 🏠 DATABASE FOREIGN KEYS & LINK IDENTIFIER ARRAYS
    location_id: int = Field(..., description="The matching master entry ID inside locations table")
    places_ids: List[int] = Field(..., min_length=1,
                                  description="Array of database IDs of places included in this tour")
    hotels_ids: List[int] = Field(..., min_length=1,
                                  description="Array of database IDs of hotels included in this tour")


class TourPackageUpdate(BaseModel):
    """ Handles partial attributes mutations cleanly via admin control screens. """
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[float] = None
    available_slots: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    activities: Optional[str] = None
    transportation_information: Optional[str] = None
    included_services: Optional[str] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None
    places_ids: Optional[List[int]] = None
    hotels_ids: Optional[List[int]] = None


class TourPackageResponse(BaseModel):
    """ Shapes basic output fields returned to public browsing grids. """
    id: int
    name: str
    description: str
    duration: str
    price: float
    available_slots: int
    start_date: datetime
    end_date: datetime
    activities: Optional[str]
    transportation_information: Optional[str]
    included_services: Optional[str]
    status: PackageStatusEnum

    location_id: int
    creator_id: int
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
