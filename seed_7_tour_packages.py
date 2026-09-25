from database import SessionLocal
from models.tour_package import TourPackages
import datetime


def seed():
    db = SessionLocal()
    try:
        if db.query(TourPackages).first():
            print("[SKIP] TourPackages already seeded.")
            return

        packages = [
            ("5-Day Hunza Blossom Escape", 1), ("4-Day Skardu Shangrila Paradise", 2),
            ("3-Day Swat Valley Ski Break", 3), ("6-Day Fairy Meadows Expedition", 7),
            ("5-Day Neelum Valley Retreat", 8), ("4-Day Kumrat Forest Glamping", 9),
            ("7-Day Full Northern Pakistan Mega Tour", 1), ("3-Day Naran Lake Saif-ul-Maluk Stay", 4),
            ("5-Day Chitral & Kalash Culture Festival", 6), ("4-Day Astor Deosai Safari", 10)
        ]

        for name, loc_id in packages:
            pkg = TourPackages(
                name=name,
                description="Comprehensive bundle itinerary inclusive of stays, transport and guidance maps.",
                price=35000.0 + (loc_id * 2000.0),
                duration=f"Multiple Days",
                start_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10),
                end_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=15),
                available_slots=25,  # 🚀 MATCHES YOUR MODEL INVENTORY COLUMN
                status="active",
                location_id=loc_id,
                creator_id=1
            )
            db.add(pkg)

        db.commit()
        print("[SUCCESS] 10 Comprehensive Group Tour Packages seeded safely.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding TourPackages failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
