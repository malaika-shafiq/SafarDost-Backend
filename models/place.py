from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship


class Places(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    category = Column(String)     # e.g., "Lake", "Fort", "Valley"
    description = Column(Text)
    image = Column(String)
    # Add the physical integer column to hold the owner's ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relational link: Connects a tourist place to its incoming reviews
    reviews = relationship("Reviews", back_populates="place")


    # 3. Add the explicit relationship property that SQLAlchemy is looking for
    creator = relationship("Users", back_populates="created_places")
