from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Ladder(Base):
    __tablename__ = "ladders"

    id = Column(Integer, primary_key=True, index=True)

    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)

    name = Column(String, nullable=False)
    ranking_method = Column(String, default="elo")  # elo, points, win_percentage

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    competition = relationship("Competition", back_populates="ladders")
