from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class RecoveryStage(Base):
    __tablename__ = "recovery_stages"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("recovery_protocols.id"), nullable=False)

    name = Column(String, nullable=False)
    instructions = Column(Text, nullable=True)
    objective_criteria = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    protocol = relationship("RecoveryProtocol", back_populates="stages")
    progress = relationship("RecoveryProgress", back_populates="stage")
