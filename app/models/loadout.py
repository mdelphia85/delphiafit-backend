from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Loadout(Base):
    __tablename__ = "loadouts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)              # "SWAT CQB Loadout", "SOF Ruck", "Fireline Pack"
    category = Column(String, nullable=False)          # swat, sof, fire, hazmat, wildland, sar, maritime
    description = Column(Text, nullable=True)
    total_weight = Column(Float, default=0.0)
    mobility_score = Column(Float, default=1.0)
    endurance_score = Column(Float, default=1.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("LoadoutItem", back_populates="loadout")


class LoadoutItem(Base):
    __tablename__ = "loadout_items"

    id = Column(Integer, primary_key=True, index=True)

    loadout_id = Column(Integer, ForeignKey("loadouts.id"), nullable=False)
    name = Column(String, nullable=False)              # helmet, vest, ammo, rope, medkit, SCBA, etc.
    weight = Column(Float, default=0.0)
    quantity = Column(Integer, default=1)
    notes = Column(Text, nullable=True)

    loadout = relationship("Loadout", back_populates="items")
