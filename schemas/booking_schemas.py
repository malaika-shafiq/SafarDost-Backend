from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime
from typing import Optional, List
from models.booking import BookingTypeEnum, BookingStatusEnum, PaymentStatusEnum


# ==========================================
# 🧱 DOMAIN CHILD LEVEL REQUEST SEGMENTS
# ==========================================

class HotelBookingRequest(BaseModel):
    """ Captures detailed room choices and guest counts (Section 2 & 10) [INDEX: 0.1.10, 0.1.22] """
    hotel_id: int = Field(..., description="Target database hotel row ID")
    room_id: int = Field(..., description="Target specific bedroom row selection ID")
    check_in: datetime = Field(..., description="Check-in arrival date timestamp")
    check_out: datetime = Field(..., description="Check-out departure calendar timestamp")
    number_of_rooms: int = Field(1, ge=1, description="Total bedrooms pool to reserve")
    adults: int = Field(1, ge=1, description="Adult headcounts occupant count")
    children: int = Field(0, ge=0, description="Minor occupant count numbers")
    child_ages: Optional[str] = Field(None, description="Comma-separated age string, e.g., '5,9'")


class RestaurantBookingRequest(BaseModel):
    """ Captures table slots, seating choices, and times (Section 4 & 11) [INDEX: 0.1.15, 0.1.22] """
    restaurant_id: int = Field(..., description="Target database restaurant record ID")
    reservation_date: datetime = Field(..., description="Reservation target date timestamp")
    reservation_time: str = Field(..., description="Time window format, e.g., '08:00 PM'")
    adults: int = Field(1, ge=1, description="Adult guest seating headcount")
    children: int = Field(0, ge=0, description="Child guest seating headcount")
    seating_preference: Optional[str] = Field("No preference", description="Indoor, Outdoor, or No preference")


class TransportBookingRequest(BaseModel):
    """ Captures vehicle selections, route nodes, and timetables (Section 7 & 12) [INDEX: 0.1.17, 0.1.23] """
    transport_id: int = Field(..., description="Target transit fleet database ID")
    from_location: str = Field(..., description="Departure starting point station text")
    to_location: str = Field(..., description="Target final arrival location point")
    departure_date: datetime = Field(..., description="Departure route target calendar date")
    departure_time: str = Field(..., description="Fleet vehicle operational launch hour")
    adults: int = Field(1, ge=1, description="Adult head passenger seats capacity")
    children: int = Field(0, ge=0, description="Child passenger headcount seats tracking")
    pickup_location: Optional[str] = Field(None, description="Detailed pickup address text details")
    dropoff_location: Optional[str] = Field(None, description="Detailed terminal dropping off location specs")


class TourBookingRequest(BaseModel):
    """ Captures predefined holiday group package entries (Section 16) [INDEX: 0.1.27] """
    package_id: int = Field(..., description="Target tour package bundle catalog code")
    number_of_travelers: int = Field(1, ge=1, description="Total passenger tickets seats to request")
    adults: int = Field(1, ge=1, description="Adult passenger seat distributions")
    children: int = Field(0, ge=0, description="Child passenger seat distributions")


# ==========================================
# 🏛️ MASTER TRANSACT INITIALIZATION PAYLOAD
# ==========================================

class BookingCreate(BaseModel):
    """
    Unified master entry payload endpoint body [INDEX: 0.1.21].
    Employs Option B contact mapping strings along with CNIC identification [INDEX: 0.1.12, 0.1.24].
    """
    booking_type: BookingTypeEnum = Field(..., description="Categorization: hotel, restaurant, transport, or tour")

    # Option B: Booking-specific parameters tracking primary guest details (Section 13) [INDEX: 0.1.24]
    contact_name: str = Field(..., min_length=2, max_length=100, description="Primary traveler full name")
    contact_phone: str = Field(..., min_length=5, max_length=50, description="Active emergency contact line")
    contact_email: EmailStr = Field(..., description="Transactional digital stay voucher notification inbox")

    # 💳 NATIONAL IDENTITY RECORD VERIFICATION FIELD
    cnic_number: str = Field(..., min_length=5, max_length=50, description="Primary traveler CNIC verification number")

    special_requests: Optional[str] = Field(None, description="e.g., Late check-in, Extra mattress, Glacial views")

    # Optional payload blocks matching the active booking selection domain path
    hotel_details: Optional[HotelBookingRequest] = None
    restaurant_details: Optional[RestaurantBookingRequest] = None
    transport_details: Optional[TransportBookingRequest] = None
    tour_details: Optional[TourBookingRequest] = None


# ==========================================
# 📊 DOMAIN CHILD LEVEL RESPONSE SEGMENTS
# ==========================================

class HotelBookingResponse(BaseModel):
    id: int
    booking_id: int
    hotel_id: int
    room_id: int
    check_in: datetime
    check_out: datetime
    number_of_rooms: int
    adults: int
    children: int
    child_ages: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class RestaurantBookingResponse(BaseModel):
    id: int
    booking_id: int
    restaurant_id: int
    reservation_date: datetime
    reservation_time: str
    adults: int
    children: int
    seating_preference: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TransportBookingResponse(BaseModel):
    id: int
    booking_id: int
    transport_id: int
    from_location: str
    to_location: str
    departure_date: datetime
    departure_time: str
    adults: int
    children: int
    pickup_location: Optional[str]
    dropoff_location: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class TourBookingResponse(BaseModel):
    id: int
    booking_id: int
    package_id: int
    number_of_travelers: int
    adults: int
    children: int

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 🏛️ UNIFIED CENTRAL MASTER OUTPUT RESPONSE
# ==========================================

class BookingResponse(BaseModel):
    """
    Shapes the complete structured JSON payload output returned back to the tracking interfaces.
    Unfolds specific child relationship extensions dynamically based on the booking type context.
    """
    id: int
    user_id: int
    booking_type: BookingTypeEnum

    # Primary Guest Contacts (Option B + CNIC parameters verified)
    contact_name: str
    contact_phone: str
    contact_email: EmailStr
    cnic_number: str

    total_amount: float
    booking_status: BookingStatusEnum
    payment_status: PaymentStatusEnum
    special_requests: Optional[str]

    created_at: datetime
    updated_at: datetime

    # Conditionally nested child data objects loaded dynamically on demand
    hotel_details: Optional[HotelBookingResponse] = None
    restaurant_details: Optional[RestaurantBookingResponse] = None
    transport_details: Optional[TransportBookingResponse] = None
    tour_details: Optional[TourBookingResponse] = None

    model_config = ConfigDict(from_attributes=True)
