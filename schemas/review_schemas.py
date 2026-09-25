from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.review import ReviewStatusEnum


class ReviewCreate(BaseModel):
    """ Validates incoming payloads sent from travelers' mobile applications. """
    rating: int = Field(..., ge=1, le=5, description="Star rating grading from 1 to 5")
    comment: str = Field(..., min_length=5, description="Detailed travel text review commentary content")
    images: Optional[List[str]] = Field(default=[], description="Array containing traveler-uploaded photo URLs")

    # 🔗 RELATIONAL TARGET ENTITIES MAP:
    place_id: Optional[int] = Field(None, description="Target tourist spot ID if reviewing a place")
    hotel_id: Optional[int] = Field(None, description="Target hotel ID if reviewing a stay")
    restaurant_id: Optional[int] = Field(None, description="Target restaurant ID if reviewing a dining spot")
    transport_id: Optional[int] = Field(None, description="Target vehicle fleet ID if reviewing a transport option")


class ReviewUpdate(BaseModel):
    """ Validates modification payloads sent when a traveler edits their own review. """
    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated star rating grading from 1 to 5")
    comment: Optional[str] = Field(None, min_length=5, description="Updated travel text review commentary")
    images: Optional[List[str]] = None


# 🚀 THE CRITICAL CRASH FIX: EXPLICITLY BOUND RESPONSE CONTRACT MODEL:
class ReviewResponse(BaseModel):
    """ Shapes basic output payloads for general listings feeds. """
    id: int
    rating: int
    comment: str
    status: ReviewStatusEnum
    user_id: int

    place_id: Optional[int]
    hotel_id: Optional[int]
    restaurant_id: Optional[int]
    transport_id: Optional[int]  # Shapes the value for output JSON payloads

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
