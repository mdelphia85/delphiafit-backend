from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)

    # The user who created or is participating in the challenge
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Challenge details
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)  # e.g., "fitness", "nutrition", "consistency"

    # Challenge parameters
    target_value = Column(Integer, nullable=True)  # e.g., 100 pushups, 10 workouts
    current_value = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)

    # Optional: daily/weekly streak tracking inside a challenge
    streak_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to User
    user = relationship("User", back_populates="challenges")
