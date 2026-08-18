import datetime
from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, String
from sqlalchemy.orm import relationship
from database import Base

# --- HOTEL RESERVATION MODEL ---
class HotelBookings(Base):
    __tablename__ = "hotel_bookings"

    id = Column(Integer, primary_key=True, index=True)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    total_price = Column(Integer, nullable=False)  # Automatically calculated rate in PKR
    # Enforces explicit timezone support inside SQLite engine configuration
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Foreign Key tracking references
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)

    # Relational loops back to parent models
    user = relationship("Users", back_populates="bookings")
    hotel = relationship("Hotels", back_populates="bookings")


# --- RESTAURANT RESERVATION MODEL ---
class RestaurantBookings(Base):
    __tablename__ = "restaurant_bookings"

    id = Column(Integer, primary_key=True, index=True)
    reservation_date = Column(Date, nullable=False)
    reservation_time = Column(String, nullable=False) # e.g., "20:30" (8:30 PM PKT)
    number_of_guests = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)

    # Relational loops back to parents
    user = relationship("Users", back_populates="restaurant_bookings")
    restaurant = relationship("Restaurants", back_populates="bookings")


# --- TRANSPORT BOOKING MODEL ---
class TransportBookings(Base):
    __tablename__ = "transport_bookings"

    id = Column(Integer, primary_key=True, index=True)
    transport_type = Column(String, nullable=False) # e.g., "Rent-a-Car", "Bus", "Coaster"
    departure_date = Column(Date, nullable=False)
    source_city = Column(String, nullable=False)     # e.g., "Lahore"
    destination_city = Column(String, nullable=False)# e.g., "Skardu"
    total_price = Column(Integer, nullable=False)     # Flat operational rate in PKR
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relational loop back to parent traveler
    user = relationship("Users", back_populates="transport_bookings")