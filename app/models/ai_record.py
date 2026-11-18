from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.database.connection import Base


class AIRecord(Base):
    __tablename__ = "ai_records"
    __table_args__ = (
        Index("uq_ai_records_user_id_idempotency_key", "user_id", "idempotency_key", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=True)
    feature = Column(String, nullable=False, index=True)
    input_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
