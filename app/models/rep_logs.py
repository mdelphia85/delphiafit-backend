from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.database.connection import Base

class RepLog(Base):
    __tablename__ = "rep_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    exercise_name = Column(String, nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
