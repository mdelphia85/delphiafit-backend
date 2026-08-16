from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from datetime import datetime
from app.database.connection import Base

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    ingredients = Column(JSON, nullable=False)
    instructions = Column(String, nullable=False)

    calories = Column(Integer, default=0)
    protein = Column(Integer, default=0)
    carbs = Column(Integer, default=0)
    fats = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
