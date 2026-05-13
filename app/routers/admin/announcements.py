from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models.announcements import Announcement
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/announcements", tags=["Admin Announcements"])


# -----------------------------
# GET ALL ANNOUNCEMENTS
# -----------------------------
@router.get("/")
def get_announcements(
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    announcements = (
        db.query(Announcement)
        .order_by(Announcement.created_at.desc())
        .all()
    )
    return announcements


# -----------------------------
# CREATE ANNOUNCEMENT
# -----------------------------
@router.post("/")
def create_announcement(
    data: dict,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    title = data.get("title")
    message = data.get("message")

    if not title or not message:
        raise HTTPException(status_code=400, detail="Title and message are required")

    new_announcement = Announcement(
        title=title,
        message=message,
        created_at=datetime.utcnow()
    )

    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)

    return {"status": "success", "announcement": new_announcement}


# -----------------------------
# DELETE ANNOUNCEMENT
# -----------------------------
@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin)
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    db.delete(announcement)
    db.commit()

    return {"status": "deleted", "id": announcement_id}
