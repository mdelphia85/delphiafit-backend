"""Coach Hub API: plans, assignments, messaging, progress, teams, drills and invitations.

Mounted under /staff by app.routers.staff. Coach endpoints require a coach token;
the /my/* endpoints require a regular user token whose email matches a Client record.
"""

from datetime import datetime, timedelta
import json
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth.coach_dependencies import get_current_client, get_current_coach
from app.database.connection import get_db
from app.models.body_metrics import BodyMetrics
from app.models.client import Client
from app.models.coach import Coach
from app.models.coach_message import CoachMessage
from app.models.daily_log import DailyLog
from app.models.drill import Drill
from app.models.invite import Invite
from app.models.plan import Plan
from app.models.plan_assignment import PlanAssignment
from app.models.team import Team
from app.models.user import User
from app.models.weight import WeightLog
from app.models.workout_log import WorkoutLog
from app.services.coach_access import (
    accessible_team_ids,
    get_accessible_team,
    get_managed_client,
    managed_clients_query,
)
from app.services.email_delivery import send_coach_invitation

router = APIRouter(tags=["Coach Hub"])

COACH_INVITE_ROLES = {"assistant_coach", "analyst", "recruiter", "coach"}


def _iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------
def activity_by_email(db: Session, emails: list[str]) -> dict[str, dict]:
    """Workouts and distinct active days over the last 7 days, keyed by client email."""
    result = {email: {"workouts_7d": 0, "active_days_7d": 0} for email in emails}
    if not emails:
        return result
    users = db.query(User.id, User.email).filter(User.email.in_(emails)).all()
    by_id = {user_id: email for user_id, email in users}
    if not by_id:
        return result
    week_ago = datetime.utcnow() - timedelta(days=7)
    logs = db.query(WorkoutLog.user_id, WorkoutLog.date).filter(
        WorkoutLog.user_id.in_(list(by_id)), WorkoutLog.date >= week_ago
    ).all()
    days: dict[str, set] = {}
    for user_id, when in logs:
        email = by_id[user_id]
        result[email]["workouts_7d"] += 1
        days.setdefault(email, set()).add(when.date() if when else None)
    for email, day_set in days.items():
        result[email]["active_days_7d"] = len(day_set)
    return result


