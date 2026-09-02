from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ImageResponse(BaseModel):
    """ Shapes the output JSON metadata when returning photo records. """
    id: int
    image_url: str
    resource_type: str
    resource_id: int
    creator_id: int  # 👈 Include it here to satisfy the audit requirement
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
