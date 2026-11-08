from sqlalchemy import Column, Integer, String, DateTime
from app.database.connection import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    activity_type = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    calories_burned = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
