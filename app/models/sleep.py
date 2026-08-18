from sqlalchemy import Column, Integer, Float, String, DateTime
from app.database.connection import Base

class SleepLog(Base):
    __tablename__ = "sleep_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    duration_hours = Column(Float, nullable=False)
    quality = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    date = Column(DateTime, nullable=False)