@router.get("/clients/{client_id}/progress")
def client_progress(
    client_id: int,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    client = get_managed_client(db, coach, client_id)
    user = db.query(User).filter(User.email == client.email).first()
    payload = {
        "client": {
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "status": (client.status or "active").title(),
            "joinDate": client.created_at.date().isoformat() if client.created_at else None,
        },
        "has_account": user is not None,
        "weights": [],
        "workouts": [],
        "daily_logs": [],
        "body_metrics": [],
        "summary": {
            "latest_weight_kg": None,
            "starting_weight_kg": None,
            "weight_change_kg": None,
            "workouts_7d": 0,
            "workouts_30d": 0,
            "minutes_30d": 0,
            "active_days_7d": 0,
            "last_activity": None,
        },
        "plans": _client_plans(db, client.id),
    }
    if user is None:
        return payload

    weights = db.query(WeightLog).filter(WeightLog.user_id == user.id).order_by(WeightLog.date.desc()).limit(60).all()
    weights.reverse()
    payload["weights"] = [
        {"date": _iso(w.date), "weight_kg": w.weight_kg, "body_fat_percent": w.body_fat_percent} for w in weights
    ]

    now = datetime.utcnow()
    workouts = (
        db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id).order_by(WorkoutLog.date.desc()).limit(30).all()
    )
    payload["workouts"] = [
        {
            "id": w.id,
            "date": _iso(w.date),
            "mode": w.mode,
            "name": w.manual_name or w.workout_type or "Workout",
            "duration_minutes": w.duration_minutes,
        }
        for w in workouts
    ]
    logs = db.query(DailyLog).filter(DailyLog.user_id == user.id).order_by(DailyLog.date.desc()).limit(14).all()
    payload["daily_logs"] = [
        {
            "date": _iso(d.date),
            "protein": d.protein,
            "water": d.water,
            "calories": d.calories,
            "meals": d.meals,
            "workouts": d.workouts,
            "mood": d.mood,
            "energy": d.energy,
        }
        for d in logs
    ]
    metrics = db.query(BodyMetrics).filter(BodyMetrics.user_id == user.id).order_by(BodyMetrics.date.desc()).limit(10).all()
    payload["body_metrics"] = [
        {
            "date": _iso(m.date),
            "weight_kg": m.weight_kg,
            "body_fat_percent": m.body_fat_percent,
            "waist_cm": m.waist_cm,
            "chest_cm": m.chest_cm,
            "hips_cm": m.hips_cm,
        }
        for m in metrics
    ]

    summary = payload["summary"]
    if weights:
        summary["latest_weight_kg"] = weights[-1].weight_kg
        summary["starting_weight_kg"] = weights[0].weight_kg
        summary["weight_change_kg"] = round(weights[-1].weight_kg - weights[0].weight_kg, 2)
    recent = [w for w in workouts if w.date and w.date >= now - timedelta(days=30)]
    summary["workouts_30d"] = len(recent)
    summary["minutes_30d"] = sum(w.duration_minutes or 0 for w in recent)
    summary["workouts_7d"] = sum(1 for w in recent if w.date >= now - timedelta(days=7))
    summary["active_days_7d"] = len({w.date.date() for w in recent if w.date >= now - timedelta(days=7)})
    summary["last_activity"] = _iso(workouts[0].date) if workouts else None
    return payload


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
class PlanIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=4000)
    plan_type: str = Field(default="workout", max_length=40)
    duration_weeks: int = Field(default=4, ge=1, le=104)
    difficulty: Optional[str] = Field(default=None, max_length=40)
    items: list[str] = Field(default_factory=list, max_length=100)
    team_id: Optional[int] = None


class AssignIn(BaseModel):
    client_id: Optional[int] = None
    team_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=1000)


def _plan_content(data: PlanIn) -> str:
    return json.dumps(
        {
            "duration_weeks": data.duration_weeks,
            "difficulty": data.difficulty,
            "items": [item.strip() for item in data.items if item.strip()],
        }
    )


def _plan_payload(plan: Plan, coach: Coach, assigned: int = 0) -> dict:
    try:
        content = json.loads(plan.content) if plan.content else {}
    except ValueError:
        content = {}
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "plan_type": plan.plan_type,
        "duration_weeks": content.get("duration_weeks"),
        "difficulty": content.get("difficulty"),
        "items": content.get("items", []),
        "team_id": plan.team_id,
        "version": plan.version,
        "owned": plan.coach_id == coach.id,
        "assigned_clients": assigned,
        "created_at": _iso(plan.created_at),
        "updated_at": _iso(plan.updated_at),
    }


def _get_plan(db: Session, coach: Coach, plan_id: int) -> Plan:
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.coach_id != coach.id and (plan.team_id is None or plan.team_id not in accessible_team_ids(db, coach.id)):
        raise HTTPException(status_code=403, detail="You do not have access to that plan")
    return plan


def _client_plans(db: Session, client_id: int) -> list[dict]:
    rows = (
        db.query(PlanAssignment, Plan)
        .join(Plan, Plan.id == PlanAssignment.plan_id)
        .filter(PlanAssignment.client_id == client_id, PlanAssignment.status == "active")
        .order_by(PlanAssignment.assigned_at.desc())
        .all()
    )
    result = []
    for assignment, plan in rows:
        try:
            content = json.loads(plan.content) if plan.content else {}
        except ValueError:
            content = {}
        result.append(
            {
                "assignment_id": assignment.id,
                "plan_id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "plan_type": plan.plan_type,
                "duration_weeks": content.get("duration_weeks"),
                "difficulty": content.get("difficulty"),
                "items": content.get("items", []),
                "notes": assignment.notes,
                "assigned_at": _iso(assignment.assigned_at),
            }
        )
    return result


