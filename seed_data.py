from sqlalchemy.orm import sessionmaker
from database import engine
from datetime import datetime, timedelta

# Force all synchronized models into memory to prevent mapping setup crashes at script startup
from models.user import Users
from models.location import Locations, LocationStatusEnum
from models.category import Categories, CategoryStatusEnum
from models.place import Places, PlaceStatusEnum
from models.hotel import Hotels, HotelRooms, HotelStatusEnum, RoomStatusEnum
from models.restaurant import Restaurants, RestaurantStatusEnum
from models.review import Reviews, ReviewStatusEnum
from models.tour_package import TourPackages, PackageStatusEnum
from models.transport import Transports, TransportStatusEnum
from models.image import Images, ImageResourceTypeEnum

# Set up the session connection factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_safardost_master_data():
    db = SessionLocal()
    try:
        print("[-] Fetching master administrator reference...")
        admin = db.query(Users).filter(Users.role == "admin").first()
        if not admin:
            print("[!] Seeding failed: No admin user found. Please run 'python seed_admin.py' first!")
            return

        admin_id = admin.id
        print(f"[+] Found Admin ID: {admin_id}. Initiating master data injection...")

        # ==========================================
        # 1. SEED MASTER LOCATIONS
        # ==========================================
        print("[-] Seeding regional master location nodes...")
        hunza = db.query(Locations).filter(Locations.name == "Hunza").first()
        if not hunza:
            hunza = Locations(
                name="Hunza",
                province_or_region="Gilgit-Baltistan",
                description="A mountainous valley in the northern part of Gilgit-Baltistan.",
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
        # 2. SEED DYNAMIC TAXONOMY CATEGORIES
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

        hotels_cat = db.query(Categories).filter(Categories.name == "Hotels").first()
        if not hotels_cat:
            hotels_cat = Categories(
                name="Hotels",
                description="Luxury resorts, guest houses, and alpine stays.",
                status=CategoryStatusEnum.active.value,
                creator_id=admin_id
            )
            db.add(hotels_cat)

        rest_cat = db.query(Categories).filter(Categories.name == "Restaurants").first()
        if not rest_cat:
            rest_cat = Categories(
                name="Restaurants",
                description="Local cafes, traditional diners, and continental eateries.",
                status=CategoryStatusEnum.active.value,
                creator_id=admin_id
            )
            db.add(rest_cat)

        db.commit()
        db.refresh(lakes_cat)
        db.refresh(hotels_cat)
        db.refresh(rest_cat)
        print("[+] Base taxonomy lookup categories synchronized successfully.")

        # ==========================================
        # 3. SEED TOURIST PLACES
        # ==========================================
        print("[-] Seeding optimized destination spot records...")
        attabad = db.query(Places).filter(Places.name == "Attabad Lake").first()
        if not attabad:
            attabad = Places(
                name="Attabad Lake",
                description="A stunning turquoise lake in the Hunza Valley created by a landslide in 2010.",
                latitude=36.3167,
                longitude=74.8667,
                physical_address="Gojal Valley, Hunza District, Gilgit-Baltistan",
                entry_information="Free open public access. Boating activities require separate fares.",
                recommended_visiting_information="Best visibility is from May to October.",
                travel_tips="Carry local PKR cash; mobile signals can be unstable around the lake edge.",
                status=PlaceStatusEnum.active.value,
                location_id=hunza.id,
                category_id=lakes_cat.id,
                creator_id=admin_id
            )
            db.add(attabad)
            db.commit()
            db.refresh(attabad)

            # Polymorphic Image for Place
            db.add(Images(image_url="https://cloudinary.com", resource_type=ImageResourceTypeEnum.place,
                          resource_id=attabad.id, creator_id=admin_id))
            print("[+] Tourist Place 'Attabad Lake' injected successfully.")

        # ==========================================
        # 4. SEED HOTELS & ROOMS
        # ==========================================
        print("[-] Seeding hotel marketplace properties and room inventory...")
        luxus_hunza = db.query(Hotels).filter(Hotels.name == "Luxus Hunza").first()
        if not luxus_hunza:
            luxus_hunza = Hotels(
                name="Luxus Hunza",
                description="A premium luxury resort offering panoramic views of Attabad Lake and surrounding mountain ranges.",
                contact_information="+92-51-111-luxus",
                facilities="WiFi, AC, Free Parking, Heated Rooms, Lake-view Balcony, Restaurant",
                status=HotelStatusEnum.active,
                location_id=hunza.id,
                category_id=hotels_cat.id,
                creator_id=admin_id
            )
            db.add(luxus_hunza)
            db.commit()
            db.refresh(luxus_hunza)

            # Seed Rooms inside Hotel [INDEX: 0.1.11]
            room1 = HotelRooms(hotel_id=luxus_hunza.id, room_type="Deluxe Lake View Suite",
                               description="King bed, floor-to-ceiling glass windows facing the lake.",
                               price_per_night=25000.0, capacity=2, status=RoomStatusEnum.available)
            room2 = HotelRooms(hotel_id=luxus_hunza.id, room_type="Luxury Family Room",
                               description="Two queen beds, attached dynamic living area space.",
                               price_per_night=40000.0, capacity=4, status=RoomStatusEnum.available)
            db.add_all([room1, room2])

            # Polymorphic Image for Hotel
            db.add(Images(image_url="https://cloudinary.com", resource_type=ImageResourceTypeEnum.hotel,
                          resource_id=luxus_hunza.id, creator_id=admin_id))
            print("[+] Hotel 'Luxus Hunza' and nested rooms initialized successfully.")

        # ==========================================
        # 5. SEED RESTAURANTS
        # ==========================================
        print("[-] Seeding regional dining eateries...")
        cafe_de_hunza = db.query(Restaurants).filter(Restaurants.name == "Cafe de Hunza").first()
        if not cafe_de_hunza:
            cafe_de_hunza = Restaurants(
                name="Cafe de Hunza",
                description="Famous central local cafe known for its organic walnut cake, fresh coffee, and overlooking view of Karimabad bazaar.",
                cuisine="Local, Continental, Cafe Bakery",
                menu_details="Famous Walnut Cake, Hunza Herbal Tea, Espresso, local Apricot Pancakes",
                price_range="Medium",
                contact="+92-355-1234567",
                opening_information="08:00 AM - 10:00 PM",
                table_capacity=45,
                status=RestaurantStatusEnum.active,
                location_id=hunza.id,
                category_id=rest_cat.id,
                creator_id=admin_id
            )
            db.add(cafe_de_hunza)
            db.commit()
            db.refresh(cafe_de_hunza)

            # Polymorphic Image for Restaurant
            db.add(Images(image_url="https://cloudinary.com", resource_type=ImageResourceTypeEnum.restaurant,
                          resource_id=cafe_de_hunza.id, creator_id=admin_id))
            print("[+] Restaurant 'Cafe de Hunza' injected successfully.")

        # ==========================================
        # 6. SEED REVIEWS & EXPERIENCES
        # ==========================================
        print("[-] Seeding traveler shared experiences...")
        sample_review = db.query(Reviews).filter(Reviews.comment.ilike("%Amazing experience%")).first()
        if not sample_review and luxus_hunza:
            sample_review = Reviews(
                rating=5,
                comment="Amazing experience staying at Luxus Hunza! The lake view from the Deluxe room windows is breathtaking. Highly recommended!",
                status=ReviewStatusEnum.active,
                user_id=admin_id,
                hotel_id=luxus_hunza.id
            )
            db.add(sample_review)
            db.commit()
            db.refresh(sample_review)

            # Polymorphic Image for Review
            db.add(Images(image_url="https://cloudinary.com", resource_type=ImageResourceTypeEnum.review,
                          resource_id=sample_review.id, creator_id=admin_id))
            print("[+] Traveler sample review and photos uploaded live.")

        # ==========================================
        # 7. SEED RELATIONAL PREDEFINED TOUR PACKAGES
        # ==========================================
        print("[-] Seeding relational tour package bundles...")
        hunza_tour = db.query(TourPackages).filter(TourPackages.name == "5-Day Luxury Hunza Escape").first()
        if not hunza_tour and luxus_hunza and attabad:
            current_date = datetime.now()
            hunza_tour = TourPackages(
                name="5-Day Luxury Hunza Escape",
                description="A premium, all-inclusive luxury group tour package across Hunza Valley featuring lakeside stays and guided trekking.",
                duration="5 Days / 4 Nights",
                price=85000.0,
                available_slots=12,
                start_date=current_date + timedelta(days=15),
                end_date=current_date + timedelta(days=20),
                activities="Day 1: Arrival & Karimabad Tour. Day 2: Boating at Attabad Lake. Day 3: Khunjerab Pass Border Trek. Day 4: Altit & Baltit Fort visits.",
                transportation_information="Luxury AC Grand Cabin Saloon Coaster with professional mountain driver.",
                included_services="Breakfast & Dinner, Dedicated Tour Guide, Jeep Fares to Attabad, Basic Medical Kit, Professional Travel Photography",
                status=PackageStatusEnum.active,
                location_id=hunza.id,
                creator_id=admin_id
            )

            # 🏛️ RELATIONAL MANY-TO-MANY APPENDS: Binds actual model entries straight into your association schema bridge arrays! [INDEX: 0.1.27]
            hunza_tour.places.append(attabad)
            hunza_tour.hotels.append(luxus_hunza)

            db.add(hunza_tour)
            db.commit()
            db.refresh(hunza_tour)

            # Polymorphic Image for Tour Package
            db.add(Images(image_url="https://cloudinary.com", resource_type=ImageResourceTypeEnum.tour_package,
                          resource_id=hunza_tour.id, creator_id=admin_id))
            print("[+] Predefined Tour Package '5-Day Luxury Hunza Escape' mapped and seeded successfully.")

        # ==========================================
        # 8. SEED TRANSPORTS
        # ==========================================
        print("[-] Seeding transport fleet routes and vehicle profiles...")
        prado_jeep = db.query(Transports).filter(Transports.transport_type == "4x4 Toyota Prado Jeep").first()
        if not prado_jeep:
            prado_jeep = Transports(
                transport_type="4x4 Toyota Prado Jeep",
                from_location="Karimabad",
                to_location="Attabad Lake / Passu Cones",
                departure_time="Flexible Departure (Available on Demand)",
                arrival_time="1.5 Hours approximate transit time",
                price=8000.0,
                capacity=4,
                status=TransportStatusEnum.active,
                location_id=hunza.id,
                creator_id=admin_id
            )
            db.add(prado_jeep)
            db.commit()
            db.refresh(prado_jeep)

            # Polymorphic Image for Transport Asset
            db.add(Images(
                image_url="https://cloudinary.com",
                resource_type=ImageResourceTypeEnum.transport,
                resource_id=prado_jeep.id,
                creator_id=admin_id
            ))
            print("[+] Transport fleet asset '4x4 Toyota Prado Jeep' seeded successfully.")

        db.commit()
        print("\n[***] ALL MASTER ARCHITECTURE TESTING DATA SEEDS APPLIED SUCCESSFULLY! [***]")

    except Exception as error:
        db.rollback()
        print(f"[!] Seeding sequence failed: {str(error)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_safardost_master_data()
