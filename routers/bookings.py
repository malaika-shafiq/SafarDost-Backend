import math
from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from database import get_db

# Model and Schema Cross-Imports
from models.booking import Bookings, HotelBookings, RestaurantBookings, TransportBookings, TourBookings
from models.booking import BookingTypeEnum, BookingStatusEnum, PaymentStatusEnum
from models.hotel import Hotels, HotelRooms
from models.restaurant import Restaurants
from models.transport import Transports, TransportStatusEnum
from models.tour_package import TourPackages, PackageStatusEnum
from schemas.booking_schemas import BookingCreate, BookingResponse
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/bookings", tags=["Polymorphic Booking & Checkout System"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("", status_code=status.HTTP_200_OK)
def get_all_bookings_paginated(
        db: db_dependency,
        current_user: user_dependency,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        limit: int = Query(10, ge=1, le=50, description="Items per page"),
        booking_type: Optional[BookingTypeEnum] = Query(None, description="Filter by booking type context"),
        booking_status: Optional[BookingStatusEnum] = Query(None, description="Filter by transaction status")
):
    """Dual-Role Pagination Fetch: Admin sees everything, travelers see their own history."""
    query = db.query(Bookings).options(
        joinedload(Bookings.hotel_details),
        joinedload(Bookings.restaurant_details),
        joinedload(Bookings.transport_details),
        joinedload(Bookings.tour_details)
    )

    if current_user.get("role") != "admin":
        query = query.filter(Bookings.user_id == current_user.get("id"))

    if booking_type:
        query = query.filter(Bookings.booking_type == booking_type)
    if booking_status:
        query = query.filter(Bookings.booking_status == booking_status)

    query = query.order_by(desc(Bookings.created_at))
    total_items = query.count()

    offset = (page - 1) * limit
    bookings_list = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 0

    return {
        "items": bookings_list,
        "total": total_items,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    }


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_transaction_booking(
        booking_request: BookingCreate,
        current_user: user_dependency,
        db: db_dependency
):
    """ Dynamic polymorphic checkout interface with strict inventory stock checks. """
    db_master = Bookings(
        user_id=current_user.get("id"),
        booking_type=booking_request.booking_type,
        contact_name=booking_request.contact_name.strip(),
        contact_phone=booking_request.contact_phone.strip(),
        contact_email=booking_request.contact_email.strip(),
        cnic_number=booking_request.cnic_number.strip(),
        special_requests=booking_request.special_requests,
        booking_status=BookingStatusEnum.pending,
        payment_status=PaymentStatusEnum.pending,
        total_amount=0.0
    )
    db.add(db_master)
    db.flush()

    # ==========================================
    # A. SUB-ROUTING WORKFLOW: HOTEL INVENTORY QUANTITY CHECK
    # ==========================================
    if booking_request.booking_type == BookingTypeEnum.hotel:
        details = booking_request.hotel_details
        if not details:
            raise HTTPException(status_code=400, detail="Missing required 'hotel_details' payload block.")

        # 🔒 PESSIMISTIC LOCK APPLIED: Protects room targets against multi-user race conditions natively
        target_room = db.query(HotelRooms).filter(
            HotelRooms.id == details.room_id,
            HotelRooms.hotel_id == details.hotel_id
        ).with_for_update().first()

        if not target_room:
            raise HTTPException(status_code=404, detail="The requested room type classification was not found.")

        # 📅 OVERLAPPING OCCUPANCY ALGORITHM
        booked_rooms_sum = db.query(func.sum(HotelBookings.number_of_rooms)).join(Bookings).filter(
            HotelBookings.room_id == details.room_id,
            Bookings.booking_status == BookingStatusEnum.confirmed,
            HotelBookings.check_out > details.check_in,
            HotelBookings.check_in < details.check_out
        ).scalar() or 0

        if (booked_rooms_sum + details.number_of_rooms) > target_room.quantity:
            rooms_left = max(0, target_room.quantity - booked_rooms_sum)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Inventory Shortage: Only {rooms_left} units of '{target_room.room_type}' left for these dates."
            )

        nights = (details.check_out - details.check_in).days
        if nights <= 0:
            raise HTTPException(status_code=400, detail="Invalid date matrix setup: Check-out must exceed Check-in.")

        db_master.total_amount = target_room.price_per_night * nights * details.number_of_rooms

        db_child = HotelBookings(
            booking_id=db_master.id,
            hotel_id=details.hotel_id,
            room_id=details.room_id,
            check_in=details.check_in,
            check_out=details.check_out,
            number_of_rooms=details.number_of_rooms,
            adults=details.adults,
            children=details.children,
            child_ages=details.child_ages
        )
        db.add(db_child)

    # ==========================================
    # B. RESTAURANT BRANCH
    # ==========================================
    elif booking_request.booking_type == BookingTypeEnum.restaurant:
        details = booking_request.restaurant_details
        if not details:
            raise HTTPException(status_code=400, detail="Missing required 'restaurant_details' payload block.")

        db_master.total_amount = 0.0
        db_child = RestaurantBookings(
            booking_id=db_master.id,
            restaurant_id=details.restaurant_id,
            reservation_date=details.reservation_date,
            reservation_time=details.reservation_time.strip(),
            adults=details.adults,
            children=details.children,
            seating_preference=details.seating_preference
        )
        db.add(db_child)

    # ==========================================
    # C. TRANSPORT BRANCH
    # ==========================================
    elif booking_request.booking_type == BookingTypeEnum.transport:
        details = booking_request.transport_details
        if not details:
            raise HTTPException(status_code=400, detail="Missing required 'transport_details' payload block.")

        vehicle = db.query(Transports).filter(Transports.id == details.transport_id,
                                              Transports.status == TransportStatusEnum.active).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="Target vehicle profile is offline.")

        if vehicle.capacity < (details.adults + details.children):
            raise HTTPException(status_code=400, detail="Seating Capacity Overflow.")

        db_master.total_amount = vehicle.price
        db_child = TransportBookings(
            booking_id=db_master.id,
            transport_id=details.transport_id,
            from_location=details.from_location.strip(),
            to_location=details.to_location.strip(),
            departure_date=details.departure_date,
            departure_time=details.departure_time.strip(),
            adults=details.adults,
            children=details.children,
            pickup_location=details.pickup_location,
            dropoff_location=details.dropoff_location
        )
        db.add(db_child)

    # ==========================================
    # D. TOUR BUNDLE BRANCH
    # ==========================================
    elif booking_request.booking_type == BookingTypeEnum.tour:
        details = booking_request.tour_details
        if not details:
            raise HTTPException(status_code=400, detail="Missing required 'tour_details' payload block.")

        # 🔒 PESSIMISTIC LOCK APPLIED: Protects package seats from concurrent race conditions
        package = db.query(TourPackages).filter(
            TourPackages.id == details.package_id,
            TourPackages.status == PackageStatusEnum.active
        ).with_for_update().first()

        if not package:
            raise HTTPException(status_code=400, detail="Target tour package is offline.")

        if package.available_slots < details.number_of_travelers:
            raise HTTPException(status_code=400, detail="Insufficient seats left.")

        package.available_slots -= details.number_of_travelers
        db_master.total_amount = package.price * details.number_of_travelers

        db_child = TourBookings(
            booking_id=db_master.id,
            package_id=details.package_id,
            number_of_travelers=details.number_of_travelers,
            adults=details.adults,
            children=details.children
        )
        db.add(db_child)
        db.add(package)

    db.commit()
    db.refresh(db_master)
    return db_master


