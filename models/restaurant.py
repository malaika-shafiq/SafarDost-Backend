from database import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship


class Restaurants(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)
    price_range = Column(String)  # e.g., "Budget", "Luxury"
    rating = Column(Float, default=0.0)
    image = Column(String)

    # Relational link: Connects a restaurant to its incoming reviews
    reviews = relationship("Reviews", back_populates="restaurant")

    bookings = relationship("RestaurantBookings", back_populates="restaurant")

    # 🪝 Foreign Key Constraint Link
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    # 🔗 Relationship mapping to fetch parent category details
    category = relationship("Categories", back_populates="restaurants")