from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)

    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    price = Column(Float, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("Creator", back_populates="listings")
