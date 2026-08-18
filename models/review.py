from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime

def get_utc_now():
    """
    Standardized UTC Timestamp Helper: Generates precise timezone-naive
    datetime stamps optimized for storage engines like SQLite and PostgreSQL.
    """
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer)  # Star rating score restricted between 1 and 5
    comment = Column(Text)
    image_url = Column(String, nullable=True)  # Optional photo attachment URL
    created_at = Column(DateTime, default=get_utc_now)

    # Foreign Key tracking who wrote the review (Exactly like owner_id in Todos)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Target Foreign Keys linking to what is being reviewed (All are optional/nullable)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)

    # Inverse relationships linking back to parental objects
    user = relationship("Users", back_populates="reviews")
    hotel = relationship("Hotels", back_populates="reviews")
    restaurant = relationship("Restaurants", back_populates="reviews")
    place = relationship("Places", back_populates="reviews")