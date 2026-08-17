from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    weight_kg = Column(Float, nullable=False)
    body_fat_percent = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)
