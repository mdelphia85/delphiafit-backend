"""Authenticated account management: change password, data export, delete account, notification prefs."""
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.crud.user import delete_user as delete_user_record
from app.database.connection import Base, get_db
from app.models.user import User
from app.models.user_data_record import UserDataRecord
from app.services.email_delivery import _send_email
from app.utils.security import get_current_user_id

router = APIRouter(prefix="/account", tags=["account"])

NOTIFICATION_COLLECTION = "notification_prefs"
NOTIFICATION_DEFAULTS = {"workout_summaries": False, "weekly_reports": False, "product_updates": False}
# Tables never included in a user's export (security/telemetry, not user content).
EXPORT_EXCLUDED = {"login_logs", "user_devices", "offline_sync"}
# Tables whose rows are removed through ORM cascades on User (content shared with other users).
DELETE_VIA_CASCADE = {"posts", "comments", "reactions", "group_members"}


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10)


class DeleteAccount(BaseModel):
    confirm: str
    password: str


class NotificationPrefs(BaseModel):
    workout_summaries: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    product_updates: Optional[bool] = None


def _current_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def _delivery_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


@router.post("/change-password")
def change_password(
    payload: ChangePassword,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = _current_user(db, user_id)
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(status_code=400, detail="New password must differ from the current password")
    user.hashed_password = hash_password(payload.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()
    return {"detail": "Password updated"}


@router.get("/export")
def export_data(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = _current_user(db, user_id)
    data = {
        "account": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
        },
        "records": {},
    }
    for table in Base.metadata.sorted_tables:
        if table.name == "users" or table.name in EXPORT_EXCLUDED or "user_id" not in table.c:
            continue
        rows = db.execute(table.select().where(table.c.user_id == user_id)).mappings().all()
        if rows:
            data["records"][table.name] = [dict(row) for row in rows]
    return jsonable_encoder(data)


@router.delete("")
def delete_account(
    payload: DeleteAccount,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = _current_user(db, user_id)
    if payload.confirm != "DELETE":
        raise HTTPException(status_code=400, detail='Type "DELETE" to confirm account deletion')
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    for table in reversed(Base.metadata.sorted_tables):
        if table.name == "users" or table.name in DELETE_VIA_CASCADE or "user_id" not in table.c:
            continue
        db.execute(table.delete().where(table.c.user_id == user_id))
    db.flush()
    if not delete_user_record(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "Account deleted"}


def _prefs_record(db: Session, user_id: int) -> Optional[UserDataRecord]:
    return (
        db.query(UserDataRecord)
        .filter(UserDataRecord.user_id == user_id, UserDataRecord.collection == NOTIFICATION_COLLECTION)
        .first()
    )


def _prefs_response(record: Optional[UserDataRecord]) -> dict:
    prefs = {**NOTIFICATION_DEFAULTS, **((record.data or {}) if record else {})}
    return {
        "preferences": prefs,
        "delivery_configured": _delivery_configured(),
        "delivery_note": None
        if _delivery_configured()
        else "Email delivery is not configured on this server, so notifications are saved but not sent.",
    }


@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return _prefs_response(_prefs_record(db, user_id))


@router.put("/notifications")
def update_notifications(
    payload: NotificationPrefs,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    record = _prefs_record(db, user_id)
    changes = payload.model_dump(exclude_none=True)
    if record is None:
        record = UserDataRecord(user_id=user_id, collection=NOTIFICATION_COLLECTION, data=changes)
        db.add(record)
    else:
        record.data = {**(record.data or {}), **changes}
    db.commit()
    db.refresh(record)
    return _prefs_response(record)


@router.post("/notifications/test")
def send_test_notification(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = _current_user(db, user_id)
    if not _delivery_configured():
        return {"sent": False, "delivery_configured": False}
    try:
        sent = _send_email(user.email, "DelphiaFit notification test", "Email notifications are working.")
    except Exception:
        sent = False
    return {"sent": sent, "delivery_configured": True}
