from database import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    current_refresh_token = Column(String, nullable=True)
    role = Column(String, default="traveler")  # Track authority levels: "admin" or "traveler"

    # Relational links: Connects a user to their generated application resources
    reviews = relationship("Reviews", back_populates="user")
    created_places = relationship("Places", back_populates="creator")
    created_hotels = relationship("Hotels", back_populates="creator")

    # 🏛️ BILATERAL ALIGNMENT: Perfectly mirrors your booking module relationship definitions
    bookings = relationship("HotelBookings", back_populates="user")
    restaurant_bookings = relationship("RestaurantBookings", back_populates="user")
    transport_bookings = relationship("TransportBookings", back_populates="user")
