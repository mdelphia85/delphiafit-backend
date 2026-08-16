from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    calories = Column(Integer, default=0)
    protein = Column(Integer, default=0)
    carbs = Column(Integer, default=0)
    fats = Column(Integer, default=0)
    water_oz = Column(Integer, default=0)

    notes = Column(String, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
