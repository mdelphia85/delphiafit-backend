from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.connection import get_db
from app.models.invite import Invite
from app.models.team import Team
from app.models.coach import Coach

import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/invite", tags=["Invite"])


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class InviteCreate(BaseModel):
    coach_id: int
    team_id: Optional[int] = None
    email: str
    role: str = "client"  # client, assistant_coach, recruiter, etc.


class InviteResend(BaseModel):
    invite_id: int


class InviteRevoke(BaseModel):
    invite_id: int


# ---------------------------------------------------------
# Create Invite
# ---------------------------------------------------------
@router.post("/create")
def create_invite(data: InviteCreate, db: Session = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.id == data.coach_id).first()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")

    if data.team_id:
        team = db.query(Team).filter(Team.id == data.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found.")

    token = str(uuid.uuid4())

    invite = Invite(
        coach_id=data.coach_id,
        team_id=data.team_id,
        email=data.email,
        role=data.role,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        accepted=False,
        created_at=datetime.utcnow()
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    return {
        "message": "Invite created successfully.",
        "invite_id": invite.id,
        "token": invite.token
    }


# ---------------------------------------------------------
# Get Invite by ID
# ---------------------------------------------------------
@router.get("/{invite_id}")
def get_invite(invite_id: int, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")
    return invite


# ---------------------------------------------------------
# List Invites for Coach
# ---------------------------------------------------------
@router.get("/coach/{coach_id}")
def list_invites_for_coach(coach_id: int, db: Session = Depends(get_db)):
    invites = db.query(Invite).filter(Invite.coach_id == coach_id).all()
    return invites


# ---------------------------------------------------------
# List Invites for Team
# ---------------------------------------------------------
@router.get("/team/{team_id}")
def list_invites_for_team(team_id: int, db: Session = Depends(get_db)):
    invites = db.query(Invite).filter(Invite.team_id == team_id).all()
    return invites


# ---------------------------------------------------------
# Resend Invite (new token + new expiration)
# ---------------------------------------------------------
@router.post("/resend")
def resend_invite(data: InviteResend, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == data.invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")

    invite.token = str(uuid.uuid4())
    invite.expires_at = datetime.utcnow() + timedelta(days=7)

    db.commit()
    db.refresh(invite)

    return {
        "message": "Invite resent successfully.",
        "new_token": invite.token
    }


# ---------------------------------------------------------
# Revoke Invite
# ---------------------------------------------------------
@router.post("/revoke")
def revoke_invite(data: InviteRevoke, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == data.invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")

    db.delete(invite)
    db.commit()

    return {"message": "Invite revoked successfully."}
