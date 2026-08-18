from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="tenants")
