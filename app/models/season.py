from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)  # 2024-2025, Spring 2026, etc.
    year = Column(Integer, nullable=True)
    sport = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    competitions = relationship("Competition", back_populates="season")
