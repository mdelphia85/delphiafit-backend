from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database.connection import Base

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    workout_type = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
