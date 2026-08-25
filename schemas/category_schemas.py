from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

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
    status: str

    model_config = ConfigDict(from_attributes=True)
