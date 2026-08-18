from datetime import datetime, timedelta
import hashlib
import os
import secrets
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_coach
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.crud.coach import CoachCRUD
from app.database.connection import get_db
from app.models.client import Client
from app.models.coach import Coach
from app.models.coach_team_membership import CoachTeamMembership
from app.models.invite import Invite
from app.models.plan import Plan
from app.models.schedule import Schedule
from app.models.team import Team
from app.routers.admin.auth import verify_admin
from app.services.email_delivery import send_coach_password_reset

router = APIRouter(prefix="/coach", tags=["Coach"])
coach_crud = CoachCRUD()


class CoachCreate(BaseModel):
    email: EmailStr
    name: str
    organization: Optional[str] = None
    role: Optional[str] = "coach"


class CoachUpdate(BaseModel):
    updates: Dict[str, Any]


class InviteAccept(BaseModel):
    token: str
    name: str


class CoachInviteAccept(BaseModel):
    invitation_token: str
    name: str
    password: str


class CoachLogin(BaseModel):
    email: EmailStr
    password: str


class CoachForgotPassword(BaseModel):
    email: EmailStr


class CoachResetPassword(BaseModel):
    email: EmailStr
    token: str
    new_password: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _accessible_teams(db: Session, coach: Coach) -> list[Team]:
    owned = db.query(Team).filter(Team.coach_id == coach.id, Team.is_active.is_(True)).all()
    memberships = db.query(CoachTeamMembership).filter(CoachTeamMembership.coach_id == coach.id).all()
    member_ids = [membership.team_id for membership in memberships]
    shared = []
    if member_ids:
        shared = db.query(Team).filter(Team.id.in_(member_ids), Team.is_active.is_(True)).all()
    by_id = {team.id: team for team in owned + shared}
    return list(by_id.values())


# ---------------------------------------------------------------------------
# Frontend coach-auth contract. Keep static routes before /{coach_id} routes.
# ---------------------------------------------------------------------------
@router.post("/login")
def coach_login(data: CoachLogin, db: Session = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.email == data.email, Coach.is_active.is_(True)).first()
    if not coach or not coach.hashed_password or not verify_password(data.password, coach.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid coach credentials")

    teams = _accessible_teams(db, coach)
    team_id = teams[0].id if teams else None
    token = create_access_token(
        {
            "sub": str(coach.id),
            "email": coach.email,
            "actor_type": "coach",
            "role": coach.role,
        }
    )
    return {"access_token": token, "token_type": "bearer", "coach_id": coach.id, "team_id": team_id}


@router.post("/password/forgot")
def coach_forgot_password(data: CoachForgotPassword, db: Session = Depends(get_db)):
    coach = db.query(Coach).filter(Coach.email == data.email).first()
    debug_token = None
    delivered = False
    if coach:
        raw_token = secrets.token_urlsafe(32)
        coach.password_reset_token_hash = _token_hash(raw_token)
        coach.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        try:
            delivered = send_coach_password_reset(coach.email, raw_token)
        except Exception:
            delivered = False
        if os.getenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "false").lower() in {"1", "true", "yes"}:
            debug_token = raw_token

    response = {"message": "If that coach account exists, reset instructions have been sent.", "delivery_configured": delivered}
    if debug_token:
        response["debug_token"] = debug_token
    return response


