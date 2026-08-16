from sqlalchemy import Column, Integer, Boolean, Text, DateTime, ForeignKey
from datetime import datetime

from app.database import Base


class Clearance(Base):
    __tablename__ = "clearance"

    id = Column(Integer, primary_key=True, index=True)
    injury_id = Column(Integer, ForeignKey("injuries.id"), nullable=False)
    user_id = Column(Integer, nullable=False)

    cleared = Column(Boolean, default=False)
    clinician_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    cleared_at = Column(DateTime, nullable=True)
