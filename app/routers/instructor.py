from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.database.connection import get_db
from app.crud.instructor import InstructorCRUD
from app.models.instructor import Instructor, InstructorAssignment, InstructorFeedback
from app.models.user import User

router = APIRouter(prefix="/instructor", tags=["Instructor Portal"])
crud = InstructorCRUD()


class InstructorCreate(BaseModel):
    user_id: Optional[int] = None
    agency: str
    role: str


class AssignmentCreate(BaseModel):
    instructor_id: int
    target_type: str
    target_id: int
    notes: Optional[str] = None


class FeedbackCreate(BaseModel):
    instructor_id: int
    user_id: int
    category: str
    feedback: str


def require_instructor(db: Session, instructor_id: int, coach_id: int):
    instructor = db.query(Instructor).filter(
        Instructor.id == instructor_id,
        Instructor.user_id == coach_id,
        Instructor.active.is_(True),
    ).first()
    if instructor is None:
        raise HTTPException(status_code=404, detail="Instructor not found.")
    return instructor


@router.post("/create")
def create_instructor(data: InstructorCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    return crud.create_instructor(db, {**data.model_dump(), "user_id": coach.id})


@router.get("/list/{agency}")
def list_instructors(agency: str, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    return crud.list_instructors(db, agency)


@router.post("/assign")
def assign(data: AssignmentCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    require_instructor(db, data.instructor_id, coach.id)
    return crud.assign(db, data.model_dump())


@router.get("/assign/{instructor_id}")
def list_assignments(instructor_id: int, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    require_instructor(db, instructor_id, coach.id)
    return crud.list_assignments(db, instructor_id)


@router.post("/feedback")
def add_feedback(data: FeedbackCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    require_instructor(db, data.instructor_id, coach.id)
    if db.query(User.id).filter(User.id == data.user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return crud.add_feedback(db, data.model_dump())


@router.get("/feedback/{user_id}")
def list_feedback(user_id: int, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    instructor_ids = db.query(Instructor.id).filter(Instructor.user_id == coach.id, Instructor.active.is_(True)).subquery()
    return db.query(InstructorFeedback).filter(
        InstructorFeedback.instructor_id.in_(instructor_ids),
        InstructorFeedback.user_id == user_id,
    ).all()
