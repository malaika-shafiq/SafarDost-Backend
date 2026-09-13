import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# Global administrative lifecycle control state
class HotelStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Hotels(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, comment="Hotel Name")
    description = Column(Text, nullable=False, comment="Detailed property overview description")
    contact_information = Column(String, nullable=False, comment="Phone numbers or booking contact desks")
    facilities = Column(Text, nullable=True,
                        comment="Comma-separated amenities summary tokens, e.g., WiFi, AC, Parking")

    status = Column(
        Enum(HotelStatusEnum),
        default=HotelStatusEnum.active,
        server_default=HotelStatusEnum.active.value,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # System Accountability Audit Trails
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("Users", foreign_keys="[Hotels.creator_id]", back_populates="created_hotels")
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="hotels")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Categories", back_populates="hotels")

    reviews = relationship("Reviews", back_populates="hotel", cascade="all, delete-orphan")
    bookings = relationship("HotelBookings", back_populates="hotel", cascade="all, delete-orphan")

    # One-to-Many Bridge: A single hotel maps to a collection of unique room types
    rooms = relationship("HotelRooms", back_populates="hotel", cascade="all, delete-orphan")


class HotelRooms(Base):
    __tablename__ = "hotel_rooms"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)

    room_type = Column(String, nullable=False, comment="e.g., Deluxe Suite, Standard Twin, Luxury Family Room")
    description = Column(Text, nullable=True, comment="Specific room layout or landscape view features description")
    price_per_night = Column(Float, nullable=False, comment="Nightly rental baseline calculation metric")
    capacity = Column(Integer, default=2, nullable=False, comment="Maximum guest sleep capacity limits")

    # TRACKS STOCK METRICS INSTEAD OF SINGLE INSTANCES
    quantity = Column(Integer, default=1, nullable=False,
                      comment="Total baseline rooms operational under this type classification")

    # Relational Back-reference
    hotel = relationship("Hotels", back_populates="rooms")