# ==========================================
# 3. READ A SINGLE BOOKING PROFILE DETAILS
# ==========================================
@router.get("/{booking_id}", response_model=BookingResponse, status_code=status.HTTP_200_OK)
def get_individual_booking_by_id(
        booking_id: int,
        current_user: user_dependency,
        db: db_dependency
):
    """ Single Ledger Profile View. Enforces absolute user access security boundaries. """
    # ❌ READ-ONLY PATH: Intentionally excludes pessimistic locking to preserve low latency traffic streams
    booking = db.query(Bookings).options(
        joinedload(Bookings.hotel_details),
        joinedload(Bookings.restaurant_details),
        joinedload(Bookings.transport_details),
        joinedload(Bookings.tour_details)
    ).filter(Bookings.id == booking_id).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Target transaction booking record not found.")

    if current_user.get("role") != "admin" and booking.user_id != current_user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security Violation: Insufficient account permissions to view this transaction ledger."
        )

    return booking


# ==========================================
# 4. MODERATE STATUS APPROVALS/REJECTIONS (🔒 Admin Only)
# ==========================================
@router.patch("/{booking_id}/status", response_model=BookingResponse, status_code=status.HTTP_200_OK)
def moderate_booking_status_override(
        booking_id: int,
        new_status: BookingStatusEnum,
        new_payment: PaymentStatusEnum,
        current_user: user_dependency,
        db: db_dependency
):
    """
    ADMIN ONLY: Overrides system transaction states.
    Automatically refunds seat slot allocations to tour packages upon cancellation/rejection.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges are required to override system transaction states."
        )

    booking = db.query(Bookings).filter(Bookings.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Target transaction booking record not found.")

    # 🚨 INVENTORY REFUND ENGINE
    if new_status in [BookingStatusEnum.rejected,
                      BookingStatusEnum.cancelled] and booking.booking_status == BookingStatusEnum.pending:

        # Scenario A: Refund group tour package seat assignments instantly
        if booking.booking_type == BookingTypeEnum.tour and booking.tour_details:
            package = db.query(TourPackages).filter(
                TourPackages.id == booking.tour_details.package_id).with_for_update().first()
            if package:
                package.available_slots += booking.tour_details.number_of_travelers
                db.add(package)

    booking.booking_status = new_status
    booking.payment_status = new_payment

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


# ==========================================
# 5. REMOVE / PURGE A RECORD LEDGER (🔒 Admin Only)
# ==========================================
@router.delete("/{booking_id}", status_code=status.HTTP_200_OK)
def delete_historical_booking_record(
        booking_id: int,
        current_user: user_dependency,
        db: db_dependency
):
    """ ADMIN ONLY: Hard purge operation. Wipes transactional rows from disk. """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to delete historical data rows from memory."
        )

    booking = db.query(Bookings).filter(Bookings.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Target tracking reservation code not found.")

    print(f"[SECURITY CHECKOUT AUDIT] Admin ID {current_user.get('id')} has purged booking ID: {booking.id}")

    db.delete(booking)
    db.commit()
    return {"message": f"Success. Reservation ledger block reference ID '{booking_id}' permanently dropped."}


# =====================================================================
# 🔒 SOFT CANCELLATION LIFECYCLE GATEWAY (Polished & Fully Synchronized)
# =====================================================================
@router.patch("/{booking_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_user_travel_booking(
        booking_id: int,
        current_user: user_dependency,
        db: db_dependency
):
    """
    STATE MUTATION GATEWAY: Transitions booking states from active to 'cancelled'.
    Releases slot capacities back into production while fully preserving audit logs.
    """
    # 1. Locate the targeted transaction ledger row
    booking = db.query(Bookings).filter(Bookings.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested booking transaction ledger record could not be found."
        )

    # 2. Enforce absolute security boundaries (Prevent cross-user tempering)
    if booking.user_id != current_user.get("id") and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action denied: You are unauthorized to modify this transaction record."
        )

    # ✅ FIXED FIELD ATTRIBUTE NAME: Unifies perfectly with 'booking_status' parameter schema
    if booking.booking_status == BookingStatusEnum.cancelled:
        return {
            "success": True,
            "message": "This travel reservation asset has already been marked as cancelled."
        }

    # 🚨 DYNAMIC AUTOMATED INVENTORY RELEASE SYSTEM
    # If the booking is a tour package, refund the slots instantly upon cancellation
    if booking.booking_type == BookingTypeEnum.tour and booking.tour_details:
        package = db.query(TourPackages).filter(
            TourPackages.id == booking.tour_details.package_id).with_for_update().first()
        if package:
            package.available_slots += booking.tour_details.number_of_travelers
            db.add(package)

    # Note: Hotel room updates require no manual increment code here,
    # since our query filters release rooms back into the date pool the second booking_status shifts!

    # Execute safe state mutation changes
    booking.booking_status = BookingStatusEnum.cancelled
    booking.payment_status = PaymentStatusEnum.refunded if booking.payment_status == PaymentStatusEnum.paid else PaymentStatusEnum.pending

    db.add(booking)
    db.commit()

    return {
        "success": True,
        "message": "Your travel booking was cancelled successfully. Inventory slots have been automatically updated."
    }
