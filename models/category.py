import enum
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Define a clean enum for system configuration status mapping
class CategoryStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class Categories(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Upgraded status tracking using database enums
    status = Column(
        Enum(CategoryStatusEnum),
        default=CategoryStatusEnum.active,
        server_default=CategoryStatusEnum.active.value,
        nullable=False
    )

    # System-level automatic timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relational Back-references
    places = relationship("Places", back_populates="category")
    hotels = relationship("Hotels", back_populates="category")
    restaurants = relationship("Restaurants", back_populates="category")

    # 🏛️ Pass "Users" as a string instead of a direct class object
    creator = relationship("Users", foreign_keys="[Categories.creator_id]", back_populates="created_categories")

