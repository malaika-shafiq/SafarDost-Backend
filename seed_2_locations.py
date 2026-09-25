from database import SessionLocal
from models.location import Locations
from models.user import Users  # 👈 Added User import to find the admin signature


def seed():
    db = SessionLocal()
    try:
        if db.query(Locations).first():
            print("[SKIP] Locations already seeded.")
            return

        # 🧠 AUDIT SIGNATURE ACQUISITION: Find the administrator account [INDEX: 1.1.2]
        admin = db.query(Users).filter(Users.role == "admin").first()
        admin_id = admin.id if admin else 1

        # Array containing explicit (Name, Province/Region) tuples matching your SRS specs
        valleys = [
            ("Hunza Valley", "Gilgit-Baltistan"),
            ("Skardu", "Gilgit-Baltistan"),
            ("Swat Valley", "Khyber Pakhtunkhwa"),
            ("Naran Kaghan", "Khyber Pakhtunkhwa"),
            ("Gilgit Valley", "Gilgit-Baltistan"),
            ("Chitral", "Khyber Pakhtunkhwa"),
            ("Fairytale Meadows", "Gilgit-Baltistan"),
            ("Neelum Valley", "Azad Jammu & Kashmir"),
            ("Kumrat Valley", "Khyber Pakhtunkhwa"),
            ("Astor Valley", "Gilgit-Baltistan")
        ]

        items = [
            Locations(
                name=name,
                province_or_region=prov,  # ✅ FIXES THE NOT-NULL CONSTRAINT ERROR NATIVELY!
                description=f"Premium tourist destination node in {name}",
                status="active",
                creator_id=admin_id
            )
            for name, prov in valleys
        ]

        db.add_all(items)
        db.commit()
        print("[SUCCESS] 10 Master Regional Locations successfully seeded with provinces and admin audit IDs.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Locations failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
