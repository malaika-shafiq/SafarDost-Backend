from database import SessionLocal
from models.place import Places


def seed():
    db = SessionLocal()
    try:
        if db.query(Places).first():
            print("[SKIP] Places already seeded.")
            return

        spots = [
            ("Attabad Lake", 1, 3), ("Altit Fort", 1, 5), ("Baltit Fort", 1, 5),
            ("Lower Kachura Shangrila", 2, 3), ("Upper Kachura Lake", 2, 3), ("Cold Desert Safaranga", 2, 4),
            ("Kalam Valley Lakes", 3, 4), ("Fizagat Riverside Park", 3, 4), ("Saif-ul-Maluk Lake", 4, 3),
            ("Babusar Top View", 4, 4), ("Naltar Valley Lakes", 5, 3), ("Kalash Heritage Site", 6, 5),
            ("Fairytale Meadows Base", 7, 6), ("Ratti Gali Alpine Lake", 8, 3), ("Jahaz Banda Meadows", 9, 6)
        ]

        for name, loc_id, cat_id in spots:
            place = Places(
                name=name,
                description="A breathtaking premium location drawing global explorers daily.",
                latitude=35.0 + (loc_id * 0.1),
                longitude=74.0 + (cat_id * 0.1),
                physical_address="Main Scenic Alpine Track Route",
                entry_information="Open to the public",
                recommended_visiting_information="Best visited between May and October",
                # ✅ SYNCED TO MODEL COLUMN NAME
                travel_tips="Bring offline local cash references and camera gear.",
                status="active",
                location_id=loc_id,
                category_id=cat_id,
                creator_id=1
            )
            db.add(place)

        db.commit()
        print("[SUCCESS] 15 Breathtaking Tourist Places seeded safely.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Places failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
