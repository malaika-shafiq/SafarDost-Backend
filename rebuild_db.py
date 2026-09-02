from database import engine, Base
from sqlalchemy import text
# Make sure your other models remain imported here so create_all knows about them
from models.user import Users
from models.location import Locations
from models.category import Categories
from models.place import Places
from models.image import Images


def rebuild_database():
    print("[-] Executing structural database cascade wipe...")

    # 🏎️ FIXED LOCK TRAP: Force a cascade drop via raw SQL connection execution hooks
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            # Drops every single table in your public schema regardless of foreign key ties!
            connection.execute(text("DROP SCHEMA public CASCADE;"))
            connection.execute(text("CREATE SCHEMA public;"))
            transaction.commit()
            print("[+] Old schema structures dropped and schema namespace cleaned.")
        except Exception as err:
            transaction.rollback()
            print(f"[!] Safe wipe block failed, attempting standard approach: {err}")

    print("[+] Re-mapping optimized relational layout tables...")
    Base.metadata.create_all(bind=engine)
    print("[+] Database structure successfully refreshed!")


if __name__ == "__main__":
    rebuild_database()
