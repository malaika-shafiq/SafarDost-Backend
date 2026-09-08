import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# Explicit enums matching the required "Availability/status" and "Delete/deactivate" fields in SRS Image 2
class HotelStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class RoomStatusEnum(str, enum.Enum):
    available = "available"
    booked = "booked"
    maintenance = "maintenance"


class Hotels(Base):
    __tablename__ = "hotels"

    # Core Structural Identifiers (Image 2 Requirements)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, comment="Hotel Name")
    description = Column(Text, nullable=False, comment="Detailed property overview description")
    contact_information = Column(String, nullable=False, comment="Phone numbers or booking contact desks")
    facilities = Column(Text, nullable=True,
                        comment="Comma-separated amenities summary tokens, e.g., WiFi, AC, Parking, Heater")

    # Upgraded lifecycle control state
    status = Column(
        Enum(HotelStatusEnum),
        default=HotelStatusEnum.active,
        server_default=HotelStatusEnum.active.value,
        nullable=False
    )

    # Life-Cycle Server Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 🏛️ SYSTEM ACCOUNTABILITY AUDIT TRAILS
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # String-based relationship hook to completely bypass Python's circular loading loop traps
    # Inside models/hotel.py — Ensure your relationship line reads exactly like this:
    creator = relationship("Users", foreign_keys="[Hotels.creator_id]", back_populates="created_hotels")

    # 🪝 MASTER LOCATIONS VALLEYS COUPLING (Image 2: Location requirement)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="hotels")

    # 🗂️ DYNAMIC TAXONOMY CATEGORY BINDING (Hooks up to "Hotels" category)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Categories", back_populates="hotels")

    # 🏛️ BILATERAL ALIGNMENT: Tell Hotels how to back-populate your shared traveler reviews cleanly
    reviews = relationship("Reviews", back_populates="hotel", cascade="all, delete-orphan")

    # Child Table Back-reference Linkage
    rooms = relationship("HotelRooms", back_populates="hotel", cascade="all, delete-orphan")

    # 🏛️ BILATERAL ALIGNMENT: Connects your hotel profile to the bookings registration ledger table
    bookings = relationship("HotelBookings", back_populates="hotel", cascade="all, delete-orphan")


class HotelRooms(Base):
    __tablename__ = "hotel_rooms"

    # Room Specification Information (Image 2 Requirements)
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)

    room_type = Column(String, nullable=False, comment="e.g., Deluxe Suite, Standard Twin, Luxury Family Room")
    description = Column(Text, nullable=True, comment="Specific room layout or landscape view features description")
    price_per_night = Column(Float, nullable=False, comment="Image 2: Price field requirement")
    capacity = Column(Integer, default=2, nullable=False, comment="Maximum guest sleep capacity limits")

    # Image 2: Availability/status field requirement
    status = Column(
        Enum(RoomStatusEnum),
        default=RoomStatusEnum.available,
        server_default=RoomStatusEnum.available.value,
        nullable=False
    )

    # Relational Bridges
    hotel = relationship("Hotels", back_populates="rooms")
