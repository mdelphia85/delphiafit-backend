from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.database.connection import Base

class PersonalRecord(Base):
    __tablename__ = "personal_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_name = Column(String, nullable=False)
    pr_type = Column(String, nullable=False)  # "1RM", "max_reps", "max_weight"
    value = Column(Float, nullable=False)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
