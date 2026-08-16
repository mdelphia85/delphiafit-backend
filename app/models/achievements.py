from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)

    # The user who earned the achievement
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Achievement details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)  # e.g., "fitness", "nutrition", "consistency"
    icon = Column(String, nullable=True)      # frontend icon reference
    points = Column(Integer, default=0)       # XP or reward points

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to User
    user = relationship("User", back_populates="achievements")
