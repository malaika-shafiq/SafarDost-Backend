from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from models.location import LocationStatusEnum

class LocationCreate(BaseModel):
    """ Validates the data payload incoming from the admin dashboard when adding a new region. """
    name: str = Field(..., min_length=2, max_length=100, description="Name of the city or region, e.g., Hunza")
    province_or_region: str = Field(..., min_length=2, max_length=100, description="Administrative region, e.g., Gilgit-Baltistan")
    description: Optional[str] = Field(None, description="A summary context overview introducing the valley")
    image_url: Optional[str] = Field(None, description="Landscape cover picture URL path for mobile view headers")

class LocationResponse(BaseModel):
    """ Shapes the structured JSON output context returned to the mobile app layout. """
    id: int
    name: str
    province_or_region: str
    description: Optional[str]
    image_url: Optional[str]
    status: LocationStatusEnum
    created_at: datetime
    creator_id: int  # 👈 Added to track who built this location record
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
