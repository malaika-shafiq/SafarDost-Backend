import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load variables from your hidden local .env file
load_dotenv()

# 1. Fetch the DATABASE_URL variable.
# On my laptop, it reads from my local .env file.
# On Railway, Railway overrides this automatically with its secure cloud database URL.
raw_url = os.getenv("DATABASE_URL")

# 2. Safety fallback check in case .env isn't loaded properly locally
if not raw_url:
    raise ValueError("DATABASE_URL environment variable is missing! Check your local .env file.")

# 3. Fix the PostgreSQL dialect mismatch for SQLAlchemy 2.0
if raw_url.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = raw_url.replace("postgres://", "postgresql://", 1)
else:
    SQLALCHEMY_DATABASE_URL = raw_url

# 4. Initialize engine and session
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
