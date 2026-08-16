from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)
    agency = Column(String, nullable=False)          # police, fire, ems, military, sof, swat
    role = Column(String, nullable=False)            # lead instructor, assistant, evaluator
    active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    assignments = relationship("InstructorAssignment", back_populates="instructor")


class InstructorAssignment(Base):
    __tablename__ = "instructor_assignments"

    id = Column(Integer, primary_key=True, index=True)

    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    target_type = Column(String, nullable=False)     # academy, sof, swat, scenario, loadout, certification
    target_id = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    instructor = relationship("Instructor", back_populates="assignments")


class InstructorFeedback(Base):
    __tablename__ = "instructor_feedback"

    id = Column(Integer, primary_key=True, index=True)

    instructor_id = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)        # performance, fitness, tactics, decision-making
    feedback = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
