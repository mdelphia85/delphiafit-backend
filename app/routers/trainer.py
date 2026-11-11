"""Personal-trainer client management, independent of Coach Hub.

Clients must explicitly accept trainer invitations before the trainer can see
their saved workout information. Ownership is checked server-side.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.trainer import TrainerClientLink, TrainerProfile
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.services.email_delivery import send_trainer_invitation

router = APIRouter(prefix="/trainer", tags=["Personal Trainer"])


class ClientInvitation(BaseModel):
    email: EmailStr


def _user(payload: dict, db: Session) -> User:
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or user.is_suspended:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user session")
    return user


def _trainer(payload: dict, db: Session) -> User:
    user = _user(payload, db)
    trainer = db.query(TrainerProfile).filter(
        TrainerProfile.user_id == user.id,
        TrainerProfile.is_active.is_(True),
    ).first()
    if trainer is None:
        raise HTTPException(status_code=403, detail="Personal trainer access required")
    return user


@router.get("/me")
def trainer_me(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    has_role = db.query(TrainerProfile.id).filter(
        TrainerProfile.user_id == user.id,
        TrainerProfile.is_active.is_(True),
    ).first() is not None
    return {"is_trainer": has_role}


@router.get("/clients")
def list_clients(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    trainer = _trainer(payload, db)
    rows = (
        db.query(TrainerClientLink, User)
        .join(User, User.id == TrainerClientLink.client_user_id)
        .filter(TrainerClientLink.trainer_user_id == trainer.id)
        .order_by(TrainerClientLink.invited_at.desc(), TrainerClientLink.id.desc())
        .all()
    )
    return {
        "clients": [
            {"id": client.id, "name": client.name, "email": client.email, "status": link.status}
            for link, client in rows
        ]
    }


@router.post("/clients/invite", status_code=201)
def invite_client(data: ClientInvitation, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    trainer = _trainer(payload, db)
    email = str(data.email).strip()
    client = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if client is None:
        raise HTTPException(status_code=404, detail="The client needs a DelphiaFit account before an invitation can be sent.")
    if client.id == trainer.id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself.")

    link = db.query(TrainerClientLink).filter(
        TrainerClientLink.trainer_user_id == trainer.id,
        TrainerClientLink.client_user_id == client.id,
    ).first()
    if link:
        if link.status == "active":
            raise HTTPException(status_code=409, detail="This person is already your client.")
        return {"status": "pending", "message": "Invitation is already pending.", "delivery_configured": False}

    link = TrainerClientLink(trainer_user_id=trainer.id, client_user_id=client.id, status="pending")
    db.add(link)
    db.commit()
    delivered = False
    try:
        delivered = bool(send_trainer_invitation(client.email, trainer.name))
    except Exception:
        pass
    return {
        "status": "pending",
        "delivery_configured": delivered,
        "message": "Invitation pending. The client must accept it from My Trainer before any workout history is shared.",
    }


@router.get("/invitations")
def list_invitations(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    rows = (
        db.query(TrainerClientLink, User)
        .join(User, User.id == TrainerClientLink.trainer_user_id)
        .filter(TrainerClientLink.client_user_id == user.id, TrainerClientLink.status == "pending")
        .order_by(TrainerClientLink.invited_at.desc())
        .all()
    )
    return {"invitations": [{"id": link.id, "trainer_name": trainer.name} for link, trainer in rows]}


@router.get("/my-trainers")
def list_my_trainers(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    rows = (
        db.query(TrainerClientLink, User)
        .join(User, User.id == TrainerClientLink.trainer_user_id)
        .filter(TrainerClientLink.client_user_id == user.id, TrainerClientLink.status == "active")
        .order_by(TrainerClientLink.accepted_at.desc())
        .all()
    )
    return {"trainers": [{"id": trainer.id, "name": trainer.name} for link, trainer in rows]}


@router.delete("/my-trainers/{trainer_id}")
def disconnect_trainer(trainer_id: int, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    link = db.query(TrainerClientLink).filter(
        TrainerClientLink.trainer_user_id == trainer_id,
        TrainerClientLink.client_user_id == user.id,
        TrainerClientLink.status == "active",
    ).first()
    if link is None:
        raise HTTPException(status_code=404, detail="Trainer relationship not found")
    db.delete(link)
    db.commit()
    return {"status": "disconnected"}


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(invitation_id: int, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    link = db.query(TrainerClientLink).filter(
        TrainerClientLink.id == invitation_id,
        TrainerClientLink.client_user_id == user.id,
    ).first()
    if not link or link.status != "pending":
        raise HTTPException(status_code=404, detail="Pending invitation not found")
    link.status = "active"
    link.accepted_at = datetime.utcnow()
    db.commit()
    return {"status": "active"}


@router.post("/invitations/{invitation_id}/decline")
def decline_invitation(invitation_id: int, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _user(payload, db)
    link = db.query(TrainerClientLink).filter(
        TrainerClientLink.id == invitation_id,
        TrainerClientLink.client_user_id == user.id,
        TrainerClientLink.status == "pending",
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Pending invitation not found")
    db.delete(link)
    db.commit()
    return {"status": "declined"}


@router.delete("/clients/{client_id}")
def remove_client(client_id: int, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    trainer = _trainer(payload, db)
    link = db.query(TrainerClientLink).filter(
        TrainerClientLink.trainer_user_id == trainer.id,
        TrainerClientLink.client_user_id == client_id,
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(link)
    db.commit()
    return {"status": "removed"}


@router.get("/clients/{client_id}/progress")
def client_progress(client_id: int, payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    trainer = _trainer(payload, db)
    link = db.query(TrainerClientLink.id).filter(
        TrainerClientLink.trainer_user_id == trainer.id,
        TrainerClientLink.client_user_id == client_id,
        TrainerClientLink.status == "active",
    ).first()
    if link is None:
        raise HTTPException(status_code=404, detail="Client not found")

    workouts = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == client_id)
        .order_by(WorkoutLog.date.desc(), WorkoutLog.id.desc())
        .limit(20)
        .all()
    )
    return {"workouts": [
        {
            "id": item.id,
            "name": item.manual_name or item.workout_type or "Workout",
            "date": item.date.isoformat() if item.date else None,
            "duration_minutes": item.duration_minutes,
        }
        for item in workouts
    ]}
