from pydantic import BaseModel, Field
from typing import Optional

class GearItemCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5)
    price_pkr: float = Field(..., gt=0.0)
    stock_quantity: int = Field(default=0, ge=0)

class GearItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price_pkr: float
    stock_quantity: int

    class Config:
        from_attributes = True

class GearOrderCreate(BaseModel):
    gear_item_id: int = Field(..., gt=0)
    purchase_quantity: int = Field(default=1, gt=0)

class GearOrderResponse(BaseModel):
    id: int
    user_id: int
    gear_item_id: int
    purchase_quantity: int
    total_invoice_pkr: float

    class Config:
        from_attributes = True
