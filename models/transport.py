import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class TransportStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class TransportRentalModeEnum(str, enum.Enum):
    private_dedicated = "private_dedicated"  # Entire vehicle hire (Car, Jeep, Prado)
    public_shared = "public_shared"  # Seat-by-seat ticket system (Bus, Coaster)


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
    price = Column(Float, nullable=False, comment="Private vehicle price OR individual seat ticket price value")
    capacity = Column(Integer, nullable=False, comment="Total passenger seating capacity limits")

    rental_mode = Column(
        Enum(TransportRentalModeEnum),
        default=TransportRentalModeEnum.private_dedicated,
        server_default=TransportRentalModeEnum.private_dedicated.value,
        nullable=False,
        comment="Specifies whether the booking is per vehicle or per seat"
    )
    available_seats = Column(
        Integer,
        nullable=False,
        comment="Tracks active available seat counts for public shared routes"
    )

    status = Column(
        Enum(TransportStatusEnum),
        default=TransportStatusEnum.active,
        server_default=TransportStatusEnum.active.value,
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("Users", foreign_keys="[Transports.creator_id]")

    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="transports")

    bookings = relationship("TransportBookings", back_populates="transport", cascade="all, delete-orphan")

    # =====================================================================
    # 🪝 THE CHOSEN RELATIONSHIP INTEGRATION LINK HOOK:
    # =====================================================================
    # This connects the model directly to your core reviews module table rows natively!
    reviews = relationship("Reviews", back_populates="transport", cascade="all, delete-orphan")
