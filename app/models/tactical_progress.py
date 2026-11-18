from sqlalchemy import Column, ForeignKey, Integer, JSON, String, UniqueConstraint

from app.database.connection import Base


class TacticalProgress(Base):
    __tablename__ = "tactical_progress"
    __table_args__ = (UniqueConstraint("user_id", "module", "item_key", name="uq_tactical_progress_user_module_item"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module = Column(String(80), nullable=False, index=True)
    item_key = Column(String(120), nullable=False, default="state")
    data = Column(JSON, nullable=False)
