from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database.connection import Base


class AdminAuditLog(Base):
    """Append-only record of admin logins and administrative actions."""

    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=True, index=True)
    admin_email = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
