from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.instructor import InstructorCRUD

router = APIRouter(prefix="/instructor", tags=["Instructor Portal"])
crud = InstructorCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class InstructorCreate(BaseModel):
    user_id: int
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


# ---------------------------------------------------------
# Instructor
# ---------------------------------------------------------
@router.post("/create")
def create_instructor(data: InstructorCreate, db: Session = Depends(get_db)):
    return crud.create_instructor(db, data.model_dump())


@router.get("/list/{agency}")
def list_instructors(agency: str, db: Session = Depends(get_db)):
    return crud.list_instructors(db, agency)


# ---------------------------------------------------------
# Assignments
# ---------------------------------------------------------
@router.post("/assign")
def assign(data: AssignmentCreate, db: Session = Depends(get_db)):
    return crud.assign(db, data.model_dump())


@router.get("/assign/{instructor_id}")
def list_assignments(instructor_id: int, db: Session = Depends(get_db)):
    return crud.list_assignments(db, instructor_id)


# ---------------------------------------------------------
# Feedback
# ---------------------------------------------------------
@router.post("/feedback")
def add_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    return crud.add_feedback(db, data.model_dump())


@router.get("/feedback/{user_id}")
def list_feedback(user_id: int, db: Session = Depends(get_db)):
    return crud.list_feedback(db, user_id)
