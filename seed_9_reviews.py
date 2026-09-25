from database import SessionLocal
from models.review import Reviews, ReviewStatusEnum
from models.user import Users


def seed():
    db = SessionLocal()
    try:
        if db.query(Reviews).first():
            print("[SKIP] Reviews already seeded.")
            return

        # ✅ SAFETY CHECK: Ensure User ID 1 possesses a valid name fallback attribute for your endpoints
        test_user = db.query(Users).filter(Users.id == 1).first()
        if test_user and not getattr(test_user, "name", None):
            # Dynamically set a name property mapping if the column exists on your database row layout
            try:
                test_user.name = f"{test_user.first_name} {test_user.last_name}"
                db.add(test_user)
                db.flush()
            except Exception:
                pass  # Fall back gracefully if your user layout splits names purely across first/last fields

        comments = [
            "Exceptional view and hospitality!",
            "Very authentic taste, highly recommended.",
            "Comfortable ride through complex mountain loops.",
            "Unforgettable scenic beauty, pure paradise."
        ]

        for i in range(1, 31):
            target = i % 4
            rev = Reviews(
                rating=4 if i % 2 == 0 else 5,
                comment=comments[i % len(comments)],
                status=ReviewStatusEnum.active,
                user_id=1,
                place_id=(i % 15 + 1) if target == 0 else None,
                hotel_id=(i % 15 + 1) if target == 1 else None,
                restaurant_id=(i % 15 + 1) if target == 2 else None,
                transport_id=(i % 5 + 1) if target == 3 else None
            )
            db.add(rev)

        db.commit()
        print("[SUCCESS] 30 Polymorphic Traveler Reviews successfully synchronized and seeded.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding Reviews failed: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
