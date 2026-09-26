from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.hotel import HotelStatusEnum


# ==========================================
# 🏢 ROOM INVENTORY CATEGORY SCHEMAS
# ==========================================
class RoomCreate(BaseModel):
    """ Validates custom room groups embedded inside the hotel registration payload. """
    room_type: str = Field(..., min_length=2, max_length=100, description="e.g., Deluxe Suite, Standard Twin")
    description: Optional[str] = Field(None, description="Balcony details, bed configurations, or landscape views")
    price_per_night: float = Field(..., gt=0, description="Nightly charge rate baseline currency metric")
    capacity: int = Field(2, ge=1, description="Maximum sleep occupant limits per unit")
    quantity: int = Field(1, ge=1, description="Total active room supply stock count for this category")


class RoomResponse(BaseModel):
    """ Shapes custom room group structures sent back to your UI panels. """
    id: int
    hotel_id: int
    room_type: str
    description: Optional[str]
    price_per_night: float
    capacity: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class RoomQuantityUpdate(BaseModel):
    """ [NEW] Option 1: Validates a direct standalone adjustment to room stock metrics. """
    quantity: int = Field(..., ge=0, description="The newly updated total available stock count")


# ==========================================
# 🏨 HOTEL ESTABLISHMENT VALIDATION SCHEMAS
# ==========================================
class HotelCreate(BaseModel):
    """
    Validates incoming hotel payloads from the administrative panel.
    Captures multi-image arrays and nested room type batches in a single operation.
    """
    name: str = Field(..., min_length=2, max_length=150, description="The official name of the hotel property")
    description: str = Field(..., min_length=10, description="Deep property summary overview text context")
    contact_information: str = Field(..., min_length=5, max_length=100, description="Phone lines or desk numbers")
    facilities: Optional[str] = Field(None, description="Comma-separated amenity list, e.g., WiFi, AC, Parking, Heater")
    base_price: float = Field(..., gt=0, description="Baseline starting rate for this hotel")

    # Unified polymorphic media handler array
    images: List[str] = Field(..., min_length=1, description="Hosted landscape media file URL strings")

    # Database relational foreign key indicators
    location_id: int = Field(..., description="The matching master entry ID inside locations table")
    category_id: int = Field(..., description="The matching master entry ID inside categories table")

    # Nested inventory array (Admin defines custom rooms and quantities here)
    rooms: List[RoomCreate] = Field(..., min_length=1,
                                    description="List tracking structural room types and stock levels to onboard")


class HotelUpdate(BaseModel):
    """ Handles partial properties metadata overrides via admin control screens. """
    name: Optional[str] = None
    description: Optional[str] = None
    contact_information: Optional[str] = None
    facilities: Optional[str] = None
    base_price: Optional[float] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None


class HotelResponse(BaseModel):
    """ Shapes the base hotel core data returned to global tracking feeds. """
    id: int
    name: str
    description: str
    contact_information: str
    facilities: Optional[str]
    base_price: float
    status: HotelStatusEnum

    location_id: int
    category_id: int
    creator_id: int
    updated_by: Optional[int]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 📊 NEW NESTED CONTRACT SHAPING TRAVELER FEEDBACK REVIEWS NATIVELY:
class HotelReviewItem(BaseModel):
    id: int
    rating: int
    comment: str
    reviewer_name: str
    created_at: datetime


class HotelDetailResponse(BaseModel):
    """ Advanced nested data structure tailored to feed mobile traveler app profile screens. """
    hotel: HotelResponse
    images: List[str] = Field(default=[], description="Unfolded media storage URL link arrays")
    rooms: List[RoomResponse] = Field(default=[], description="Unfolded child room categories stock inventories")

    # 🚀 UPGRADED REAL-TIME TELEMETRY FIELDS FOR YOUR FEEDBACK HOOKS:
    reviews: List[HotelReviewItem] = Field(default=[], description="Polymorphic feedback arrays from active travelers")
    average_rating: float = Field(default=0.0, description="On-the-fly rounded aggregate star score calculation value")
    total_reviews_count: int = Field(default=0, description="Total active feedback rows log sum count")
