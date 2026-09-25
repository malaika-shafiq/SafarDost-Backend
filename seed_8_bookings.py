from database import SessionLocal
from models.booking import Bookings, HotelBookings, RestaurantBookings, TransportBookings, TourBookings
from models.booking import BookingTypeEnum, BookingStatusEnum, PaymentStatusEnum
from datetime import datetime, timezone, timedelta  # 👈 Added explicit timezone tracking here


def seed():
    db = SessionLocal()
    try:
        if db.query(Bookings).first():
            print("[SKIP] Bookings already seeded.")
            return

        # We will loop to generate 15 balanced historic entries across all domains
        for i in range(1, 16):
            b_type = \
            [BookingTypeEnum.hotel, BookingTypeEnum.restaurant, BookingTypeEnum.transport, BookingTypeEnum.tour][i % 4]
            master = Bookings(
                user_id=1, booking_type=b_type, contact_name=f"Traveler User {i}",
                contact_phone=f"+92-321-45678{i:02d}", contact_email=f"traveler{i}@gmail.com",
                cnic_number=f"37405-1234567-{i % 9}", total_amount=12000.0 * (i % 4 + 1),
                booking_status=BookingStatusEnum.confirmed, payment_status=PaymentStatusEnum.paid,
                special_requests="Non-smoking room, punctual dispatch preferences."
            )
            db.add(master)
            db.flush()

            # 🚀 UPDATED ALL TIMESTAMPS TO THE MODERN TIMEZONE-AWARE METHOD:
            current_utc_time = datetime.now(timezone.utc)

            if b_type == BookingTypeEnum.hotel:
                db.add(HotelBookings(
                    booking_id=master.id, hotel_id=1, room_id=1,
                    check_in=current_utc_time,
                    check_out=current_utc_time + timedelta(days=2),
                    number_of_rooms=1, adults=2, children=0
                ))
            elif b_type == BookingTypeEnum.restaurant:
                db.add(RestaurantBookings(
                    booking_id=master.id, restaurant_id=1,
                    reservation_date=current_utc_time,
                    reservation_time="08:00 PM", adults=2, children=0
                ))
            elif b_type == BookingTypeEnum.transport:
                db.add(TransportBookings(
                    booking_id=master.id, transport_id=1, from_location="Islamabad", to_location="Hunza",
                    departure_date=current_utc_time,
                    departure_time="09:00 PM", adults=2, children=0
                ))
            elif b_type == BookingTypeEnum.tour:
                db.add(TourBookings(
                    booking_id=master.id, package_id=1, number_of_travelers=2, adults=2, children=0
                ))

        db.commit()
        print("[SUCCESS] 15 Active, Confirmed Transaction Bookings successfully committed with zero warnings.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Bookings failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
