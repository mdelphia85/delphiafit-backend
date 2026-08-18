from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.crud.certification import CertificationCRUD

router = APIRouter(prefix="/certification", tags=["Certifications"])
crud = CertificationCRUD()


# ---------------------------------------------------------
# Schemas
# ---------------------------------------------------------

class CertificationCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    required_score: Optional[float] = 70.0
    expires_months: Optional[int] = 12


class RequirementCreate(BaseModel):
    certification_id: int
    requirement_type: str
    target_id: int
    notes: Optional[str] = None


class RecordIssue(BaseModel):
    user_id: int
    certification_id: int
    score: Optional[float] = 0.0
    passed: Optional[bool] = False


# ---------------------------------------------------------
# Certifications
# ---------------------------------------------------------
@router.post("/create")
def create_certification(data: CertificationCreate, db: Session = Depends(get_db)):
    return crud.create_certification(db, data.model_dump())


@router.get("/list")
def list_certifications(db: Session = Depends(get_db)):
    return crud.list_certifications(db)


# ---------------------------------------------------------
# Requirements
# ---------------------------------------------------------
@router.post("/requirement")
def add_requirement(data: RequirementCreate, db: Session = Depends(get_db)):
    return crud.add_requirement(db, data.model_dump())


@router.get("/requirement/{certification_id}")
def list_requirements(certification_id: int, db: Session = Depends(get_db)):
    return crud.list_requirements(db, certification_id)


# ---------------------------------------------------------
# Records
# ---------------------------------------------------------
@router.post("/record")
def issue_record(data: RecordIssue, db: Session = Depends(get_db)):
    return crud.issue_certification(db, data.model_dump())


@router.get("/record/{user_id}")
def list_records(user_id: int, db: Session = Depends(get_db)):
    return crud.list_records(db, user_id)
