from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)

    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)

    name = Column(String, nullable=False)
    format = Column(String, nullable=True)  # single_elimination, round_robin, swiss, etc.
    rules = Column(Text, nullable=True)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    competition = relationship("Competition", back_populates="tournaments")
