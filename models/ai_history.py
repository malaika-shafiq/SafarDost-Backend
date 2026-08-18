import datetime
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from database import Base


def get_utc_now():
    # Modern, up-to-date UTC format helper optimized for SQLite structure
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class AIRecommendationHistory(Base):
    __tablename__ = "ai_recommendation_history"

    id = Column(Integer, primary_key=True, index=True)

    # Secure Link: Connects this specific history entry back to Users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Input Constraints Cache
    destination = Column(String, index=True, nullable=False)
    budget_pkr = Column(Float, nullable=False)
    total_days = Column(Integer, nullable=False)
    travel_style = Column(String, nullable=False)

    # The JSON Data Container: Saves the complex generated multi-day itinerary array block directly
    generated_itinerary = Column(JSON, nullable=False)

    # Active Audit Tracking Column
    created_at = Column(DateTime, default=get_utc_now)
