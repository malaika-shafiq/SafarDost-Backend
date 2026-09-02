import os
from sqlalchemy.orm import sessionmaker
from database import engine

# 1. Force all relational models into memory to fix mapping setups
from models.user import Users, UserStatusEnum
from models.category import Categories
#from models.hotel import Hotels
from models.place import Places
#from models.restaurant import Restaurants
from models.location import Locations  # 👈 Add this line!

# Import your password hashing utility from your utils script
from utils.auth_utils import hash_password

# Set up the session factory linking directly to your database engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_admin_user():
    db = SessionLocal()
    try:
        admin_email = "admin@safardost.com"

        # Check if this admin email already exists to prevent duplicate entries
        existing_admin = db.query(Users).filter(Users.email == admin_email).first()
        if existing_admin:
            print(f"[-] Admin user '{admin_email}' already exists in the database.")
            return

        # Hash your admin password using your utility function
        hashed_pass = hash_password("SecureAdminPass123!")

        # Create the instance according to your exact modern model columns
        new_admin = Users(
            name="Administrator",
            email=admin_email,
            hashed_password=hashed_pass,
            role="admin",
            status=UserStatusEnum.active.value  # 👈 FIXED: Swapped out the object mapping for the raw value string string!
        )

        db.add(new_admin)
        db.commit()
        print(f"[+] Success! Admin user '{admin_email}' has been seeded safely into the database.")

    except Exception as e:
        print(f"[!] Seeding failed: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin_user()
