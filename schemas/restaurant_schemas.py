from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.restaurant import RestaurantStatusEnum  # 👈 Import your explicit lifecycle enum here


class RestaurantCreate(BaseModel):
    """
    Validates incoming JSON payloads sent from the admin panel dashboard.
    Captures multi-image string URLs and explicit restaurant metadata.
    """
    name: str = Field(..., min_length=2, max_length=150, description="The restaurant name text label")
    description: str = Field(..., min_length=10, description="Deep profile description summary text")
    cuisine: str = Field(..., min_length=2, max_length=100, description="Cuisine type, e.g., Traditional, Continental")
    menu_details: Optional[str] = Field(None, description="Menu specialities or highlighted dishes text")
    price_range: str = Field(..., description="Price spectrum indicator, e.g., Low, Medium, High")
    contact: str = Field(..., min_length=5, max_length=50, description="Phone numbers or booking contact desks")
    opening_information: str = Field(..., description="Operational opening hours, e.g., 12:00 PM - 12:00 AM")
    table_capacity: Optional[int] = Field(None, ge=1, description="Estimated total seating capacity available")

    # 🖼️ MULTI-IMAGE HANDLER ARRAY (Follows your exact Places design)
    images: List[str] = Field(..., min_length=1, description="Array list containing hosted image URL string paths")

    # 🏠 DATABASE FOREIGN KEYS
    location_id: int = Field(..., description="The matching master entry ID inside locations table")
    category_id: int = Field(..., description="The matching master entry ID inside categories table")


class RestaurantUpdate(BaseModel):
    """ Handles full or partial fields modification updates safely via administration controllers. """
    name: Optional[str] = None
    description: Optional[str] = None
    cuisine: Optional[str] = None
    menu_details: Optional[str] = None
    price_range: Optional[str] = None
    contact: Optional[str] = None
    opening_information: Optional[str] = None
    table_capacity: Optional[int] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None
    category_id: Optional[int] = None


class RestaurantResponse(BaseModel):
    """ Shapes the structured JSON output returned back to the mobile layout views. """
    id: int
    name: str
    description: str
    cuisine: str
    menu_details: Optional[str]
    price_range: str
    contact: str
    opening_information: str
    table_capacity: Optional[int]

    status: RestaurantStatusEnum  # 👈 Enforces your explicit database Enum state checks
    location_id: int
    category_id: int
    creator_id: int  # Tracks administrative creation accountability paths
    updated_by: Optional[int]  # Tracks administrative update accountability paths

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  # 👈 Modern Pydantic v2 binding


class RestaurantDetailResponse(BaseModel):
    """ Advanced nested payload schema designed to feed your React Native mobile layout profile views. """
    restaurant: RestaurantResponse
    images: List[str] = Field(default=[], description="Unfolded cloud storage photo string URL lists")
