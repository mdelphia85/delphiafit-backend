from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Drill(Base):
    __tablename__ = "drills"

    id = Column(Integer, primary_key=True, index=True)

    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)

    name = Column(String, nullable=False)
    category = Column(String, nullable=True)        # warmup, speed, agility, strength, tactical, etc.
    tags = Column(String, nullable=True)            # comma-separated tags
    difficulty = Column(String, default="medium")   # easy, medium, hard
    equipment = Column(String, nullable=True)       # cones, ladder, ball, sled, etc.

    video_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    instructions = Column(Text, nullable=True)
    # Example:
    # "Set up cones 10 yards apart. Sprint to cone, backpedal to start..."

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    coach = relationship("Coach", back_populates="drills")
