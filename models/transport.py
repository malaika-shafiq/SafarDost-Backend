import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# Explicit enum matching the "Availability" and "Delete/deactivate" principles in your SRS
class TransportStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Transports(Base):
    __tablename__ = "transports"

    id = Column(Integer, primary_key=True, index=True)
    transport_type = Column(String, nullable=False,
                            comment="e.g., Private AC Saloon Coaster, Grand Cabin, 4x4 Jeep Prado")
    from_location = Column(String, nullable=False, comment="Starting destination / Origin point")
    to_location = Column(String, nullable=False, comment="Target final arrival location point")

    # Timeline Parameters (Departure & Arrival)
    departure_time = Column(String, nullable=False, comment="Scheduled departure details / timing rule")
    arrival_time = Column(String, nullable=False, comment="Scheduled approximate arrival details / timing rule")

    # Capacity & Pricing Constraints
    price = Column(Float, nullable=False, comment="Fare price value mapping string")
    capacity = Column(Integer, nullable=False, comment="Total passenger seating capacity limits")

    # Upgraded lifecycle control availability state
    status = Column(
        Enum(TransportStatusEnum),
        default=TransportStatusEnum.active,
        server_default=TransportStatusEnum.active.value,
        nullable=False
    )

    # Life-Cycle Server Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 🏛️ MASTER ACCOUNTABILITY AUDIT TRAILS
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # String-based relationship hook to bypass Python's circular loading loop traps
    creator = relationship("Users", foreign_keys="[Transports.creator_id]")

    # 🪝 MASTER LOCATIONS COUPLING LINKAGE (Links to the primary destination hub node if needed)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="transports")

    bookings = relationship("TransportBookings", back_populates="transport", cascade="all, delete-orphan")
