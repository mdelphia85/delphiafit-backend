from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from sqlalchemy import func
from app.models.sports_log import SportsLog
from app.models.user import User

from app.database.connection import get_db
from app.utils.security import get_current_user_id

from app.schemas.sports_log import (
    SportsLogCreate,
    SportsLogRead
)
from app.crud.sports_log import (
    create_sports_log,
    get_sports_logs
)

router = APIRouter(prefix="/sports/logs", tags=["sports logs"])


@router.get("/leaderboard")
def sports_leaderboard(
    period: str = "weekly",
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if period not in {"weekly", "monthly", "alltime"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="period must be weekly, monthly, or alltime")
    query = db.query(
        User.id.label("user_id"),
        User.name.label("name"),
        func.sum(SportsLog.duration_minutes).label("minutes"),
        func.count(SportsLog.id).label("sessions"),
    ).join(SportsLog, SportsLog.user_id == User.id)
    if period != "alltime":
        days = 7 if period == "weekly" else 30
        query = query.filter(SportsLog.date >= datetime.utcnow() - timedelta(days=days))
    rows = query.group_by(User.id, User.name).order_by(func.sum(SportsLog.duration_minutes).desc(), User.id).limit(100).all()
    return [{"rank": index + 1, "user_id": row.user_id, "name": row.name,
             "minutes": int(row.minutes or 0), "sessions": int(row.sessions or 0)}
            for index, row in enumerate(rows)]

@router.post("/", response_model=SportsLogRead)
def add_sports_log(
    payload: SportsLogCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return create_sports_log(db, user_id, payload)

@router.get("/", response_model=List[SportsLogRead])
def list_sports_logs(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return get_sports_logs(db, user_id)
