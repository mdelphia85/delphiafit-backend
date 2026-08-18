from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.announcements import Announcement
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/announcements", tags=["Admin Announcements"])


class AnnouncementCreate(BaseModel):
    title: str
    body: str | None = None
    message: str | None = None


def _payload(announcement: Announcement) -> dict:
    return {
        "id": announcement.id,
        "title": announcement.title,
        "body": announcement.message,
        "message": announcement.message,
        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
    }


@router.get("")
def get_announcements(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [_payload(item) for item in announcements]


@router.post("")
@router.post("/")
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    message = data.body or data.message
    if not data.title.strip() or not message or not message.strip():
        raise HTTPException(status_code=400, detail="Title and body are required")
    announcement = Announcement(title=data.title.strip(), message=message.strip(), created_at=datetime.utcnow())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return _payload(announcement)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    db.delete(announcement)
    db.commit()
    return {"status": "deleted", "id": announcement_id}
