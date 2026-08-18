from sqlalchemy import Column, Integer, Float, DateTime
from app.database.connection import Base

class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    weight_kg = Column(Float, nullable=False)
    body_fat_percent = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)

    @property
    def weight(self) -> float:
        return self.weight_kg

    @property
    def body_fat(self) -> float | None:
        return self.body_fat_percent

