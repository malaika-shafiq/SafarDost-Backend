from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReviewCreate(BaseModel):
    rating: int = Field(default=5, ge=1, le=5)
    comment: str = Field(..., min_length=3, max_length=1000)
    hotel_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    place_id: Optional[int] = None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, min_length=3, max_length=1000)

class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: str
    image_url: Optional[str] = None
    created_at: datetime
    user_id: int
    hotel_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    place_id: Optional[int] = None

    class Config:
        from_attributes = True
