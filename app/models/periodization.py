from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class PeriodizationBlock(Base):
    __tablename__ = "periodization_blocks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    block_name = Column(String, nullable=False)  # e.g. "Hypertrophy Phase"
    focus = Column(String, nullable=False)       # strength, endurance, power
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
