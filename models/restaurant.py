import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Explicit enum matching the "Availability" and "Delete/deactivate" requirements in the SRS
class RestaurantStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Restaurants(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, comment="Restaurant Name")
    description = Column(Text, nullable=False, comment="Description")
    cuisine = Column(String, nullable=False, comment="Cuisine type (e.g., Pakistani, Chinese, Continental)")
    menu_details = Column(Text, nullable=True, comment="Menu/details summary description or text layout")
    price_range = Column(String, nullable=False, comment="Price range mapping (e.g., Low, Medium, High or approximate budget)")
    contact = Column(String, nullable=False, comment="Contact phone numbers or registration desks")
    opening_information = Column(String, nullable=False, comment="Opening information / Opening Hours (e.g., 11:00 AM - 11:00 PM)")
    table_capacity = Column(Integer, nullable=True, comment="Table/Capacity mapping context total seats available")

    # Upgraded lifecycle control state
    status = Column(
        Enum(RestaurantStatusEnum),
        default=RestaurantStatusEnum.active,
        server_default=RestaurantStatusEnum.active.value,
        nullable=False
    )

    # Life-Cycle Server Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 🏛️ SYSTEM ACCOUNTABILITY AUDIT TRAILS
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # String-based relationship hook to completely bypass Python's circular loading loop traps
    creator = relationship("Users", foreign_keys="[Restaurants.creator_id]")

    # 🪝 MASTER LOCATIONS BINDING
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="restaurants")

    # 🗂️ DYNAMIC TAXONOMY CATEGORY BINDING (Hooks up to "Restaurants" metadata nodes)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Categories", back_populates="restaurants")

    # 🏛️ BILATERAL ALIGNMENT: Connects your dining spots to your central reviews table cleanly
    reviews = relationship("Reviews", back_populates="restaurant", cascade="all, delete-orphan")

    # 🏛️ BILATERAL ALIGNMENT: Connects your restaurant profile to your restaurant bookings table cleanly
    bookings = relationship("RestaurantBookings", back_populates="restaurant", cascade="all, delete-orphan")
