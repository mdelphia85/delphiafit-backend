from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.announcements import Announcement


def create_announcement(db: Session, data: dict) -> Announcement:
    announcement = Announcement(**data)
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def get_announcement(db: Session, announcement_id: int) -> Optional[Announcement]:
    return db.query(Announcement).filter(Announcement.id == announcement_id).first()


def get_announcements(db: Session) -> List[Announcement]:
    return db.query(Announcement).all()


def update_announcement(db: Session, announcement_id: int, data: dict) -> Optional[Announcement]:
    announcement = get_announcement(db, announcement_id)
    if not announcement:
        return None

    for field, value in data.items():
        setattr(announcement, field, value)

    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, announcement_id: int) -> bool:
    announcement = get_announcement(db, announcement_id)
    if not announcement:
        return False

    db.delete(announcement)
    db.commit()
    return True
