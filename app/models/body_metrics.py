from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BodyMetrics(Base):
    __tablename__ = "body_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    body_fat_percent = Column(Float, nullable=True)
    muscle_mass_kg = Column(Float, nullable=True)

    waist_cm = Column(Float, nullable=True)
    hips_cm = Column(Float, nullable=True)
    chest_cm = Column(Float, nullable=True)

    date = Column(DateTime, nullable=False)
