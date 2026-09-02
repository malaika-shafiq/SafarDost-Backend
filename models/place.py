import enum

from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Define a clean enum for the tourist place lifecycle states
class PlaceStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class Places(Base):
    __tablename__ = "places"

    # 1. Core Primary Keys & Structural Text Fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)

    # 2. 📍 MAP ROUTER COUPLING (Precise Coordinates for dropping Google Maps pins)
    latitude = Column(Float, nullable=False, comment="Extracted map anchor latitude decimal coordinate")
    longitude = Column(Float, nullable=False, comment="Extracted map anchor longitude decimal coordinate")
    physical_address = Column(String, nullable=True,
                              comment="Physical street landmarks or area directions text description")

    # 3. 🏠 SRS DOCUMENTATION METADATA ARTIFACT FIELDS
    entry_information = Column(Text, nullable=True, default="Open to the public")  # e.g. Passports/Tickets info
    recommended_visiting_information = Column(Text, nullable=True)  # e.g. "Best time to visit: May to October"
    travel_tips = Column(Text, nullable=True)  # e.g. "No ATMs nearby, carry local cash"

    status = Column(
        Enum(PlaceStatusEnum),
        default=PlaceStatusEnum.active,
        server_default=PlaceStatusEnum.active.value,
        nullable=False
    )

    # 4. 🕒 SERVER-SIDE LIFE-CYCLE TIMESTAMPS
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 5. 🏛️ MASTER AUDIT TRAILS (Tracks exactly which admin creates or updates a destination spot)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 🏛️ Pass "Users" as a string here too
    creator = relationship("Users", foreign_keys="[Places.creator_id]", back_populates="created_places")

    # 6. 🪝 MASTER LOCATIONS VALLEYS COUPLING (Foreign Key replacing old string)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="places")

    # 7. 🪝 DYNAMIC TAXONOMY CATEGORY BINDINGS
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    category = relationship("Categories", back_populates="places")

    # 8. 💬 TRAVELER REVIEW MODULE HOOKS
    reviews = relationship("Reviews", back_populates="place")
