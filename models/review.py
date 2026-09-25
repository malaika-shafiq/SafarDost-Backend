import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class ReviewStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Reviews(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer, nullable=False, comment="Star rating grading metrics from 1 to 5")
    comment = Column(Text, nullable=False, comment="Travel text review commentary content or shared experience description")

    status = Column(
        Enum(ReviewStatusEnum),
        default=ReviewStatusEnum.active,
        server_default=ReviewStatusEnum.active.value,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("Users", foreign_keys=[user_id], back_populates="reviews")

    # 🔗 POLYMORPHIC REGISTRY EXPANDED FOR VEHICLE FLEETS:
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=True)
    transport_id = Column(Integer, ForeignKey("transports.id", ondelete="CASCADE"), nullable=True)  # 👈 NEW COLUMN BINDING

    # Back-reference relationship mappings to target entities
    place = relationship("Places", back_populates="reviews")
    hotel = relationship("Hotels", back_populates="reviews")
    restaurant = relationship("Restaurants", back_populates="reviews")
    transport = relationship("Transports", back_populates="reviews")  # 👈 NEW RELATIONSHIP TRACKER
