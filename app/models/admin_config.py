from sqlalchemy import Column, JSON, String

from app.database.connection import Base


class AdminConfigSetting(Base):
    __tablename__ = "admin_config"

    key = Column(String, primary_key=True)
    data = Column(JSON, nullable=False, default=dict)
