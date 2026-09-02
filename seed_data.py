from sqlalchemy.orm import sessionmaker
from database import engine

# Force all synchronized models into memory
from models.user import Users
from models.location import Locations, LocationStatusEnum
from models.category import Categories, CategoryStatusEnum
from models.place import Places, PlaceStatusEnum
from models.image import Images, ImageResourceTypeEnum

# Set up the session connection factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_safardost_test_data():
    db = SessionLocal()
    try:
        print("[-] Fetching master administrator reference...")
        # 1. Fetch your existing admin user to use as the creator identity anchor
        admin = db.query(Users).filter(Users.role == "admin").first()
        if not admin:
            print("[!] Seeding failed: No admin user found. Please run 'python seed_admin.py' first!")
            return

        admin_id = admin.id
        print(f"[+] Found Admin ID: {admin_id}. Initiating master resource injection...")

        # ==========================================
        # 2. SEED MASTER LOCATIONS (VALLEYS)
        # ==========================================
        print("[-] Seeding regional master location nodes...")
        hunza = db.query(Locations).filter(Locations.name == "Hunza").first()
        if not hunza:
            hunza = Locations(
                name="Hunza",
                province_or_region="Gilgit-Baltistan",
                description="A mountainous valley in the northern part of the Gilgit-Baltistan region of Pakistan.",
                image_url="https://cloudinary.com",
                status=LocationStatusEnum.active.value,
                creator_id=admin_id
            )
            db.add(hunza)
            db.commit()
            db.refresh(hunza)
            print("[+] Location 'Hunza' injected successfully.")
        else:
            print("[-] Location 'Hunza' already exists. Skipping.")

        # ==========================================
        # 3. SEED DYNAMIC TAXONOMY CATEGORIES
        # ==========================================
        print("[-] Seeding dynamic taxonomy categorizations...")
        lakes_cat = db.query(Categories).filter(Categories.name == "Lakes").first()
        if not lakes_cat:
            lakes_cat = Categories(
                name="Lakes",
                description="Natural alpine or turquoise glacier water body formations.",
                status=CategoryStatusEnum.active.value,
                creator_id=admin_id
            )
            db.add(lakes_cat)
            db.commit()
            db.refresh(lakes_cat)
            print("[+] Category 'Lakes' injected successfully.")
        else:
            print("[-] Category 'Lakes' already exists. Skipping.")

        # ==========================================
        # 4. SEED TOURIST PLACES (POINTS OF INTEREST)
        # ==========================================
        print("[-] Seeding optimized destination spot records...")
        attabad = db.query(Places).filter(Places.name == "Attabad Lake").first()
        if not attabad:
            attabad = Places(
                name="Attabad Lake",
                description="A stunning turquoise lake in the Hunza Valley created by a landslide barrier event in 2010.",
                latitude=36.3167,
                longitude=74.8667,
                physical_address="Gojal Valley, Hunza District, Gilgit-Baltistan",
                entry_information="Free open public access. Boating or jet-ski activities require personal ticket fares.",
                recommended_visiting_information="Best visibility is from May to October when water turns solid blue.",
                travel_tips="Carry local PKR currency notes. Local mobile network data signals can be unstable around the lake edges.",
                status=PlaceStatusEnum.active.value,
                location_id=hunza.id,  # 👈 Safely hooks up the dynamic Location ID
                category_id=lakes_cat.id,  # 👈 Safely hooks up the dynamic Category ID
                creator_id=admin_id
            )
            db.add(attabad)
            db.commit()
            db.refresh(attabad)
            print("[+] Tourist Place 'Attabad Lake' injected successfully.")

            # ==========================================
            # 5. SEED POLYMORPHIC IMAGE ENTRIES
            # ==========================================
            print("[-] Unfolding nested multi-image strings into central polymorphic layout tables...")
            sample_photos = [
                "https://cloudinary.com",
                "https://cloudinary.com"
            ]
            for url in sample_photos:
                db_image = Images(
                    image_url=url,
                    resource_type=ImageResourceTypeEnum.place,
                    resource_id=attabad.id,  # Links directly to the newly generated Place ID
                    creator_id=admin_id
                )
                db.add(db_image)
            db.commit()
            print("[+] Relational polymorphic image links registered successfully.")
        else:
            print("[-] Tourist Place 'Attabad Lake' already exists. Skipping.")

        print("\n[***] ALL ENDPOINT MOCK VALIDATION SEEDS APPLIED SUCCESSFULY! [***]")

    except Exception as error:
        db.rollback()
        print(f"[!] Seeding sequence failed: {str(error)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_safardost_test_data()
