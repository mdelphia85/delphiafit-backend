from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class MacroPlan(Base):
    __tablename__ = "macro_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    daily_calories = Column(Integer, default=0)
    daily_protein = Column(Integer, default=0)
    daily_carbs = Column(Integer, default=0)
    daily_fats = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
