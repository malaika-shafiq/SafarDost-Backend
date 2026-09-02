import enum
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# 1. Define the enum class right here so the columns below can use it
class UserStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending_verification = "pending verification"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    current_refresh_token = Column(String, nullable=True)
    role = Column(String, default="traveler")  # "admin" or "traveler"

    # New Columns (Non-mandatory / Nullable)
    phone_number = Column(String, nullable=True)
    cnic_number = Column(String, nullable=True)

    # Swap out the string column for a proper database Enum type
    status = Column(
        Enum(UserStatusEnum),
        default=UserStatusEnum.active,
        server_default=UserStatusEnum.active.value,
        nullable=False
    )

    # 🕒 NEW TIMESTAMPS ADDED HERE
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relational links: Connects a user to their generated application resources
    reviews = relationship("Reviews", back_populates="user")

    # 🏛️ Use explicit string definitions to prevent circular imports
    created_places = relationship("Places", foreign_keys="Places.creator_id", back_populates="creator")
    created_categories = relationship("Categories", foreign_keys="Categories.creator_id", back_populates="creator")

    # Left aside for future alignment modifications
    created_hotels = relationship("Hotels", back_populates="creator")

    # 🏛️ BILATERAL ALIGNMENT: Perfectly mirrors your booking module relationship definitions
    bookings = relationship("HotelBookings", back_populates="user")
    restaurant_bookings = relationship("RestaurantBookings", back_populates="user")
    transport_bookings = relationship("TransportBookings", back_populates="user")
