from sqlalchemy import Column, Integer, DateTime, String
from app.database.connection import Base

class HydrationLog(Base):
    __tablename__ = "hydration_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    amount_ml = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)
