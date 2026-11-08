from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.hashing import verify_password
from app.auth.errors import authentication_database_error
from app.auth.jwt_handler import create_access_token, get_active_access_token
from app.database.connection import get_db
from app.models.login_log import LoginLog
from app.models.logs import AdminAuditLog
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


class AdminLogin(BaseModel):
    email: str
    password: str


def record_audit(
    db: Session,
    admin: dict | None,
    action: str,
    target_type: str | None = None,
    target_id=None,
    detail: str | None = None,
    success: bool = True,
) -> AdminAuditLog:
    """Persist an audit entry. `admin` is the dict returned by verify_admin."""
    entry = AdminAuditLog(
        admin_id=admin.get("admin_id") if admin else None,
        admin_email=admin.get("admin_email") if admin else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        detail=detail,
        success=success,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    return entry


@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    email = data.email.strip()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()

    if not user or not verify_password(data.password, user.hashed_password):
        record_audit(
            db, {"admin_email": email}, "admin.login_failed",
            detail="Invalid credentials", success=False,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    admin_ctx = {"admin_id": user.id, "admin_email": user.email}
    if not user.is_admin:
        record_audit(db, admin_ctx, "admin.login_denied", detail="Not an admin", success=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    if user.is_suspended:
        record_audit(db, admin_ctx, "admin.login_denied", detail="Account suspended", success=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "is_admin": True,
        "token_version": user.token_version,
    })
    db.add(LoginLog(user_id=user.id, timestamp=datetime.utcnow()))
    db.commit()
    record_audit(db, admin_ctx, "admin.login")

    return {"access_token": token, "token_type": "bearer"}


def verify_admin(
    request: Request,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
) -> dict:
    """Require a valid token whose user currently has is_admin set in the database.

    Returns the token claims plus `admin_id` / `admin_email` for audit logging.
    """
    if token_data.get("actor_type") not in (None, "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    try:
        user_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")

    try:
        user = db.query(User).filter(User.id == user_id).first()
    except Exception as exc:
        raise authentication_database_error(db, request, "administrator token validation", exc) from None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    if not token_data.get("is_admin") or not user.is_admin or user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return {**token_data, "admin_id": user.id, "admin_email": user.email}


@router.get("/me")
def admin_me(admin: dict = Depends(verify_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == admin["admin_id"]).first()
    return {"id": user.id, "email": user.email, "name": user.name, "is_admin": True}
