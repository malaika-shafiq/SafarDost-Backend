from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.hotel import HotelStatusEnum, RoomStatusEnum


# ==========================================
# 🏢 ROOM INVENTORY VALUATION SCHEMAS
# ==========================================
class RoomCreate(BaseModel):
    """ Validates individual room records passed inside the parent hotel initialization body. """
    room_type: str = Field(..., min_length=2, max_length=100, description="e.g., Deluxe Suite, Standard Twin")
    description: Optional[str] = Field(None, description="Balcony details, bed configuration, or scenery descriptions")
    price_per_night: float = Field(..., gt=0, description="Nightly charge rate requirement string value")
    capacity: int = Field(2, ge=1, description="Maximum sleep occupant limits per night")


class RoomResponse(BaseModel):
    """ Shapes individual room data attributes sent back out across the network. """
    id: int
    hotel_id: int
    room_type: str
    description: Optional[str]
    price_per_night: float
    capacity: int
    status: RoomStatusEnum

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 🏨 HOTEL ESTABLISHMENT VALIDATION SCHEMAS
# ==========================================
class HotelCreate(BaseModel):
    """
    Validates incoming hotel payload blocks sent from the administrative dashboard panel.
    Captures polymorphic picture URLs and nested room inventories in a single network request.
    """
    name: str = Field(..., min_length=2, max_length=150, description="The official name of the hotel property")
    description: str = Field(..., min_length=10, description="Deep property summary overview text context")
    contact_information: str = Field(..., min_length=5, max_length=100, description="Phone lines or desk numbers")
    facilities: Optional[str] = Field(None,
                                      description="Comma-separated amenity string list, e.g., WiFi, AC, Parking, Heater")

    # 🖼️ MULTI-IMAGE HANDLER ARRAY (Follows your exact unified polymorphic pattern)
    images: List[str] = Field(..., min_length=1, description="Array containing hosted landscape media file URL strings")

    # 🏠 DATABASE FOREIGN KEYS
    location_id: int = Field(..., description="The matching master entry ID inside locations table")
    category_id: int = Field(..., description="The matching master entry ID inside categories table")

    # 🗂️ NESTED INVENTORY ARRIVAL ARRAY
    rooms: List[RoomCreate] = Field(..., min_length=1,
                                    description="List tracking structural room configurations to onboard")


class HotelUpdate(BaseModel):
    """ Handles partial properties metadata overrides cleanly via admin control screens. """
    name: Optional[str] = None
    description: Optional[str] = None
    contact_information: Optional[str] = None
    facilities: Optional[str] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None


class HotelResponse(BaseModel):
    """ Shapes the structured base hotel payload returned to tracking list views. """
    id: int
    name: str
    description: str
    contact_information: str
    facilities: Optional[str]
    status: HotelStatusEnum

    location_id: int
    category_id: int
    creator_id: int  # Tracks administrative creation accountability paths
    updated_by: Optional[int]  # Tracks administrative update accountability paths

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 👈 Modern Pydantic v2 standard binding


class HotelDetailResponse(BaseModel):
    """ Advanced nested payload data contract custom-tailored to feed your traveler app profile pages. """
    hotel: HotelResponse
    images: List[str] = Field(default=[], description="Unfolded media storage URL link arrays")
    rooms: List[RoomResponse] = Field(default=[], description="Unfolded child room options inventory lists")
