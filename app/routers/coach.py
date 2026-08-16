from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.crud.coach import CoachCRUD

router = APIRouter(prefix="/coach", tags=["Coach"])
coach_crud = CoachCRUD()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class CoachCreate(BaseModel):
    email: str
    name: str
    organization: Optional[str] = None
    role: Optional[str] = "coach"


class CoachUpdate(BaseModel):
    updates: Dict[str, Any]


class InviteAccept(BaseModel):
    token: str
    name: str


# ---------------------------------------------------------
# Create Coach
# ---------------------------------------------------------
@router.post("/create")
def create_coach(data: CoachCreate, db: Session = Depends(get_db)):
    try:
        coach = coach_crud.create_coach(
            db=db,
            email=data.email,
            name=data.name,
            organization=data.organization,
            role=data.role
        )
        return coach
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Coach by ID
# ---------------------------------------------------------
@router.get("/{coach_id}")
def get_coach(coach_id: int, db: Session = Depends(get_db)):
    coach = coach_crud.get_coach(db, coach_id)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")
    return coach


# ---------------------------------------------------------
# Get Coach by Email (login)
# ---------------------------------------------------------
@router.get("/email/{email}")
def get_coach_by_email(email: str, db: Session = Depends(get_db)):
    coach = coach_crud.get_coach_by_email(db, email)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")
    return coach


# ---------------------------------------------------------
# Update Coach
# ---------------------------------------------------------
@router.put("/{coach_id}/update")
def update_coach(coach_id: int, data: CoachUpdate, db: Session = Depends(get_db)):
    try:
        return coach_crud.update_coach(db, coach_id, data.updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Deactivate Coach
# ---------------------------------------------------------
@router.delete("/{coach_id}/deactivate")
def deactivate_coach(coach_id: int, db: Session = Depends(get_db)):
    try:
        return coach_crud.deactivate_coach(db, coach_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Accept Invite
# ---------------------------------------------------------
@router.post("/invite/accept")
def accept_invite(data: InviteAccept, db: Session = Depends(get_db)):
    try:
        return coach_crud.accept_invite(db, data.token, data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Coach Teams
# ---------------------------------------------------------
@router.get("/{coach_id}/teams")
def get_coach_teams(coach_id: int, db: Session = Depends(get_db)):
    try:
        return coach_crud.get_coach_teams(db, coach_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------
# Get Coach Clients
# ---------------------------------------------------------
@router.get("/{coach_id}/clients")
def get_coach_clients(coach_id: int, db: Session = Depends(get_db)):
    try:
        return coach_crud.get_coach_clients(db, coach_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
