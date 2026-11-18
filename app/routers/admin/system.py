from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.logs import AdminAuditLog
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin", tags=["Admin System"])
_STARTED_AT = datetime.utcnow()


@router.get("/system/health")
def system_health(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"
    uptime_seconds = max(0, int((datetime.utcnow() - _STARTED_AT).total_seconds()))
    hours, rem = divmod(uptime_seconds, 3600)
    minutes, _ = divmod(rem, 60)

    failed_24h = 0
    if database_status == "ok":
        failed_24h = (
            db.query(AdminAuditLog)
            .filter(
                AdminAuditLog.success.is_(False),
                AdminAuditLog.created_at >= datetime.utcnow() - timedelta(hours=24),
            )
            .count()
        )
    return {
        "api_status": "ok",
        "database_status": database_status,
        "uptime": f"{hours}h {minutes}m",
        "uptime_seconds": uptime_seconds,
        "failed_admin_actions_24h": failed_24h,
    }


@router.get("/actions/recent")
def recent_admin_actions(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    rows = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc()).limit(25).all()
    return {
        "actions": [
            {
                "id": row.id,
                "action": row.action,
                "summary": row.action + (f" {row.target_type}#{row.target_id}" if row.target_type else ""),
                "detail": row.detail,
                "admin": row.admin_email,
                "success": bool(row.success),
                "timestamp": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }
