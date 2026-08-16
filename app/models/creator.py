from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Creator(Base):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)  # links to your existing user system
    name = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    expertise = Column(String, nullable=True)  # fitness, coaching, nutrition, etc.
    profile_image = Column(String, nullable=True)

    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    listings = relationship("Listing", back_populates="creator")
    ratings = relationship("Rating", back_populates="creator")
