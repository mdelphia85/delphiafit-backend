from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_access_token
from app.database.connection import get_db
from app.models.announcements import Announcement
from app.routers.admin.auth import record_audit, verify_admin

# Admin management lives under /admin/announcements; the read-only feed for
# signed-in users is GET /announcements (same router, explicit paths).
router = APIRouter(tags=["Announcements"])


class AnnouncementCreate(BaseModel):
    title: str
    body: str | None = None
    message: str | None = None
    published: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    message: str | None = None
    published: bool | None = None


class PublishBody(BaseModel):
    published: bool | None = None


def _iso(value):
    return value.isoformat() if value else None


def _payload(announcement: Announcement) -> dict:
    return {
        "id": announcement.id,
        "title": announcement.title,
        "body": announcement.message,
        "message": announcement.message,
        "is_active": bool(announcement.is_active),
        "published": bool(announcement.is_active),
        "created_at": _iso(announcement.created_at),
        "published_at": _iso(announcement.published_at),
        "updated_at": _iso(announcement.updated_at),
    }


def _get(db: Session, announcement_id: int) -> Announcement:
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.get("/announcements")
def list_active_announcements(
    db: Session = Depends(get_db),
    token_data: dict = Depends(decode_access_token),
):
    rows = (
        db.query(Announcement)
        .filter(Announcement.is_active.is_(True))
        .order_by(Announcement.created_at.desc(), Announcement.id.desc())
        .all()
    )
    return [
        {"id": a.id, "title": a.title, "body": a.message, "message": a.message,
         "created_at": _iso(a.created_at), "published_at": _iso(a.published_at)}
        for a in rows
    ]


@router.get("/admin/announcements")
def get_announcements(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    rows = db.query(Announcement).order_by(Announcement.created_at.desc(), Announcement.id.desc()).all()
    return [_payload(item) for item in rows]


@router.post("/admin/announcements")
@router.post("/admin/announcements/")
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    message = data.body or data.message
    if not data.title.strip() or not message or not message.strip():
        raise HTTPException(status_code=400, detail="Title and body are required")
    now = datetime.utcnow()
    announcement = Announcement(
        title=data.title.strip(),
        message=message.strip(),
        created_at=now,
        is_active=data.published,
        published_at=now if data.published else None,
        created_by=admin["admin_id"],
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    record_audit(
        db, admin, "announcement.create", "announcement", announcement.id,
        f"{announcement.title} ({'published' if data.published else 'draft'})",
    )
    return _payload(announcement)


@router.put("/admin/announcements/{announcement_id}")
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    announcement = _get(db, announcement_id)
    if data.title is not None:
        if not data.title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        announcement.title = data.title.strip()
    message = data.body if data.body is not None else data.message
    if message is not None:
        if not message.strip():
            raise HTTPException(status_code=400, detail="Body cannot be empty")
        announcement.message = message.strip()
    if data.published is not None and data.published != bool(announcement.is_active):
        announcement.is_active = data.published
        if data.published:
            announcement.published_at = datetime.utcnow()
    announcement.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(announcement)
    record_audit(db, admin, "announcement.update", "announcement", announcement.id, announcement.title)
    return _payload(announcement)


@router.patch("/admin/announcements/{announcement_id}/publish")
def publish_announcement(
    announcement_id: int,
    body: PublishBody | None = None,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    announcement = _get(db, announcement_id)
    target = body.published if body and body.published is not None else not announcement.is_active
    announcement.is_active = target
    if target:
        announcement.published_at = datetime.utcnow()
    announcement.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(announcement)
    record_audit(
        db, admin, "announcement.publish" if target else "announcement.unpublish",
        "announcement", announcement.id, announcement.title,
    )
    return _payload(announcement)


@router.delete("/admin/announcements/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    admin=Depends(verify_admin),
):
    announcement = _get(db, announcement_id)
    title = announcement.title
    db.delete(announcement)
    db.commit()
    record_audit(db, admin, "announcement.delete", "announcement", announcement_id, title)
    return {"status": "deleted", "id": announcement_id}
