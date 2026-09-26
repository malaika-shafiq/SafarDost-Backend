from database import SessionLocal
from models.hotel import Hotels, HotelRooms


def seed():
    db = SessionLocal()
    try:
        if db.query(Hotels).first():
            print("[SKIP] Hotels already seeded.")
            return

        # Array containing explicit (Name, Location_ID, Base_Starting_Price) tuples matching your updated schema model
        hotel_names = [
            ("Karakoram Alpine Resort", 1, 8500.0),
            ("Serena Lux Inn", 1, 12000.0),
            ("Eagle's Nest Lodge", 1, 9500.0),
            ("Shangrila Resort Hotel", 2, 14000.0),
            ("Serena Shigar Fort", 2, 18000.0),
            ("Cold Desert Lodge", 2, 7500.0),
            ("Swat Palace Hotel", 3, 6500.0),
            ("Malam Jabba Ski Resort", 3, 11000.0),
            ("Naran Continental", 4, 8000.0),
            ("River View Hotel", 4, 7000.0),
            ("Gilgit Serena Inn", 5, 13000.0),
            ("Chitral Heights", 6, 9000.0),
            ("Raani Kot Cottage", 7, 5000.0),
            ("Neelum Green Resort", 8, 7500.0),
            ("Kumrat Glamping Nest", 9, 6000.0)
        ]

        for i, (name, loc_id, starting_price) in enumerate(hotel_names, start=1):
            hotel = Hotels(
                name=name,
                description="Luxury hospitality property in region offering premium amenities and comfort.",
                contact_information=f"+92-300-12345{i:02d}",
                facilities="WiFi, Hot Shower, Heating, Parking",
                base_price=starting_price,  # 🚀 FIXES THE NOT-NULL CONSTRAINT ERROR BY PASSING THE NEW BASELINE FIELD NATIVELY!
                status="active",
                location_id=loc_id,
                category_id=1,
                creator_id=1
            )
            db.add(hotel)
            db.flush()

            # Seed 2 structural room inventory types for each hotel
            r1 = HotelRooms(hotel_id=hotel.id, room_type="Standard Room", price_per_night=starting_price, capacity=2, quantity=10)
            r2 = HotelRooms(hotel_id=hotel.id, room_type="Luxury Suite", price_per_night=starting_price + 7500.0, capacity=4, quantity=5)
            db.add_all([r1, r2])

        db.commit()
        print("[SUCCESS] 15 Hotels with corresponding base prices and room supplies seeded cleanly.")
    except Exception as e:
        db.query().rollback() if hasattr(db, 'query') else db.rollback()
        print(f"[ERROR] Seeding Hotels failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
