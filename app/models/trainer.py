"""Personal trainers and consented training-client relationships.

Coach Hub/team coaching uses separate models and credentials. Trainer sessions use
regular user authentication plus an administrator-provisioned trainer profile.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class TrainerProfile(Base):
    __tablename__ = "trainer_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="trainer_profile")


class TrainerClientLink(Base):
    __tablename__ = "trainer_client_links"
    __table_args__ = (UniqueConstraint("trainer_user_id", "client_user_id", name="uq_trainer_client_link"),)

    id = Column(Integer, primary_key=True)
    trainer_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="pending", server_default="pending")
    invited_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
