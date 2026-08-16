from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Federation(Base):
    __tablename__ = "federations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    sport = Column(String, nullable=True)

    rulebook = Column(Text, nullable=True)
    licensing_requirements = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    competitions = relationship("Competition", back_populates="federation")
