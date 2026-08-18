from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.auth.hashing import hash_password
from app.database.connection import get_db
from app.models.client import Client
from app.models.coach import Coach
from app.models.coach_team_membership import CoachTeamMembership
from app.models.invite import Invite
from app.models.team import Team
from app.models.user import User
from app.services.email_delivery import send_client_invitation

router = APIRouter(prefix="/staff", tags=["Staff"])


class ClientInviteRequest(BaseModel):
    email: EmailStr


class ClientInviteAcceptRequest(BaseModel):
    invitation_token: str
    name: str
    password: str


@router.post("/invitations/accept")
def accept_client_invitation(
    data: ClientInviteAcceptRequest,
    db: Session = Depends(get_db),
):
    invite = db.query(Invite).filter(Invite.token == data.invitation_token).first()
    if not invite or invite.accepted or invite.role != "client":
        raise HTTPException(status_code=400, detail="Invalid or already-used client invitation")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")
    if len(data.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name is required")

    user = db.query(User).filter(User.email == invite.email).first()
    existing_account = user is not None
    if user is None:
        if len(data.password) < 10:
            raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
        user = User(
            name=data.name.strip(),
            email=invite.email,
            hashed_password=hash_password(data.password),
        )
        db.add(user)
        db.flush()

    client = db.query(Client).filter(Client.email == invite.email).first()
    if client is None:
        client = Client(
            coach_id=invite.coach_id,
            team_id=invite.team_id,
            email=invite.email,
            name=data.name.strip(),
            status="active",
        )
        db.add(client)
    else:
        client.coach_id = invite.coach_id
        client.team_id = invite.team_id
        client.name = data.name.strip()
        client.status = "active"
        client.updated_at = datetime.utcnow()

    invite.accepted = True
    invite.accepted_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return {
        "message": "Invitation accepted",
        "client_id": client.id,
        "existing_account": existing_account,
        "login_email": invite.email,
    }


def _team_ids(db: Session, coach_id: int) -> list[int]:
    owned = [row[0] for row in db.query(Team.id).filter(Team.coach_id == coach_id, Team.is_active.is_(True)).all()]
    shared = [row[0] for row in db.query(CoachTeamMembership.team_id).filter(CoachTeamMembership.coach_id == coach_id).all()]
    return list(dict.fromkeys(owned + shared))


def _client_payload(client: Client) -> dict:
    return {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "status": (client.status or "active").title(),
        "joinDate": client.created_at.date().isoformat() if client.created_at else None,
        "team_id": client.team_id,
    }


@router.get("/clients")
def list_staff_clients(
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    team_ids = _team_ids(db, coach.id)
    query = db.query(Client).filter(Client.status != "inactive")
    if team_ids:
        clients = query.filter((Client.coach_id == coach.id) | (Client.team_id.in_(team_ids))).all()
    else:
        clients = query.filter(Client.coach_id == coach.id).all()
    return {"clients": [_client_payload(client) for client in clients]}


@router.post("/clients/invite")
def invite_staff_client(
    data: ClientInviteRequest,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    existing = db.query(Client).filter(Client.email == data.email, Client.status != "inactive").first()
    if existing:
        raise HTTPException(status_code=400, detail="That client is already active")

    team_ids = _team_ids(db, coach.id)
    team_id = team_ids[0] if team_ids else None
    token = secrets.token_urlsafe(32)
    invite = Invite(
        coach_id=coach.id,
        team_id=team_id,
        email=data.email,
        role="client",
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),
        accepted=False,
        created_at=datetime.utcnow(),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    delivered = False
    try:
        delivered = send_client_invitation(invite.email, invite.token)
    except Exception:
        delivered = False
    return {"message": "Invitation created", "invite_id": invite.id, "delivery_configured": delivered}


@router.delete("/clients/{client_id}")
def remove_staff_client(
    client_id: int,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    accessible_team_ids = set(_team_ids(db, coach.id))
    if client.coach_id != coach.id and client.team_id not in accessible_team_ids:
        raise HTTPException(status_code=403, detail="You do not manage this client")
    client.status = "inactive"
    client.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "removed", "id": client.id}
