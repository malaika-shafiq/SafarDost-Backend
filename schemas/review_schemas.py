from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.transport import TransportStatusEnum, TransportRentalModeEnum


class TransportCreate(BaseModel):
    """
    Validates incoming JSON payloads sent from the admin transport panel dashboard.
    Captures multi-image vehicle string URLs, rental modes, and transit specifications.
    """
    transport_type: str = Field(..., min_length=2, max_length=150, description="e.g., Grand Cabin, 4x4 Jeep Prado")
    from_location: str = Field(..., min_length=2, max_length=100, description="Starting departure point / city")
    to_location: str = Field(..., min_length=2, max_length=100, description="Target arrival destination / region")
    departure_time: str = Field(...,
                                description="Scheduled departure description details, e.g., 'Every Friday 06:00 AM'")
    arrival_time: str = Field(..., description="Estimated arrival details, e.g., '12 Hours approximate transit time'")
    price: float = Field(..., gt=0, description="Private vehicle flat fare OR individual seat ticket price value")
    capacity: int = Field(..., ge=1, description="Total passenger seating capacity constraints")

    rental_mode: TransportRentalModeEnum = Field(
        default=TransportRentalModeEnum.private_dedicated,
        description="Defines whether the vehicle is rented entirely or per individual seat ticket"
    )

    # 🖼️ MULTI-IMAGE HANDLER ARRAY (Follows your exact unified polymorphic pattern)
    images: List[str] = Field(..., min_length=1, description="Array containing hosted vehicle image URL strings")

    # 🏠 DATABASE FOREIGN KEYS
    location_id: int = Field(..., description="The matching master entry ID inside locations table")


class TransportUpdate(BaseModel):
    """ Handles partial vehicle attributes alterations safely via administration controllers. """
    transport_type: Optional[str] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    price: Optional[float] = None
    capacity: Optional[int] = None
    rental_mode: Optional[TransportRentalModeEnum] = None
    images: Optional[List[str]] = None
    location_id: Optional[int] = None


class TransportResponse(BaseModel):
    """ Shapes the structured base JSON output returned to tracking list views and grids. """
    id: int
    transport_type: str
    from_location: str
    to_location: str
    departure_time: str
    arrival_time: str
    price: float
    capacity: int

    rental_mode: TransportRentalModeEnum
    available_seats: int

    status: TransportStatusEnum
    location_id: int
    creator_id: int
    updated_by: Optional[int]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 📊 NESTED SCHEMA CONTRACT REFACTORED TO INCLUDE RELATIONAL FEEDBACK ITEMS:
class TransportReviewItem(BaseModel):
    id: int
    rating: int
    comment: str
    reviewer_name: str
    created_at: datetime


class TransportDetailResponse(BaseModel):
    """ Advanced nested payload data contract custom-tailored to deliver seamless mobile profile pages. """
    transport: TransportResponse
    images: List[str] = Field(default=[], description="Unfolded cloud storage photo string URL arrays")
    reviews: List[TransportReviewItem] = Field(default=[],
                                               description="Polymorphic feedback arrays from active travelers")
    average_rating: float = Field(default=0.0, description="On-the-fly rounded aggregate star score calculation value")
    total_reviews_count: int = Field(default=0, description="Total active feedback rows log sum count")
