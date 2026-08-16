from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)

    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    user_id = Column(Integer, nullable=False)

    rating = Column(Float, nullable=False)  # 1.0 – 5.0
    review = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Creator", back_populates="ratings")
