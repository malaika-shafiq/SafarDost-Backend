import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# Explicit enum tracking the operational status of published tour packages
class PackageStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


# 🌉 ASSOCIATION BRIDGE TABLE: Links a single Tour Package to multiple Attractions (Places)
package_places_association = Table(
    "package_places",
    Base.metadata,
    Column("package_id", Integer, ForeignKey("tour_packages.id", ondelete="CASCADE"), primary_key=True),
    Column("place_id", Integer, ForeignKey("places.id", ondelete="CASCADE"), primary_key=True)
)

# 🌉 ASSOCIATION BRIDGE TABLE: Links a single Tour Package to multiple Contracted Hotels
package_hotels_association = Table(
    "package_hotels",
    Base.metadata,
    Column("package_id", Integer, ForeignKey("tour_packages.id", ondelete="CASCADE"), primary_key=True),
    Column("hotel_id", Integer, ForeignKey("hotels.id", ondelete="CASCADE"), primary_key=True)
)


class TourPackages(Base):
    __tablename__ = "tour_packages"

    # Core Identifiers (Image 2 & 3 Requirements)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, comment="Package Name")
    description = Column(Text, nullable=False, comment="Detailed package description overview")
    duration = Column(String, nullable=False, comment="Duration format, e.g., '5 Days / 4 Nights'")
    price = Column(Float, nullable=False, comment="Base tour price per traveler head")

    # 🗓️ SEATS CAPACITY & TIMELINE SCHEDULING (Image 2 & 3 Requirements)
    available_slots = Column(Integer, nullable=False, default=10, comment="Available seats/slots left for booking")
    start_date = Column(DateTime(timezone=True), nullable=False, comment="Tour group departure start date")
    end_date = Column(DateTime(timezone=True), nullable=False, comment="Tour group returns end date")

    # 📝 METADATA SPECIFICATION ARTIFACT FIELDS (Image 2 & 4 Requirements)
    activities = Column(Text, nullable=True, comment="Detailed text layout tracking planned itinerary events")
    transportation_information = Column(Text, nullable=True,
                                        comment="Included transport details, e.g., Private AC Coaster")
    included_services = Column(Text, nullable=True, comment="e.g., Tour Guide, Photography, Entry Tickets")

    # Lifecycle structural control state
    status = Column(
        Enum(PackageStatusEnum),
        default=PackageStatusEnum.active,
        server_default=PackageStatusEnum.active.value,
        nullable=False
    )

    # Automated life-cycle server timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 🏛️ SYSTEM ACCOUNTABILITY AUDIT TRAILS (Supervisor's Core Requirement)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # String-based relationship hook to bypass Python's circular loading loop traps
    creator = relationship("Users", foreign_keys="[TourPackages.creator_id]")

    # 🪝 GEOGRAPHIC LOCATION COUPLING LINKAGE (Image 1 & 2: Destination requirement)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    location = relationship("Locations", back_populates="tour_packages")

    # 🔗 MULTI-ENTITY MANY-TO-MANY RELATIONSHIPS (Image 3: Essential for AI tracking keys)
    # The 'secondary' parameter handles the linking ledger operations behind the scenes automatically!
    places = relationship("Places", secondary=package_places_association, backref="tour_packages")
    hotels = relationship("Hotels", secondary=package_hotels_association, backref="tour_packages")
