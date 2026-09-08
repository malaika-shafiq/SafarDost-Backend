from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
from models.review import ReviewStatusEnum  # 👈 Import your explicit lifecycle enum here


class ReviewCreate(BaseModel):
    """
    Validates incoming JSON payloads sent from travelers' mobile applications.
    Accepts star ratings, shared experiences text, and multi-image photo uploads.
    """
    rating: int = Field(..., ge=1, le=5, description="Star rating grading from 1 to 5")
    comment: str = Field(..., min_length=5,
                         description="Detailed travel text review commentary content or shared experience")

    # 🖼️ MULTI-PHOTO EXPERIENCES ARRAY (Image 1 requirement)
    images: Optional[List[str]] = Field(default=[], description="Array containing traveler-uploaded photo URLs")

    # 🔗 RELATIONAL TARGET KEYS (A review must target exactly one entity)
    place_id: Optional[int] = Field(None, description="Target tourist spot ID if reviewing a place")
    hotel_id: Optional[int] = Field(None, description="Target hotel ID if reviewing a stay")
    restaurant_id: Optional[int] = Field(None, description="Target restaurant ID if reviewing a dining spot")


class ReviewUpdate(BaseModel):
    """
    Validates modification payloads sent when a traveler edits their own review.
    Allows changing the star rating score, updating commentary text, or swapping photo listings.
    """
    rating: Optional[int] = Field(None, ge=1, le=5, description="Updated star rating grading from 1 to 5")
    comment: Optional[str] = Field(None, min_length=5,
                                   description="Updated travel text review commentary or experience details")
    images: Optional[List[str]] = Field(None, description="Updated array containing hosted image URL paths")


class ReviewResponse(BaseModel):
    """ Shapes basic output payloads for general listings feeds. """
    id: int
    rating: int
    comment: str
    status: ReviewStatusEnum  # 👈 Enforces explicit database Enum state checks
    user_id: int

    place_id: Optional[int]
    hotel_id: Optional[int]
    restaurant_id: Optional[int]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewDetailResponse(BaseModel):
    """ Comprehensive output format that bundles the review text, reviewer name, and photos together. """
    review: ReviewResponse
    reviewer_name: str = Field(..., description="The name of the traveler who shared the experience")
    images: List[str] = Field(default=[],
                              description="Unfolded array list of raw image URL strings uploaded by the traveler")
