from sqlalchemy import Column, Integer, String, DateTime, Float
from datetime import datetime
from app.database.connection import Base

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    mood = Column(String, nullable=True)
    energy = Column(String, nullable=True)
    protein = Column(Float, default=0)
    water = Column(Float, default=0)
    calories = Column(Float, default=0)
    meals = Column(Float, default=0)
    workouts = Column(Float, default=0)
    supplements = Column(Float, default=0)
    date = Column(DateTime, default=datetime.utcnow)
