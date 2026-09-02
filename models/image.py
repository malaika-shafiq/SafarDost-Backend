import enum
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func


# 1. Define explicit types to avoid unexpected plain text string entries
class ImageResourceTypeEnum(str, enum.Enum):
    place = "place"
    hotel = "hotel"
    restaurant = "restaurant"
    review = "review"


class Images(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False, comment="Cloudinary or S3 hosted URL link path")
    # 2. Polymorphic Binding Fields
    resource_type = Column(Enum(ImageResourceTypeEnum), nullable=False,
                           comment="Identifies which feature owns this photo asset")
    resource_id = Column(Integer, nullable=False, comment="The matching entry ID of the related module table row")

    # 🏛️ UNIVERSAL AUDIT TRAIL COUPLING
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="Tracks the user or admin who uploaded this photo")

    # Tracking metrics for the dashboard audits
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    creator = relationship("Users")
