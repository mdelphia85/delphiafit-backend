from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.models.user import User
from app.models.announcements import Announcement
from app.routers.admin.auth import verify_admin   # <-- ADD THIS

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get("/")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)   # <-- PROTECT ROUTE
):
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    # Total users
    total_users = db.query(User).count()

    # New users in last 7 days
    new_users_last_7_days = (
        db.query(User)
        .filter(User.created_at >= week_ago)
        .count()
    )

    # Total announcements
    total_announcements = db.query(Announcement).count()

    # Unread messages (if Message model exists)
    try:
        from app.models.messages import Message
        unread_messages = db.query(Message).filter(Message.is_read == False).count()
    except Exception:
        unread_messages = 0

    # Error / activity logs (if Log model exists)
    try:
        from app.models.logs import LogEntry
        total_logs = db.query(LogEntry).count()
    except Exception:
        total_logs = 0

    return {
        "total_users": total_users,
        "new_users_last_7_days": new_users_last_7_days,
        "total_announcements": total_announcements,
        "unread_messages": unread_messages,
        "total_logs": total_logs,
        "server_time_utc": datetime.utcnow().isoformat()
    }
