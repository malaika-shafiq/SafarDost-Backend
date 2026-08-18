from database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship


class Hotels(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    price_per_night = Column(Integer)  # Stored nightly rate in PKR
    rating = Column(Float, default=0.0)
    image = Column(String)  # Cloudinary image link
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


    # Relational link: Connects a hotel to its incoming reviews
    reviews = relationship("Reviews", back_populates="hotel")

    creator = relationship("Users", back_populates="created_hotels")

    # Add this line at the bottom of your Hotels class
    bookings = relationship("HotelBookings", back_populates="hotel")
