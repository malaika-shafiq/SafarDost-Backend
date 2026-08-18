from pydantic import BaseModel
from typing import Optional

class PlaceCreate(BaseModel):
    name: str
    location: str      # e.g., "Lahore", "Hunza Valley"
    category: str      # e.g., "Fort", "Lake", "Valley"
    description: str
    image: Optional[str] = None  # A URL string to an online image/photo

class PlaceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

class PlaceResponse(BaseModel):
    id: int
    name: str
    location: str      # Matches table column exactly
    category: str      # e.g., "Lake", "Fort", "Valley"
    description: str
    image: Optional[str] = None  # Holds the image link/URL string for the mobile app

    class Config:
        from_attributes = True  # Allows Pydantic to read classic SQLAlchemy columns
