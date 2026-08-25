from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from database import Base


class Categories(Base):
    __tablename__ = "categories"

    # 1. Structural Identifiers
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)  # Optional descriptive field

    # 2. Audit Trails (Requested by Supervisor)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # 3. Soft Delete Configuration (Requested by Supervisor)
    status = Column(String, default="y", server_default="y")

# 🔗 Bidirectional Relationships (Back-references)
    places = relationship("Places", back_populates="category")
    hotels = relationship("Hotels", back_populates="category")
    restaurants = relationship("Restaurants", back_populates="category")