from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# --- Hotel SCHEMAS ---
class HotelBookingCreate(BaseModel):
    hotel_id: int = Field(gt=0)
    check_in_date: date       # Input format from mobile client: YYYY-MM-DD
    check_out_date: date      # Input format from mobile client: YYYY-MM-DD

class HotelBookingUpdate(BaseModel):
    check_in_date: Optional[date] = None   # Optional field for flexible mobile client modifications
    check_out_date: Optional[date] = None  # Optional field for flexible mobile client modifications

class HotelBookingResponse(BaseModel):
    id: int
    hotel_id: int
    user_id: int
    check_in_date: date
    check_out_date: date
    total_price: int          # Calculated nightly price saved in PKR
    created_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to cleanly serialize standard SQLAlchemy row instances


# --- RESTAURANT SCHEMAS ---
class RestaurantBookingCreate(BaseModel):
    restaurant_id: int = Field(gt=0)
    reservation_date: date
    reservation_time: str
    number_of_guests: int = Field(gt=0, le=20) # Enforce a logical table booking cap limit

class RestaurantBookingUpdate(BaseModel):
    reservation_date: Optional[date] = None
    reservation_time: Optional[str] = None
    number_of_guests: Optional[int] = Field(default=None, gt=0, le=20)

class RestaurantBookingResponse(BaseModel):
    id: int
    restaurant_id: int
    user_id: int
    reservation_date: date
    reservation_time: str
    number_of_guests: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- TRANSPORT SCHEMAS ---
class TransportBookingCreate(BaseModel):
    transport_type: str        # e.g., "Rent-a-Car", "Bus"
    departure_date: date
    source_city: str
    destination_city: str
    total_price: int = Field(gt=0) # Base mock/calculated cost input in PKR

class TransportBookingUpdate(BaseModel):
    departure_date: Optional[date] = None
    source_city: Optional[str] = None
    destination_city: Optional[str] = None

class TransportBookingResponse(BaseModel):
    id: int
    user_id: int
    transport_type: str
    departure_date: date
    source_city: str
    destination_city: str
    total_price: int
    created_at: datetime

    class Config:
        from_attributes = True