from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.models.messages import Message
from app.models.user import User
from app.routers.admin.auth import record_audit, verify_admin

# Admin inbox under /admin/messages plus POST /messages for signed-in users to
# contact the team (explicit paths so main.py needs no extra router).
router = APIRouter(tags=["Admin Messages"])


class UserMessageCreate(BaseModel):
    subject: str = "Support request"
    message: str


def _payload(message: Message) -> dict:
    return {
        "id": message.id,
        "name": message.name,
        "email": message.email,
        "subject": message.subject,
        "message": message.message,
        "is_read": bool(message.is_read),
        "resolved": bool(message.is_read),
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def _get(db: Session, message_id: int) -> Message:
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/messages")
def send_message(
    data: UserMessageCreate,
    token_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        user_id = int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id, User.email == token_data.get("email")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    text = data.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message is required")
    message = Message(
        name=user.name,
        email=user.email,
        subject=(data.subject or "Support request").strip()[:200] or "Support request",
        message=text[:5000],
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"status": "sent", "id": message.id}


@router.get("/admin/messages")
def get_messages(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    messages = db.query(Message).order_by(Message.created_at.desc(), Message.id.desc()).all()
    return [_payload(message) for message in messages]


@router.patch("/admin/messages/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = _get(db, message_id)
    message.is_read = True
    db.commit()
    db.refresh(message)
    record_audit(db, admin, "message.mark_read", "message", message_id, message.subject)
    return {"status": "updated", "message": _payload(message)}


@router.patch("/admin/messages/{message_id}/resolve")
def toggle_message_resolved(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = _get(db, message_id)
    message.is_read = not bool(message.is_read)
    db.commit()
    db.refresh(message)
    record_audit(
        db, admin, "message.resolve" if message.is_read else "message.unresolve",
        "message", message_id, message.subject,
    )
    return {"status": "updated", "message": _payload(message)}


@router.delete("/admin/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = _get(db, message_id)
    subject = message.subject
    db.delete(message)
    db.commit()
    record_audit(db, admin, "message.delete", "message", message_id, subject)
    return {"status": "deleted", "id": message_id}
