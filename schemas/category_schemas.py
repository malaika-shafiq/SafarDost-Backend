from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
# 👈 Import your explicit category enum from the model file here
from models.category import CategoryStatusEnum

class CategoryCreate(BaseModel):
    """ Validates the data incoming from the frontend or admin panel. """
    name: str = Field(..., min_length=2, max_length=50, description="The category name text label")
    description: Optional[str] = Field(None, description="Optional text context explaining the category purpose")

class CategoryResponse(BaseModel):
    """ Explicitly shapes the JSON output returned back to the client application safely. """
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: CategoryStatusEnum  # 👈 CHANGED: Swapped out 'str' for 'CategoryStatusEnum'
    creator_id: int  # 👈 Added to track who built this category record
    updated_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
