from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class AcademyProgram(Base):
    __tablename__ = "academy_programs"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)          # Police Academy, Fire Academy, EMS Academy, etc.
    category = Column(String, nullable=False)      # police, fire, ems, military, corrections
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    modules = relationship("AcademyModule", back_populates="program")
    cadets = relationship("AcademyCadet", back_populates="program")


class AcademyModule(Base):
    __tablename__ = "academy_modules"

    id = Column(Integer, primary_key=True, index=True)

    program_id = Column(Integer, ForeignKey("academy_programs.id"), nullable=False)
    name = Column(String, nullable=False)          # PT, firearms, law, medical, scenarios
    module_type = Column(String, nullable=False)   # academic, physical, scenario, qualification
    description = Column(Text, nullable=True)

    program = relationship("AcademyProgram", back_populates="modules")
    evaluations = relationship("AcademyEvaluation", back_populates="module")


class AcademyCadet(Base):
    __tablename__ = "academy_cadets"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    program_id = Column(Integer, ForeignKey("academy_programs.id"), nullable=False)
    status = Column(String, default="enrolled")    # enrolled, active, graduated, failed

    program = relationship("AcademyProgram", back_populates="cadets")
    evaluations = relationship("AcademyEvaluation", back_populates="cadet")


class AcademyEvaluation(Base):
    __tablename__ = "academy_evaluations"

    id = Column(Integer, primary_key=True, index=True)

    cadet_id = Column(Integer, ForeignKey("academy_cadets.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("academy_modules.id"), nullable=False)

    score = Column(Float, nullable=True)
    passed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    cadet = relationship("AcademyCadet", back_populates="evaluations")
    module = relationship("AcademyModule", back_populates="evaluations")
