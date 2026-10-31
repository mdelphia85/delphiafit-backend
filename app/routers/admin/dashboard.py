from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.announcements import Announcement
from app.models.daily_log import DailyLog
from app.models.login_log import LoginLog
from app.models.logs import AdminAuditLog
from app.models.messages import Message
from app.models.sports_log import SportsLog
from app.models.user import User
from app.models.workout_log import WorkoutLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


def count_all_logs(db: Session) -> int:
    """Total rows across every source shown in the admin System Logs view."""
    return sum(
        db.query(model).count()
        for model in (WorkoutLog, DailyLog, SportsLog, LoginLog, AdminAuditLog)
    )


@router.get("")
def get_admin_dashboard(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # users.created_at is stored in UTC (server default now()).
    new_users = db.query(User).filter(User.created_at >= week_ago).count()
    unread = db.query(Message).filter(or_(Message.is_read.is_(False), Message.is_read.is_(None))).count()

    return {
        "total_users": db.query(User).count(),
        "new_users_last_7_days": new_users,
        "total_admins": db.query(User).filter(User.is_admin.is_(True)).count(),
        "suspended_users": db.query(User).filter(User.is_suspended.is_(True)).count(),
        "total_announcements": db.query(Announcement).count(),
        "active_announcements": db.query(Announcement).filter(Announcement.is_active.is_(True)).count(),
        "unread_messages": unread,
        "logins_last_7_days": db.query(LoginLog).filter(LoginLog.timestamp >= week_ago).count(),
        "total_logs": count_all_logs(db),
        "server_time_utc": now.isoformat(),
    }
