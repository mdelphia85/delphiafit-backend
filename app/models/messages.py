from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from datetime import datetime
from app.database.connection import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    # Resolution is independent of whether the owner has read the message.
    resolved = Column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at = Column(DateTime, default=datetime.utcnow)
