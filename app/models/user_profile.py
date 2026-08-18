from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.connection import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    dob = Column(String, nullable=True)
    weight_unit = Column(String, default="kg", nullable=False)
    height_unit = Column(String, default="cm", nullable=False)
    starting_weight = Column(String, nullable=True)
    current_weight = Column(String, nullable=True)
    goal_weight = Column(String, nullable=True)
    height = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")