@router.post("/password/reset")
def coach_reset_password(data: CoachResetPassword, db: Session = Depends(get_db)):
    if len(data.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    coach = db.query(Coach).filter(Coach.email == data.email).first()
    if (
        not coach
        or not coach.password_reset_token_hash
        or not coach.password_reset_expires_at
        or coach.password_reset_expires_at < datetime.utcnow()
        or not secrets.compare_digest(coach.password_reset_token_hash, _token_hash(data.token))
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    coach.hashed_password = hash_password(data.new_password)
    coach.password_reset_token_hash = None
    coach.password_reset_expires_at = None
    coach.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password reset successful"}


@router.post("/invitations/accept")
def accept_coach_invitation(data: CoachInviteAccept, db: Session = Depends(get_db)):
    if len(data.password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")

    invite = db.query(Invite).filter(Invite.token == data.invitation_token).first()
    if not invite or invite.accepted:
        raise HTTPException(status_code=400, detail="Invalid or already-used invitation")
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation has expired")
    if invite.role == "client":
        raise HTTPException(status_code=400, detail="This is a client invitation, not a coach invitation")

    coach = db.query(Coach).filter(Coach.email == invite.email).first()
    if coach is None:
        coach = Coach(
            email=invite.email,
            name=data.name,
            organization=None,
            role=invite.role,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(coach)
        db.flush()
    else:
        coach.name = data.name
        coach.role = invite.role
        coach.is_active = True
        coach.updated_at = datetime.utcnow()

    coach.hashed_password = hash_password(data.password)

    if invite.team_id:
        membership = db.query(CoachTeamMembership).filter(
            CoachTeamMembership.coach_id == coach.id,
            CoachTeamMembership.team_id == invite.team_id,
        ).first()
        if membership is None:
            db.add(CoachTeamMembership(coach_id=coach.id, team_id=invite.team_id, role=invite.role))

    invite.accepted = True
    invite.accepted_at = datetime.utcnow()
    db.commit()
    return {"message": "Invitation accepted", "coach_id": coach.id, "team_id": invite.team_id}


@router.get("/team")
def coach_team_dashboard(
    team_id: Optional[int] = Query(default=None),
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    teams = _accessible_teams(db, coach)
    team_by_id = {team.id: team for team in teams}
    selected = team_by_id.get(team_id) if team_id is not None else (teams[0] if teams else None)
    if team_id is not None and selected is None:
        raise HTTPException(status_code=403, detail="You do not have access to that team")

    if selected:
        clients = db.query(Client).filter(Client.team_id == selected.id, Client.status != "inactive").all()
        active_programs = db.query(Plan).filter(Plan.team_id == selected.id, Plan.is_active.is_(True)).count()
        schedules = db.query(Schedule).filter(Schedule.team_id == selected.id).all()
    else:
        clients = db.query(Client).filter(Client.coach_id == coach.id, Client.status != "inactive").all()
        active_programs = db.query(Plan).filter(Plan.coach_id == coach.id, Plan.is_active.is_(True)).count()
        schedules = db.query(Schedule).filter(Schedule.coach_id == coach.id).all()

    weekly_hours = 0.0
    week_ago = datetime.utcnow() - timedelta(days=7)
    for schedule in schedules:
        if schedule.start_time and schedule.end_time and schedule.start_time >= week_ago:
            weekly_hours += max(0.0, (schedule.end_time - schedule.start_time).total_seconds() / 3600)

    client_rows = []
    for client in clients:
        latest_plan = (
            db.query(Plan)
            .filter(Plan.client_id == client.id, Plan.is_active.is_(True))
            .order_by(Plan.updated_at.desc())
            .first()
        )
        client_rows.append(
            {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "status": (client.status or "active").title(),
                "program": latest_plan.name if latest_plan else "No active program",
                "progress": 0,
            }
        )

    return {
        "team_id": selected.id if selected else None,
        "team": {
            "id": selected.id,
            "name": selected.name,
            "sport": selected.sport,
            "level": selected.level,
        } if selected else None,
        "available_teams": [{"id": team.id, "name": team.name} for team in teams],
        "stats": {
            "totalClients": len(client_rows),
            "activePrograms": active_programs,
            "messagesUnread": 0,
            "weeklyHours": round(weekly_hours, 1),
        },
        "clients": client_rows,
    }


# ---------------------------------------------------------------------------
# V2 management routes.
# ---------------------------------------------------------------------------
@router.post("/create")
def create_coach(
    data: CoachCreate,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    try:
        return coach_crud.create_coach(
            db=db,
            email=data.email,
            name=data.name,
            organization=data.organization,
            role=data.role,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/email/{email}")
def get_coach_by_email(email: str, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    coach = coach_crud.get_coach_by_email(db, email)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")
    return coach


@router.post("/invite/accept")
def accept_invite(data: InviteAccept, db: Session = Depends(get_db)):
    try:
        return coach_crud.accept_invite(db, data.token, data.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{coach_id}/teams")
def get_coach_teams(coach_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    try:
        return coach_crud.get_coach_teams(db, coach_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{coach_id}/clients")
def get_coach_clients(coach_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    try:
        return coach_crud.get_coach_clients(db, coach_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{coach_id}")
def get_coach(coach_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    coach = coach_crud.get_coach(db, coach_id)
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found.")
    return coach


@router.put("/{coach_id}/update")
def update_coach(
    coach_id: int,
    data: CoachUpdate,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    try:
        return coach_crud.update_coach(db, coach_id, data.updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{coach_id}/deactivate")
def deactivate_coach(
    coach_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    try:
        return coach_crud.deactivate_coach(db, coach_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
