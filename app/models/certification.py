from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)              # Firefighter I, EMT-B, SWAT Operator, SOF Prep, etc.
    category = Column(String, nullable=False)          # fire, ems, police, sof, swat, hazmat, wildland, maritime
    description = Column(Text, nullable=True)
    required_score = Column(Float, default=70.0)
    expires_months = Column(Integer, default=12)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    requirements = relationship("CertificationRequirement", back_populates="certification")
    records = relationship("CertificationRecord", back_populates="certification")


class CertificationRequirement(Base):
    __tablename__ = "certification_requirements"

    id = Column(Integer, primary_key=True, index=True)

    certification_id = Column(Integer, ForeignKey("certifications.id"), nullable=False)
    requirement_type = Column(String, nullable=False)   # scenario, replay, evaluation, physical, academic
    target_id = Column(Integer, nullable=False)         # scenario_id, replay_id, module_id, etc.
    notes = Column(Text, nullable=True)

    certification = relationship("Certification", back_populates="requirements")


class CertificationRecord(Base):
    __tablename__ = "certification_records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    certification_id = Column(Integer, ForeignKey("certifications.id"), nullable=False)

    score = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    certification = relationship("Certification", back_populates="records")
