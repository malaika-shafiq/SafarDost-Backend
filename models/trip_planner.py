import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, JSON, ForeignKey
from database import Base


def get_utc_now():
    # Modern, up-to-date UTC format helper optimized for SQLite structure
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class TripContainer(Base):
    __tablename__ = "trip_containers"

    id = Column(Integer, primary_key=True, index=True)

    # Secure Link: Connects this specific trip portfolio entry back to Users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Core Container Metadata
    title = Column(String, nullable=False)  # e.g., "Summer Trek in Hunza"
    destination_town = Column(String, index=True, nullable=False)  # For cross-matching with weather/AI logs
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Structural ID referencing your Hotels catalog from Module B
    hotel_id = Column(Integer, nullable=True)

    # The JSON Data Containers: Saves multi-item reference ID array blocks directly
    restaurant_ids = Column(JSON, default=list, nullable=False)  # Array of integers: [12, 15]
    place_ids = Column(JSON, default=list, nullable=False)  # Array of integers: [3, 4, 8]

    # Active Audit Tracking Column
    created_at = Column(DateTime, default=get_utc_now)
