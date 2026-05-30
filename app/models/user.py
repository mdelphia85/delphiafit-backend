from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)          # <-- rename hashed_password → password
    is_admin = Column(Boolean, default=False)          # <-- add this
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # optional but recommended


