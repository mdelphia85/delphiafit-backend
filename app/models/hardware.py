from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.database.connection import Base


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_device_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String, nullable=False, index=True)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    linked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_sync = Column(DateTime, nullable=True)
    status = Column(String, default="linked", nullable=False)