@router.get("/plans")
def list_plans(coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team_ids = accessible_team_ids(db, coach.id)
    query = db.query(Plan).filter(Plan.is_active.is_(True))
    if team_ids:
        query = query.filter((Plan.coach_id == coach.id) | (Plan.team_id.in_(team_ids)))
    else:
        query = query.filter(Plan.coach_id == coach.id)
    plans = query.order_by(Plan.updated_at.desc()).all()
    counts = {}
    if plans:
        for plan_id, in db.query(PlanAssignment.plan_id).filter(
            PlanAssignment.plan_id.in_([p.id for p in plans]), PlanAssignment.status == "active"
        ):
            counts[plan_id] = counts.get(plan_id, 0) + 1
    return {"plans": [_plan_payload(plan, coach, counts.get(plan.id, 0)) for plan in plans]}


@router.post("/plans", status_code=201)
def create_plan(data: PlanIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    if data.team_id is not None:
        get_accessible_team(db, coach, data.team_id)
    plan = Plan(
        coach_id=coach.id,
        team_id=data.team_id,
        name=data.name.strip(),
        description=data.description,
        plan_type=data.plan_type,
        content=_plan_content(data),
        version=1,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_payload(plan, coach)


@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, data: PlanIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    plan = _get_plan(db, coach, plan_id)
    if data.team_id is not None:
        get_accessible_team(db, coach, data.team_id)
    plan.name = data.name.strip()
    plan.description = data.description
    plan.plan_type = data.plan_type
    plan.team_id = data.team_id
    plan.content = _plan_content(data)
    plan.version = (plan.version or 1) + 1
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return _plan_payload(plan, coach)


@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    plan = _get_plan(db, coach, plan_id)
    plan.is_active = False
    plan.updated_at = datetime.utcnow()
    db.query(PlanAssignment).filter(PlanAssignment.plan_id == plan.id, PlanAssignment.status == "active").update(
        {"status": "cancelled", "updated_at": datetime.utcnow()}
    )
    db.commit()
    return {"status": "deleted", "id": plan.id}


@router.post("/plans/{plan_id}/assignments")
def assign_plan(
    plan_id: int,
    data: AssignIn,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    plan = _get_plan(db, coach, plan_id)
    if (data.client_id is None) == (data.team_id is None):
        raise HTTPException(status_code=400, detail="Provide exactly one of client_id or team_id")

    if data.client_id is not None:
        targets = [get_managed_client(db, coach, data.client_id)]
    else:
        team = get_accessible_team(db, coach, data.team_id)
        targets = db.query(Client).filter(Client.team_id == team.id, Client.status != "inactive").all()
        if not targets:
            raise HTTPException(status_code=400, detail="That team has no active clients")

    now = datetime.utcnow()
    for client in targets:
        assignment = db.query(PlanAssignment).filter(
            PlanAssignment.plan_id == plan.id, PlanAssignment.client_id == client.id
        ).first()
        if assignment is None:
            db.add(
                PlanAssignment(
                    plan_id=plan.id,
                    client_id=client.id,
                    coach_id=coach.id,
                    status="active",
                    notes=data.notes,
                    assigned_at=now,
                    updated_at=now,
                )
            )
        else:
            assignment.status = "active"
            assignment.notes = data.notes
            assignment.coach_id = coach.id
            assignment.updated_at = now
    db.commit()
    return {"plan_id": plan.id, "assigned_client_ids": [client.id for client in targets]}


@router.delete("/plans/{plan_id}/assignments/{client_id}")
def unassign_plan(
    plan_id: int,
    client_id: int,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    plan = _get_plan(db, coach, plan_id)
    client = get_managed_client(db, coach, client_id)
    assignment = db.query(PlanAssignment).filter(
        PlanAssignment.plan_id == plan.id, PlanAssignment.client_id == client.id
    ).first()
    if assignment is None or assignment.status != "active":
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.status = "cancelled"
    assignment.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "unassigned"}


@router.get("/clients/{client_id}/plans")
def list_client_plans(client_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    client = get_managed_client(db, coach, client_id)
    return {"plans": _client_plans(db, client.id)}


@router.get("/my/plans")
def my_plans(client: Client = Depends(get_current_client), db: Session = Depends(get_db)):
    return {"plans": _client_plans(db, client.id)}


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------
class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class BroadcastIn(BaseModel):
    team_id: int
    body: str = Field(min_length=1, max_length=2000)


def _message_payload(message: CoachMessage) -> dict:
    return {
        "id": message.id,
        "sender": message.sender,
        "body": message.body,
        "created_at": _iso(message.created_at),
        "read": message.read_at is not None,
    }


def unread_for_coach(db: Session, coach_id: int) -> int:
    return (
        db.query(CoachMessage)
        .filter(CoachMessage.coach_id == coach_id, CoachMessage.sender == "client", CoachMessage.read_at.is_(None))
        .count()
    )


@router.get("/messages/threads")
def message_threads(coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    threads = []
    for client in managed_clients_query(db, coach).order_by(Client.name).all():
        last = (
            db.query(CoachMessage)
            .filter(CoachMessage.coach_id == coach.id, CoachMessage.client_id == client.id)
            .order_by(CoachMessage.created_at.desc(), CoachMessage.id.desc())
            .first()
        )
        unread = (
            db.query(CoachMessage)
            .filter(
                CoachMessage.coach_id == coach.id,
                CoachMessage.client_id == client.id,
                CoachMessage.sender == "client",
                CoachMessage.read_at.is_(None),
            )
            .count()
        )
        threads.append(
            {
                "client_id": client.id,
                "name": client.name,
                "email": client.email,
                "last_message": last.body if last else None,
                "last_message_at": _iso(last.created_at) if last else None,
                "unread": unread,
            }
        )
    threads.sort(key=lambda t: t["last_message_at"] or "", reverse=True)
    return {"threads": threads, "unread_total": sum(t["unread"] for t in threads)}


@router.post("/messages/broadcast")
def broadcast_message(data: BroadcastIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = get_accessible_team(db, coach, data.team_id)
    clients = db.query(Client).filter(Client.team_id == team.id, Client.status != "inactive").all()
    if not clients:
        raise HTTPException(status_code=400, detail="That team has no active clients")
    now = datetime.utcnow()
    for client in clients:
        db.add(CoachMessage(coach_id=coach.id, client_id=client.id, sender="coach", body=data.body.strip(), created_at=now))
    db.commit()
    return {"sent_to": len(clients)}


@router.get("/messages/{client_id}")
def get_thread(client_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    client = get_managed_client(db, coach, client_id)
    messages = (
        db.query(CoachMessage)
        .filter(CoachMessage.coach_id == coach.id, CoachMessage.client_id == client.id)
        .order_by(CoachMessage.created_at, CoachMessage.id)
        .all()
    )
    return {
        "client": {"id": client.id, "name": client.name, "email": client.email},
        "messages": [_message_payload(m) for m in messages],
    }


@router.post("/messages/{client_id}", status_code=201)
def send_message(
    client_id: int,
    data: MessageIn,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    client = get_managed_client(db, coach, client_id)
    body = data.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    message = CoachMessage(coach_id=coach.id, client_id=client.id, sender="coach", body=body, created_at=datetime.utcnow())
    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_payload(message)


@router.post("/messages/{client_id}/read")
def mark_thread_read(client_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    client = get_managed_client(db, coach, client_id)
    updated = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.coach_id == coach.id,
            CoachMessage.client_id == client.id,
            CoachMessage.sender == "client",
            CoachMessage.read_at.is_(None),
        )
        .update({"read_at": datetime.utcnow()})
    )
    db.commit()
    return {"marked_read": updated}


@router.get("/my/messages")
def my_messages(client: Client = Depends(get_current_client), db: Session = Depends(get_db)):
    messages = (
        db.query(CoachMessage)
        .filter(CoachMessage.client_id == client.id)
        .order_by(CoachMessage.created_at, CoachMessage.id)
        .all()
    )
    coach = db.query(Coach).filter(Coach.id == client.coach_id).first() if client.coach_id else None
    return {
        "coach": {"id": coach.id, "name": coach.name} if coach else None,
        "messages": [_message_payload(m) for m in messages],
        "unread": sum(1 for m in messages if m.sender == "coach" and m.read_at is None),
    }


@router.post("/my/messages", status_code=201)
def send_my_message(data: MessageIn, client: Client = Depends(get_current_client), db: Session = Depends(get_db)):
    if not client.coach_id:
        raise HTTPException(status_code=400, detail="You do not have a coach to message yet")
    body = data.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    message = CoachMessage(
        coach_id=client.coach_id, client_id=client.id, sender="client", body=body, created_at=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_payload(message)


@router.post("/my/messages/read")
def mark_my_messages_read(client: Client = Depends(get_current_client), db: Session = Depends(get_db)):
    updated = (
        db.query(CoachMessage)
        .filter(CoachMessage.client_id == client.id, CoachMessage.sender == "coach", CoachMessage.read_at.is_(None))
        .update({"read_at": datetime.utcnow()})
    )
    db.commit()
    return {"marked_read": updated}


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------
class TeamIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    sport: Optional[str] = Field(default=None, max_length=80)
    level: Optional[str] = Field(default=None, max_length=80)
    organization: Optional[str] = Field(default=None, max_length=120)
    season: Optional[str] = Field(default=None, max_length=80)


class ClientTeamIn(BaseModel):
    team_id: Optional[int] = None


def _team_payload(db: Session, team: Team, coach: Coach) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "sport": team.sport,
        "level": team.level,
        "organization": team.organization,
        "season": team.season,
        "role": "owner" if team.coach_id == coach.id else "member",
        "client_count": db.query(Client).filter(Client.team_id == team.id, Client.status != "inactive").count(),
    }


@router.get("/teams")
def list_teams(coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    ids = accessible_team_ids(db, coach.id)
    teams = db.query(Team).filter(Team.id.in_(ids)).order_by(Team.name).all() if ids else []
    return {"teams": [_team_payload(db, team, coach) for team in teams]}


@router.post("/teams", status_code=201)
def create_team(data: TeamIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = Team(coach_id=coach.id, is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), **data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return _team_payload(db, team, coach)


@router.put("/teams/{team_id}")
def update_team(team_id: int, data: TeamIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = get_accessible_team(db, coach, team_id, owner_only=True)
    for key, value in data.model_dump().items():
        setattr(team, key, value)
    team.updated_at = datetime.utcnow()
    db.commit()
    return _team_payload(db, team, coach)


@router.delete("/teams/{team_id}")
def deactivate_team(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = get_accessible_team(db, coach, team_id, owner_only=True)
    team.is_active = False
    team.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "deactivated", "id": team.id}


@router.get("/teams/{team_id}/roster")
def team_roster(team_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    team = get_accessible_team(db, coach, team_id)
    clients = db.query(Client).filter(Client.team_id == team.id, Client.status != "inactive").order_by(Client.name).all()
    activity = activity_by_email(db, [c.email for c in clients])
    return {
        "team": _team_payload(db, team, coach),
        "clients": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "position": c.position,
                "status": (c.status or "active").title(),
                "joinDate": c.created_at.date().isoformat() if c.created_at else None,
                **activity.get(c.email, {}),
            }
            for c in clients
        ],
    }


@router.post("/clients/{client_id}/team")
def assign_client_team(
    client_id: int,
    data: ClientTeamIn,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    client = get_managed_client(db, coach, client_id)
    if data.team_id is not None:
        get_accessible_team(db, coach, data.team_id)
    client.team_id = data.team_id
    client.updated_at = datetime.utcnow()
    db.commit()
    return {"id": client.id, "team_id": client.team_id}


class CoachInviteIn(BaseModel):
    email: EmailStr
    role: str = "assistant_coach"


@router.post("/teams/{team_id}/coach-invitations", status_code=201)
def invite_team_coach(
    team_id: int,
    data: CoachInviteIn,
    coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db),
):
    team = get_accessible_team(db, coach, team_id, owner_only=True)
    if data.role not in COACH_INVITE_ROLES:
        raise HTTPException(status_code=400, detail="Invalid coach role")
    invite = Invite(
        coach_id=coach.id,
        team_id=team.id,
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
    try:
        delivered = send_coach_invitation(invite.email, invite.token)
    except Exception:
        delivered = False
    return {"invite_id": invite.id, "delivery_configured": delivered, "invite_token": invite.token}


# ---------------------------------------------------------------------------
# Drills
# ---------------------------------------------------------------------------
class DrillIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: Optional[str] = Field(default=None, max_length=60)
    difficulty: str = Field(default="medium", max_length=20)
    equipment: Optional[str] = Field(default=None, max_length=200)
    instructions: Optional[str] = Field(default=None, max_length=4000)
    video_url: Optional[str] = Field(default=None, max_length=500)


def _drill_payload(drill: Drill) -> dict:
    return {
        "id": drill.id,
        "name": drill.name,
        "category": drill.category,
        "difficulty": drill.difficulty,
        "equipment": drill.equipment,
        "instructions": drill.instructions,
        "video_url": drill.video_url,
    }


def _own_drill(db: Session, coach: Coach, drill_id: int) -> Drill:
    drill = db.query(Drill).filter(Drill.id == drill_id, Drill.is_active.is_(True)).first()
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found")
    if drill.coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You do not have access to that drill")
    return drill


@router.get("/drills")
def list_drills(coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    drills = db.query(Drill).filter(Drill.coach_id == coach.id, Drill.is_active.is_(True)).order_by(Drill.name).all()
    return {"drills": [_drill_payload(d) for d in drills]}


@router.post("/drills", status_code=201)
def create_drill(data: DrillIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    drill = Drill(coach_id=coach.id, is_active=True, created_at=datetime.utcnow(), updated_at=datetime.utcnow(), **data.model_dump())
    db.add(drill)
    db.commit()
    db.refresh(drill)
    return _drill_payload(drill)


@router.put("/drills/{drill_id}")
def update_drill(drill_id: int, data: DrillIn, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    drill = _own_drill(db, coach, drill_id)
    for key, value in data.model_dump().items():
        setattr(drill, key, value)
    drill.updated_at = datetime.utcnow()
    db.commit()
    return _drill_payload(drill)


@router.delete("/drills/{drill_id}")
def delete_drill(drill_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    drill = _own_drill(db, coach, drill_id)
    drill.is_active = False
    drill.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "deleted", "id": drill.id}


# ---------------------------------------------------------------------------
# Pending invitations
# ---------------------------------------------------------------------------
@router.get("/invitations")
def list_invitations(coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    invites = db.query(Invite).filter(Invite.coach_id == coach.id).order_by(Invite.created_at.desc()).all()
    now = datetime.utcnow()
    return {
        "invitations": [
            {
                "id": i.id,
                "email": i.email,
                "role": i.role,
                "team_id": i.team_id,
                "accepted": bool(i.accepted),
                "expired": bool(i.expires_at and i.expires_at < now),
                "created_at": _iso(i.created_at),
            }
            for i in invites
        ]
    }


@router.delete("/invitations/{invite_id}")
def revoke_invitation(invite_id: int, coach: Coach = Depends(get_current_coach), db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invite.coach_id != coach.id:
        raise HTTPException(status_code=403, detail="You did not create that invitation")
    if invite.accepted:
        raise HTTPException(status_code=400, detail="That invitation was already accepted")
    db.delete(invite)
    db.commit()
    return {"status": "revoked"}
