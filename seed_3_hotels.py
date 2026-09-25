from database import SessionLocal
from models.hotel import Hotels, HotelRooms


def seed():
    db = SessionLocal()
    try:
        if db.query(Hotels).first():
            print("[SKIP] Hotels already seeded.")
            return

        hotel_names = [
            ("Karakoram Alpine Resort", 1), ("Serena Lux Inn", 1), ("Eagle's Nest Lodge", 1),
            ("Shangrila Resort Hotel", 2), ("Serena Shigar Fort", 2), ("Cold Desert Lodge", 2),
            ("Swat Palace Hotel", 3), ("Malam Jabba Ski Resort", 3), ("Naran Continental", 4),
            ("River View Hotel", 4), ("Gilgit Serena Inn", 5), ("Chitral Heights", 6),
            ("Raani Kot Cottage", 7), ("Neelum Green Resort", 8), ("Kumrat Glamping Nest", 9)
        ]

        for i, (name, loc_id) in enumerate(hotel_names, start=1):
            hotel = Hotels(
                name=name, description=f"Luxury hospitality property in region.",
                contact_information=f"+92-300-12345{i:02d}", facilities="WiFi, Hot Shower, Heating, Parking",
                status="active", location_id=loc_id, category_id=1, creator_id=1
            )
            db.add(hotel)
            db.flush()

            # Seed 2 structural room inventory types for each hotel [INDEX: 1.1.2]
            r1 = HotelRooms(hotel_id=hotel.id, room_type="Standard Room", price_per_night=8500.0, capacity=2,
                            quantity=10)
            r2 = HotelRooms(hotel_id=hotel.id, room_type="Luxury Suite", price_per_night=16000.0, capacity=4,
                            quantity=5)
            db.add_all([r1, r2])

        db.commit()
        print("[SUCCESS] 15 Hotels with corresponding room supplies seeded.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Hotels failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
