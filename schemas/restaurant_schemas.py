from pydantic import BaseModel, Field
from typing import Optional

class RestaurantCreate(BaseModel):
    name: str
    location: str
    price_range: str                  # e.g., "Budget", "Mid-Range", "Luxury"
    rating: float = Field(default=0.0, ge=0, le=5)
    image: Optional[str] = None       # Cloudinary string asset link

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    price_range: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    image: Optional[str] = None

class RestaurantResponse(BaseModel):
    id: int
    name: str
    location: str
    price_range: str
    rating: float
    image: Optional[str] = None

    class Config:
        from_attributes = True        # Allows Pydantic to cleanly read classic SQLAlchemy model instances
