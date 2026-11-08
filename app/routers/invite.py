from datetime import datetime, timedelta
from typing import Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.database.connection import get_db
from app.models.coach import Coach
from app.models.invite import Invite
from app.schemas.invite import InviteSummary
from app.services.coach_access import get_accessible_team
from app.services.email_delivery import send_client_invitation, send_coach_invitation

router = APIRouter(prefix="/invite", tags=["Invite"])

# Roles that grant coach-level access to a team; only the team owner may issue them.
COACH_ROLES = {"assistant_coach", "analyst", "recruiter", "coach"}


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class InviteCreate(BaseModel):
    coach_id: Optional[int] = None  # ignored; the inviter is always the caller
    team_id: Optional[int] = None
    email: str
    role: str = "client"  # client, assistant_coach, recruiter, etc.


class InviteResend(BaseModel):
    invite_id: int


class InviteRevoke(BaseModel):
    invite_id: int


def _own_invite(db: Session, coach: Coach, invite_id: int) -> Invite:
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if invite.coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You did not create that invite.")
    return invite


def _summary(invite: Invite) -> dict:
    return {
        "id": invite.id,
        "email": invite.email,
        "role": invite.role,
        "team_id": invite.team_id,
        "accepted": bool(invite.accepted),
        "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
        "created_at": invite.created_at.isoformat() if invite.created_at else None,
    }


# ---------------------------------------------------------
# Create Invite
# ---------------------------------------------------------
@router.post("/create")
def create_invite(data: InviteCreate, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    if data.coach_id is not None and data.coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You can only create invites for yourself.")

    if data.role in COACH_ROLES:
        if data.team_id is None:
            raise HTTPException(status_code=400, detail="A team is required for coach invitations.")
        get_accessible_team(db, coach, data.team_id, owner_only=True)
    elif data.team_id is not None:
        get_accessible_team(db, coach, data.team_id)

    invite = Invite(
        coach_id=coach.id,
        team_id=data.team_id,
        email=data.email,
        role=data.role,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=7),
        accepted=False,
        created_at=datetime.utcnow(),
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    delivered = False
    try:
        send_invitation = send_client_invitation if data.role == "client" else send_coach_invitation
        delivered = send_invitation(invite.email, invite.token)
    except Exception:
        delivered = False

    return {
        "message": "Invite created successfully.",
        "invite_id": invite.id,
        "delivery_configured": delivered,
    }


# ---------------------------------------------------------
# List Invites (static routes first)
# ---------------------------------------------------------
@router.get("/coach/{coach_id}", response_model=list[InviteSummary])
def list_invites_for_coach(coach_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    if coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You can only list your own invites.")
    return [_summary(i) for i in db.query(Invite).filter(Invite.coach_id == coach.id).all()]


@router.get("/team/{team_id}", response_model=list[InviteSummary])
def list_invites_for_team(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = get_accessible_team(db, coach, team_id)
    return [_summary(i) for i in db.query(Invite).filter(Invite.team_id == team.id).all()]


@router.get("/{invite_id}", response_model=InviteSummary)
def get_invite(invite_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    return _summary(_own_invite(db, coach, invite_id))


# ---------------------------------------------------------
# Resend Invite (new token + new expiration)
# ---------------------------------------------------------
@router.post("/resend")
def resend_invite(data: InviteResend, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    invite = _own_invite(db, coach, data.invite_id)
    if invite.accepted:
        raise HTTPException(status_code=400, detail="That invite was already accepted.")

    invite.token = secrets.token_urlsafe(32)
    invite.expires_at = datetime.utcnow() + timedelta(days=7)

    try:
        send_invitation = send_client_invitation if invite.role == "client" else send_coach_invitation
        delivered = send_invitation(invite.email, invite.token)
    except Exception:
        delivered = False
    if not delivered:
        db.rollback()
        raise HTTPException(status_code=503, detail="Invitation email could not be delivered")

    db.commit()
    db.refresh(invite)

    return {"message": "Invite resent successfully.", "delivery_configured": True}


# ---------------------------------------------------------
# Revoke Invite
# ---------------------------------------------------------
@router.post("/revoke")
def revoke_invite(data: InviteRevoke, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    invite = _own_invite(db, coach, data.invite_id)

    db.delete(invite)
    db.commit()

    return {"message": "Invite revoked successfully."}
