from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)

    # Group details
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)  # e.g., "fitness", "nutrition", "running", etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Members relationship
    members = relationship("GroupMember", back_populates="group")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)

    # Link to group
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)

    # Link to user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
