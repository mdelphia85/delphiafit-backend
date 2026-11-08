from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.sql import func

from app.database.connection import Base


class UserDataRecord(Base):
    __tablename__ = "user_data_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection = Column(String(40), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("ix_user_data_owner_collection", "user_id", "collection"),)
