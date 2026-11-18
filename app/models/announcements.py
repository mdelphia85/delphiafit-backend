from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import true
from datetime import datetime
from app.database.connection import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    # is_active means "published": only active announcements are shown to users.
    is_active = Column(Boolean, default=True, nullable=False, server_default=true())
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)
