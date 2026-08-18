import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class WeatherCache(Base):
    __tablename__ = "weather_caches"

    id = Column(Integer, primary_key=True, index=True)
    city_name = Column(String, index=True, nullable=False)
    temperature_c = Column(Float, nullable=False)
    condition_text = Column(String, nullable=False)
    humidity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)
