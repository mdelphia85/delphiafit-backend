from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.database.connection import get_db
from app.crud.certification import CertificationCRUD
from app.models.certification import Certification
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/certification", tags=["Certifications"])
crud = CertificationCRUD()


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


@router.post("/create")
def create_certification(data: CertificationCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    return crud.create_certification(db, data.model_dump())


@router.get("/list")
def list_certifications(db: Session = Depends(get_db)):
    return crud.list_certifications(db)


@router.post("/requirement")
def add_requirement(data: RequirementCreate, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    if db.query(Certification.id).filter(Certification.id == data.certification_id).first() is None:
        raise HTTPException(status_code=404, detail="Certification not found.")
    return crud.add_requirement(db, data.model_dump())


@router.get("/requirement/{certification_id}")
def list_requirements(certification_id: int, db: Session = Depends(get_db)):
    return crud.list_requirements(db, certification_id)


@router.post("/record")
def issue_record(data: RecordIssue, coach=Depends(get_current_coach), db: Session = Depends(get_db)):
    if db.query(Certification.id).filter(Certification.id == data.certification_id, Certification.active.is_(True)).first() is None:
        raise HTTPException(status_code=404, detail="Certification not found.")
    if db.query(User.id).filter(User.id == data.user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return crud.issue_certification(db, data.model_dump())


@router.get("/record/{user_id}")
def list_records(user_id: int, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if user_id != current_user_id:
        raise HTTPException(status_code=404, detail="Certification records not found.")
    return crud.list_records(db, current_user_id)
