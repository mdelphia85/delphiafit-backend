from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    sport = Column(String, nullable=True)
    level = Column(String, nullable=True)  # amateur, pro, youth, national, international

    federation_id = Column(Integer, ForeignKey("federations.id"), nullable=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=True)

    is_virtual = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    federation = relationship("Federation", back_populates="competitions")
    season = relationship("Season", back_populates="competitions")
    tournaments = relationship("Tournament", back_populates="competition")
    ladders = relationship("Ladder", back_populates="competition")
