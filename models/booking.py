import enum
from database import Base
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# --- ENUM CONVENTIONS MATCHING WORKSPACE DESIGN (Section 9, 14 & 15 Planning) ---
class BookingTypeEnum(str, enum.Enum):
    hotel = "hotel"
    restaurant = "restaurant"
    transport = "transport"
    tour = "tour"


class BookingStatusEnum(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    rejected = "rejected"


class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


# =====================================================================
# 🏛️ 1. CENTRAL MASTER BOOKING BASE TABLE (Section 9 Planning)
# =====================================================================
class Bookings(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    booking_type = Column(Enum(BookingTypeEnum), nullable=False)

    # 👤 OPTION B: Booking-specific contacts for family/friends (Section 13)
    contact_name = Column(String, nullable=False)
    contact_phone = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)

    # 💳 NATIONAL IDENTITY RECORD VERIFICATION FIELD (Image Requirements Check)
    # Placeholder token string format handled dynamically: [Aadhaar Redacted] or custom numeric formatting rules applied safely.
    cnic_number = Column(String, nullable=False, comment="Primary Traveler National Identity Verification String")

    # Financials & Status Parameters (Section 9)
    total_amount = Column(Float, nullable=False, default=0.0)
    booking_status = Column(Enum(BookingStatusEnum), default=BookingStatusEnum.pending, nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.pending, nullable=False)
    special_requests = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Core Relational Bridges
    user = relationship("Users", back_populates="bookings")

    # Child extensions (Cascades deletions cleanly if parent records are wiped)
    hotel_details = relationship("HotelBookings", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    restaurant_details = relationship("RestaurantBookings", back_populates="booking", uselist=False,
                                      cascade="all, delete-orphan")
    transport_details = relationship("TransportBookings", back_populates="booking", uselist=False,
                                     cascade="all, delete-orphan")
    tour_details = relationship("TourBookings", back_populates="booking", uselist=False, cascade="all, delete-orphan")


# =====================================================================
# 🏨 2. HOTEL BOOKING CHILD TABLE (Section 10 Planning)
# =====================================================================
class HotelBookings(Base):
    __tablename__ = "hotel_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("hotel_rooms.id", ondelete="CASCADE"), nullable=False)

    # Timeline bounds (Section 2.B)
    check_in = Column(DateTime(timezone=True), nullable=False)
    check_out = Column(DateTime(timezone=True), nullable=False)
    number_of_rooms = Column(Integer, default=1, nullable=False)

    # Guest distributions (Section 2.C)
    adults = Column(Integer, default=1, nullable=False)
    children = Column(Integer, default=0, nullable=False)
    child_ages = Column(String, nullable=True, comment="Comma separated format, e.g. '5, 9'")

    # Relational Bridges
    booking = relationship("Bookings", back_populates="hotel_details")
    hotel = relationship("Hotels", back_populates="bookings")
    room = relationship("HotelRooms")


# =====================================================================
# 🍽️ 3. RESTAURANT BOOKING CHILD TABLE (Section 11 Planning)
# =====================================================================
class RestaurantBookings(Base):
    __tablename__ = "restaurant_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)

    reservation_date = Column(DateTime(timezone=True), nullable=False)
    reservation_time = Column(String, nullable=False, comment="e.g. '08:00 PM'")

    adults = Column(Integer, default=1, nullable=False)
    children = Column(Integer, default=0, nullable=False)
    seating_preference = Column(String, nullable=True, comment="Indoor, Outdoor, or No preference")

    # Relational Bridges
    booking = relationship("Bookings", back_populates="restaurant_details")
    restaurant = relationship("Restaurants", back_populates="bookings")


# ==========================================
# 🚌 4. TRANSPORT BOOKING CHILD TABLE (Section 12 Planning)
# ==========================================
class TransportBookings(Base):
    __tablename__ = "transport_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    transport_id = Column(Integer, ForeignKey("transports.id", ondelete="CASCADE"), nullable=False)

    from_location = Column(String, nullable=False)
    to_location = Column(String, nullable=False)
    departure_date = Column(DateTime(timezone=True), nullable=False)
    departure_time = Column(String, nullable=False)

    adults = Column(Integer, default=1, nullable=False)
    children = Column(Integer, default=0, nullable=False)
    pickup_location = Column(String, nullable=True)
    dropoff_location = Column(String, nullable=True)

    # Relational Bridges
    booking = relationship("Bookings", back_populates="transport_details")
    transport = relationship("Transports", back_populates="bookings")


# =====================================================================
# 🗺️ 5. TOUR BOOKING CHILD TABLE (Section 16 Planning)
# =====================================================================
class TourBookings(Base):
    __tablename__ = "tour_bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    package_id = Column(Integer, ForeignKey("tour_packages.id", ondelete="CASCADE"), nullable=False)

    # Capacity distributions matching package limits
    number_of_travelers = Column(Integer, default=1, nullable=False)
    adults = Column(Integer, default=1, nullable=False)
    children = Column(Integer, default=0, nullable=False)

    # Relational Bridges
    booking = relationship("Bookings", back_populates="tour_details")
    package = relationship("TourPackages", back_populates="bookings")
