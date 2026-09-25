from database import SessionLocal
from models.category import Categories
from models.user import Users  # 👈 Added User import to find the admin signature


def seed():
    db = SessionLocal()
    try:
        if db.query(Categories).first():
            print("[SKIP] Categories already seeded.")
            return

        # 🧠 AUDIT SIGNATURE ACQUISITION: Find the administrator account we just seeded [INDEX: 1.1.2]
        admin = db.query(Users).filter(Users.role == "admin").first()
        admin_id = admin.id if admin else 1

        items = [
            Categories(name="Hotels & Stays", description="Luxury resorts and alpine cottages", creator_id=admin_id),
            Categories(name="Restaurants & Dining", description="Local cafes, traditional eateries, and fine dining",
                       creator_id=admin_id),
            Categories(name="Lakes & Rivers", description="Water bodies, boating valleys, and glacial streams",
                       creator_id=admin_id),
            Categories(name="Valleys & Viewpoints", description="High-altitude mountain vistas and meadows",
                       creator_id=admin_id),
            Categories(name="Historical Landmarks", description="Forts, ancient tracks, and heritage structures",
                       creator_id=admin_id),
            Categories(name="Adventure & Treks", description="Expeditions, jeep tracks, and climbing base camps",
                       creator_id=admin_id)
        ]
        db.add_all(items)
        db.commit()
        print("[SUCCESS] 6 Base Categories successfully seeded with dynamic admin audit IDs.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Categories failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
