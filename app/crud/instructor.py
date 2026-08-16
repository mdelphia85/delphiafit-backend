from sqlalchemy.orm import Session
from datetime import datetime

from app.models.instructor import Instructor, InstructorAssignment, InstructorFeedback


class InstructorCRUD:

    # ---------------------------------------------------------
    # Instructor
    # ---------------------------------------------------------
    def create_instructor(self, db: Session, data: dict):
        inst = Instructor(
            user_id=data["user_id"],
            agency=data["agency"],
            role=data["role"],
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)
        return inst

    def list_instructors(self, db: Session, agency: str):
        return db.query(Instructor).filter(
            Instructor.agency == agency,
            Instructor.active == True
        ).all()

    # ---------------------------------------------------------
    # Assignments
    # ---------------------------------------------------------
    def assign(self, db: Session, data: dict):
        assignment = InstructorAssignment(
            instructor_id=data["instructor_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            notes=data.get("notes")
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def list_assignments(self, db: Session, instructor_id: int):
        return db.query(InstructorAssignment).filter(
            InstructorAssignment.instructor_id == instructor_id
        ).all()

    # ---------------------------------------------------------
    # Feedback
    # ---------------------------------------------------------
    def add_feedback(self, db: Session, data: dict):
        fb = InstructorFeedback(
            instructor_id=data["instructor_id"],
            user_id=data["user_id"],
            category=data["category"],
            feedback=data["feedback"],
            timestamp=datetime.utcnow()
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return fb

    def list_feedback(self, db: Session, user_id: int):
        return db.query(InstructorFeedback).filter(
            InstructorFeedback.user_id == user_id
        ).all()
