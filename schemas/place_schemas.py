from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.place import PlaceStatusEnum  # 👈 Import your explicit place lifecycle enum here


class PlaceCreate(BaseModel):
    """ Validates incoming JSON data from the admin dashboard when creating a spot. """
    name: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=10)

    # 📍 MAP GPS COORDINATES
    latitude: float
    longitude: float
    physical_address: Optional[str] = None

    # 🖼️ MULTI-IMAGE ARRAY (Replaces the old single string column input)
    images: List[str] = Field(..., min_length=1, description="Array of hosted image URLs")

    # 🏠 DATABASE FOREIGN KEYS (Replaces old plain text strings)
    location_id: int
    category_id: int

    # 📋 SRS SPECS ADDITIONAL COLUMNS
    entry_information: Optional[str] = "Open to the public"
    recommended_visiting_information: Optional[str] = None
    travel_tips: Optional[str] = None


class PlaceUpdate(BaseModel):
    """ Handles partial or full updates via PUT/PATCH endpoints. """
    name: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    physical_address: Optional[str] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None
    entry_information: Optional[str] = None
    recommended_visiting_information: Optional[str] = None
    travel_tips: Optional[str] = None


class PlaceResponse(BaseModel):
    """ Shapes output JSON data contracts returned to travelers and admins. """
    id: int
    name: str
    description: str
    latitude: float
    longitude: float
    physical_address: Optional[str]

    entry_information: Optional[str]
    recommended_visiting_information: Optional[str]
    travel_tips: Optional[str]

    status: PlaceStatusEnum  # 👈 CHANGED: Enforces explicit lifecycle dropdown type checks
    location_id: int
    category_id: int
    creator_id: int  # Tracks who created the spot for accountability
    updated_by: Optional[int]  # Tracks who updated the spot for accountability

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 👈 Modern Pydantic v2 binding


class PlaceDetailResponse(BaseModel):
    """ Custom response structure to deliver full details alongside the image list array. """
    place: PlaceResponse
    images: List[str] = Field(default=[])
