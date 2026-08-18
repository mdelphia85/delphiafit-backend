from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.messages import Message
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/messages", tags=["Admin Messages"])


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


@router.get("")
def get_messages(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    messages = db.query(Message).order_by(Message.created_at.desc()).all()
    return [_payload(message) for message in messages]


@router.patch("/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = True
    db.commit()
    db.refresh(message)
    return {"status": "updated", "message": _payload(message)}


@router.patch("/{message_id}/resolve")
def toggle_message_resolved(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = not bool(message.is_read)
    db.commit()
    db.refresh(message)
    return {"status": "updated", "message": _payload(message)}


@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()
    return {"status": "deleted", "id": message_id}
