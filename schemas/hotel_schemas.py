from pydantic import BaseModel, Field
from typing import Optional

class HotelCreate(BaseModel):
    name: str
    location: str            # e.g., "Hunza Valley", "Murree"
    price_per_night: int = Field(gt=0) # Nightly rate in PKR must be greater than 0
    rating: float = Field(default=0.0, ge=0, le=5)
    image: Optional[str] = None  # Cloudinary string asset link

class HotelUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    price_per_night: Optional[int] = Field(default=None, gt=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    image: Optional[str] = None

class HotelResponse(BaseModel):
    id: int
    name: str
    location: str
    price_per_night: int
    rating: float
    image: Optional[str] = None

    class Config:
        from_attributes = True  # Allows Pydantic to cleanly read classic SQLAlchemy model instances
