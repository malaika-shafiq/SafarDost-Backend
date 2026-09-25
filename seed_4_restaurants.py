from database import SessionLocal
from models.restaurant import Restaurants


def seed():
    db = SessionLocal()
    try:
        if db.query(Restaurants).first():
            print("[SKIP] Restaurants already seeded.")
            return

        eateries = [
            ("Hunza Walnut Cafe", 1), ("Hidden Paradise", 1), ("Skardu Trout Lounge", 2),
            ("Dewan-E-Khas", 2), ("Swat Trout Diner", 3), ("White Palace Resto", 3),
            ("Naran River Cafe", 4), ("Moon Restaurant", 4), ("Gilgit Shinwari", 5),
            ("Chitral Local Bites", 6), ("Meadows BBQ Hub", 7), ("Neelum Riverside", 8),
            ("Kumrat Campfire Grill", 9), ("Astor Traditional Kitchen", 10), ("Karakoram Pizza", 1)
        ]

        for i, (name, loc_id) in enumerate(eateries, start=1):
            rest = Restaurants(
                name=name, description="Excellent local and international cuisines.",
                cuisine="Pakistani Traditional, Continental", menu_details="Special Platters, Local Teas",
                price_range="Medium", contact=f"+92-333-98765{i:02d}",
                opening_information="11:00 AM - 11:00 PM", table_capacity=40,
                status="active", location_id=loc_id, category_id=2, creator_id=1
            )
            db.add(rest)

        db.commit()
        print("[SUCCESS] 15 Balanced Local Restaurants seeded.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Restaurants failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
