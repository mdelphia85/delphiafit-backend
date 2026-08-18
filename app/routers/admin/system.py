from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
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
    return {
        "api_status": "ok",
        "database_status": database_status,
        "uptime": f"{hours}h {minutes}m",
        "errors_24h": 0,
    }


@router.get("/actions/recent")
def recent_admin_actions(admin=Depends(verify_admin)):
    # Action persistence was never modeled in the generated backend. Keep the
    # frontend contract stable until an audit-log table is introduced.
    return {"actions": []}
