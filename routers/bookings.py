from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from datetime import date
from sqlalchemy.orm import Session
from database import get_db
from models import Hotels, Restaurants
from models.booking import HotelBookings, TransportBookings, RestaurantBookings
from schemas import booking_schemas
from utils.auth_utils import get_current_user
from utils.mail_utils import send_vendor_booking_email, send_restaurant_booking_email, send_transport_booking_email


router = APIRouter(prefix="/hotels/book", tags=["Hotel Bookings"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ==============================================================================
# HOTEL RESERVATIONS SECTION
# ==============================================================================

@router.post("/hotel", response_model=booking_schemas.HotelBookingResponse, status_code=status.HTTP_201_CREATED)
def reserve_hotel_room(booking_request: booking_schemas.HotelBookingCreate, db: db_dependency, current_user: user_dependency):
    """
    Creates a brand new hotel accommodation reservation in Pakistan and triggers an automated notification email.
    """
    if booking_request.check_in_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a reservation for a date that has already passed."
        )

    if booking_request.check_out_date <= booking_request.check_in_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The check-out date must occur after your selected check-in date."
        )

    target_hotel = db.query(Hotels).filter(Hotels.id == booking_request.hotel_id).first()
    if not target_hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel record item not found for ID: {booking_request.hotel_id}"
        )

    delta_days = (booking_request.check_out_date - booking_request.check_in_date).days
    calculated_cost = delta_days * target_hotel.price_per_night

    db_booking = HotelBookings(
        **booking_request.model_dump(),
        user_id=current_user.get("id"),
        total_price=calculated_cost
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    send_vendor_booking_email(
        booking_id=db_booking.id,
        hotel_name=target_hotel.name,
        location=target_hotel.location,
        check_in=db_booking.check_in_date,
        check_out=db_booking.check_out_date,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.get("/hotel/history", response_model=List[booking_schemas.HotelBookingResponse], status_code=status.HTTP_200_OK)
def get_user_hotel_booking_history(db: db_dependency, current_user: user_dependency):
    """
    Retrieves the entire chronological hotel reservation log for the logged-in traveler account.
    """
    bookings = db.query(HotelBookings).filter(HotelBookings.user_id == current_user.get("id")).all()
    return bookings


@router.put("/hotel/{booking_id}", response_model=booking_schemas.HotelBookingResponse, status_code=status.HTTP_200_OK)
def update_hotel_reservation(booking_id: int, booking_request: booking_schemas.HotelBookingUpdate, db: db_dependency, current_user: user_dependency):
    """
    Dynamically modifies an existing hotel reservation's dates and updates financial totals in PKR.
    """
    db_booking = db.query(HotelBookings).filter(HotelBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Hotel reservation record not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    incoming_data = booking_request.model_dump(exclude_unset=True)

    final_check_in = incoming_data.get("check_in_date", db_booking.check_in_date)
    final_check_out = incoming_data.get("check_out_date", db_booking.check_out_date)

    if "check_in_date" in incoming_data and final_check_in < date.today():
        raise HTTPException(status_code=400, detail="Cannot update reservation to a past date.")

    if final_check_out <= final_check_in:
        raise HTTPException(status_code=400, detail="Check-out date must occur after check-in.")

    for key, value in incoming_data.items():
        setattr(db_booking, key, value)

    target_hotel = db.query(Hotels).filter(Hotels.id == db_booking.hotel_id).first()
    new_delta_days = (final_check_out - final_check_in).days
    db_booking.total_price = new_delta_days * target_hotel.price_per_night

    db.commit()
    db.refresh(db_booking)

    send_vendor_booking_email(
        booking_id=db_booking.id,
        hotel_name=target_hotel.name,
        location=target_hotel.location,
        check_in=db_booking.check_in_date,
        check_out=db_booking.check_out_date,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.delete("/hotel/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_hotel_reservation(booking_id: int, db: db_dependency, current_user: user_dependency):
    """
    Permanently cancels and removes a hotel reservation record from the database.
    """
    db_booking = db.query(HotelBookings).filter(HotelBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Hotel reservation record not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    db.delete(db_booking)
    db.commit()



# ==============================================================================
# RESTAURANT RESERVATIONS SECTION
# ==============================================================================

@router.post("/restaurant", response_model=booking_schemas.RestaurantBookingResponse,
             status_code=status.HTTP_201_CREATED)
def reserve_restaurant_table(booking_request: booking_schemas.RestaurantBookingCreate, db: db_dependency,
                             current_user: user_dependency):
    """
    Books a table at a local Pakistani restaurant and fires an automated vendor email alert.
    """
    if booking_request.reservation_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot book a table for a date that has already passed.")

    target_restaurant = db.query(Restaurants).filter(Restaurants.id == booking_request.restaurant_id).first()
    if not target_restaurant:
        raise HTTPException(status_code=404,
                            detail=f"Restaurant records not found for ID: {booking_request.restaurant_id}")

    db_booking = RestaurantBookings(
        **booking_request.model_dump(),
        user_id=current_user.get("id")
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    send_restaurant_booking_email(
        booking_id=db_booking.id,
        restaurant_name=target_restaurant.name,
        location=target_restaurant.location,
        res_date=db_booking.reservation_date,
        res_time=db_booking.reservation_time,
        guests=db_booking.number_of_guests,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.get("/restaurant/history", response_model=List[booking_schemas.RestaurantBookingResponse],
            status_code=status.HTTP_200_OK)
def get_user_restaurant_booking_history(db: db_dependency, current_user: user_dependency):
    """
    Retrieves the entire dining reservation log for the logged-in traveler account.
    """
    bookings = db.query(RestaurantBookings).filter(RestaurantBookings.user_id == current_user.get("id")).all()
    return bookings


@router.put("/restaurant/{booking_id}", response_model=booking_schemas.RestaurantBookingResponse,
            status_code=status.HTTP_200_OK)
def update_restaurant_table_reservation(booking_id: int, booking_request: booking_schemas.RestaurantBookingUpdate,
                                        db: db_dependency, current_user: user_dependency):
    """
    Modifies dining numbers or arrival timings for an active table booking row.
    """
    db_booking = db.query(RestaurantBookings).filter(RestaurantBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Dining reservation record item not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    incoming_data = booking_request.model_dump(exclude_unset=True)

    if "reservation_date" in incoming_data and incoming_data.get("reservation_date") < date.today():
        raise HTTPException(status_code=400, detail="Cannot shift dining entries into historical timelines.")

    for key, value in incoming_data.items():
        setattr(db_booking, key, value)

    db.commit()
    db.refresh(db_booking)

    target_restaurant = db.query(Restaurants).filter(Restaurants.id == db_booking.restaurant_id).first()
    send_restaurant_booking_email(
        booking_id=db_booking.id,
        restaurant_name=target_restaurant.name,
        location=target_restaurant.location,
        res_date=db_booking.reservation_date,
        res_time=db_booking.reservation_time,
        guests=db_booking.number_of_guests,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.delete("/restaurant/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_restaurant_reservation(booking_id: int, db: db_dependency, current_user: user_dependency):
    """
    Permanently deletes a restaurant table booking from database cache layer.
    """
    db_booking = db.query(RestaurantBookings).filter(RestaurantBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Dining reservation record item not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    db.delete(db_booking)
    db.commit()


# ==============================================================================
# TRANSPORT RESERVATIONS SECTION
# ==============================================================================

@router.post("/transport", response_model=booking_schemas.TransportBookingResponse, status_code=status.HTTP_201_CREATED)
def book_travel_transport(booking_request: booking_schemas.TransportBookingCreate, db: db_dependency,
                          current_user: user_dependency):
    """
    Books vehicles or local coaster transport across Pakistan and fires an automated vendor email alert.
    """
    if booking_request.departure_date < date.today():
        raise HTTPException(status_code=400, detail="Departure travel date cannot match historical timelines.")

    db_booking = TransportBookings(
        **booking_request.model_dump(),
        user_id=current_user.get("id")
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    send_transport_booking_email(
        booking_id=db_booking.id,
        transport_type=db_booking.transport_type,
        departure=db_booking.departure_date,
        source=db_booking.source_city,
        destination=db_booking.destination_city,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.get("/transport/history", response_model=List[booking_schemas.TransportBookingResponse],
            status_code=status.HTTP_200_OK)
def get_user_transport_booking_history(db: db_dependency, current_user: user_dependency):
    """
    Retrieves the entire vehicle transport routing historical log for the traveler.
    """
    bookings = db.query(TransportBookings).filter(TransportBookings.user_id == current_user.get("id")).all()
    return bookings


@router.put("/transport/{booking_id}", response_model=booking_schemas.TransportBookingResponse,
            status_code=status.HTTP_200_OK)
def update_transit_logistics_reservation(booking_id: int, booking_request: booking_schemas.TransportBookingUpdate,
                                         db: db_dependency, current_user: user_dependency):
    """
    Modifies travel parameters or routes dynamically for an active fleet tracking row.
    """
    db_booking = db.query(TransportBookings).filter(TransportBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Transit logistics reservation record item not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    incoming_data = booking_request.model_dump(exclude_unset=True)

    if "departure_date" in incoming_data and incoming_data.get("departure_date") < date.today():
        raise HTTPException(status_code=400, detail="Cannot alter departure schedules into historical timelines.")

    for key, value in incoming_data.items():
        setattr(db_booking, key, value)

    db.commit()
    db.refresh(db_booking)

    send_transport_booking_email(
        booking_id=db_booking.id,
        transport_type=db_booking.transport_type,
        departure=db_booking.departure_date,
        source=db_booking.source_city,
        destination=db_booking.destination_city,
        total_price=db_booking.total_price,
        customer_email=current_user.get("email")
    )

    return db_booking


@router.delete("/transport/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_transport_booking(booking_id: int, db: db_dependency, current_user: user_dependency):
    """
    Permanently cancels a transport booking and drops it from the database log.
    """
    db_booking = db.query(TransportBookings).filter(TransportBookings.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Transit logistics reservation record item not found.")

    if db_booking.user_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Adequate reservation ownership parameters missing.")

    db.delete(db_booking)
    db.commit()