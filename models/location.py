import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum

class LocationStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class Locations(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)  # e.g., "Hunza"
    province_or_region = Column(String, nullable=False)             # e.g., "Gilgit-Baltistan"
    description = Column(Text, nullable=True)                       # Summary text block
    image_url = Column(String, nullable=True)                       # Cover landscape banner photo

    status = Column(
        Enum(LocationStatusEnum),
        default=LocationStatusEnum.active,
        server_default=LocationStatusEnum.active.value,
        nullable=False
    )

    # 🕒 Tracking metrics for dashboard audits
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 🔗 Relational Back-Links: Connects a city to all its nested marketplace resources
    places = relationship("Places", back_populates="location")
    # hotels = relationship("Hotels", back_populates="location")
    # restaurants = relationship("Restaurants", back_populates="location")
    # Inside models/location.py — Update your creator relationship line to match this:
    creator = relationship("Users", foreign_keys="[Locations.creator_id]")

