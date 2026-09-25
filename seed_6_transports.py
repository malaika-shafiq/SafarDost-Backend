from database import SessionLocal
from models.transport import Transports, TransportRentalModeEnum


def seed():
    db = SessionLocal()
    try:
        if db.query(Transports).first():
            print("[SKIP] Transports already seeded.")
            return

        # Mixed Fleet Management Seeds: 3 Public Shared Buses, 2 Private Dedicated Vehicles [INDEX: 1.1.2]
        fleet = [
            Transports(
                transport_type="Karakoram Luxury AC Coaster", from_location="Islamabad", to_location="Hunza",
                departure_time="Friday 09:00 PM", arrival_time="14 Hours Transit", price=5500.0, capacity=30,
                rental_mode=TransportRentalModeEnum.public_shared, available_seats=30, status="active", location_id=1,
                creator_id=1
            ),
            Transports(
                transport_type="Skardu VIP Express Coach", from_location="Islamabad", to_location="Skardu",
                departure_time="Thursday 08:00 PM", arrival_time="16 Hours Transit", price=6500.0, capacity=30,
                rental_mode=TransportRentalModeEnum.public_shared, available_seats=30, status="active", location_id=2,
                creator_id=1
            ),
            Transports(
                transport_type="Swat Valley Saloon Bus", from_location="Islamabad", to_location="Swat",
                departure_time="Daily 07:00 AM", arrival_time="5 Hours Transit", price=3500.0, capacity=40,
                rental_mode=TransportRentalModeEnum.public_shared, available_seats=40, status="active", location_id=3,
                creator_id=1
            ),
            Transports(
                transport_type="4x4 Mountain Jeep Prado", from_location="Gilgit Airport",
                to_location="Hunza Valley Tour",
                departure_time="On Flight Arrival", arrival_time="3 Hours Trail", price=18000.0, capacity=5,
                rental_mode=TransportRentalModeEnum.private_dedicated, available_seats=5, status="active",
                location_id=1, creator_id=1
            ),
            Transports(
                transport_type="Deosai Safari Land Cruiser", from_location="Skardu Bazaar", to_location="Deosai Plains",
                departure_time="On Demand Request", arrival_time="4 Hours Trail", price=22000.0, capacity=6,
                rental_mode=TransportRentalModeEnum.private_dedicated, available_seats=6, status="active",
                location_id=2, creator_id=1
            )
        ]

        db.add_all(fleet)
        db.commit()
        print("[SUCCESS] 5 Transports (3 Public Buses + 2 Private Jeeps) successfully seeded.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Transports failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
