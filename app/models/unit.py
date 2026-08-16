from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Unit(Base):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)              # "Alpha Team", "Rescue 4", "Wildland Strike Team"
    unit_type = Column(String, nullable=False)         # swat, sof, fire, ems, sar, hazmat, wildland, maritime, aviation
    description = Column(Text, nullable=True)
    readiness_score = Column(Float, default=0.0)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("UnitMember", back_populates="unit")
    capabilities = relationship("UnitCapability", back_populates="unit")


class UnitMember(Base):
    __tablename__ = "unit_members"

    id = Column(Integer, primary_key=True, index=True)

    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    role = Column(String, nullable=False)              # breacher, medic, pilot, diver, firefighter, hazmat tech
    notes = Column(Text, nullable=True)

    unit = relationship("Unit", back_populates="members")


class UnitCapability(Base):
    __tablename__ = "unit_capabilities"

    id = Column(Integer, primary_key=True, index=True)

    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    capability = Column(String, nullable=False)         # cqb, rope_rescue, fireline, hazmat_ops, maritime_sar
    score = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    unit = relationship("Unit", back_populates="capabilities")
