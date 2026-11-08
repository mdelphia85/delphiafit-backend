from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class EnterpriseSettings(Base):
    __tablename__ = "enterprise_settings"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)

    compliance_rules = Column(Text, nullable=True)
    forecasting_model = Column(String, nullable=True)  # arima, prophet, custom
    ai_mode = Column(String, nullable=True)  # conservative, balanced, aggressive

    dashboard_config = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="enterprise_settings")
