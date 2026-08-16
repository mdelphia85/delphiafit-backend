from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    country = Column(String, nullable=True)
    timezone = Column(String, nullable=True)

    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    tenants = relationship("Tenant", back_populates="organization")
    enterprise_settings = relationship("EnterpriseSettings", back_populates="organization", uselist=False)
