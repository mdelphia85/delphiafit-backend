from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/messages", tags=["Admin Messages"])


@router.get("/")
def get_messages(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    try:
        from app.models.messages import Message
    except:
        raise HTTPException(status_code=500, detail="Message model not found")

    return db.query(Message).order_by(Message.created_at.desc()).all()


@router.patch("/{message_id}/read")
def mark_message_read(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    from app.models.messages import Message

    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.is_read = True
    db.commit()
    db.refresh(msg)

    return {"status": "updated", "message": msg}


@router.delete("/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    from app.models.messages import Message

    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(msg)
    db.commit()

    return {"status": "deleted", "id": message_id}
