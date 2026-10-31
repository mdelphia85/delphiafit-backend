from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.community_area import AcademyProgress, ChildProfile, ChildProgress, RecruitingProfile, SocialFollow
from app.models.user import User
from app.utils.security import get_current_user_id

router = APIRouter(tags=["community features"])


class AcademyProgressInput(BaseModel):
    sport: str = Field(min_length=1, max_length=80)
    drill: str = Field(min_length=1, max_length=160)
    completed: bool


class RecruitingProfileInput(BaseModel):
    sport: str = Field(min_length=1, max_length=80)
    position: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=2000)
    public: bool = False


class ChildInput(BaseModel):
    nickname: str = Field(min_length=1, max_length=40)
    parent_controls_enabled: bool = True


class ChildProgressInput(BaseModel):
    activity_key: str = Field(min_length=1, max_length=80)
    completed: bool


@router.get("/sports-academy/progress")
def list_academy_progress(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = db.query(AcademyProgress).filter_by(user_id=user_id).all()
    return [{"sport": row.sport, "drill": row.drill, "completed": row.completed} for row in rows]


@router.put("/sports-academy/progress")
def save_academy_progress(data: AcademyProgressInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(AcademyProgress).filter_by(user_id=user_id, sport=data.sport.strip(), drill=data.drill.strip()).first()
    if row is None:
        row = AcademyProgress(user_id=user_id, sport=data.sport.strip(), drill=data.drill.strip())
        db.add(row)
    row.completed = data.completed
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"sport": row.sport, "drill": row.drill, "completed": row.completed}


@router.get("/recruiting/profiles")
def browse_recruiting_profiles(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = db.query(RecruitingProfile, User.name).join(User, User.id == RecruitingProfile.user_id).filter(RecruitingProfile.public.is_(True)).order_by(User.name).all()
    return [{"user_id": row.user_id, "name": name, "sport": row.sport, "position": row.position, "bio": row.bio}
            for row, name in rows]


@router.get("/recruiting/profile")
def get_own_recruiting_profile(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(RecruitingProfile).filter_by(user_id=user_id).first()
    if row is None:
        return None
    return {"user_id": row.user_id, "sport": row.sport, "position": row.position, "bio": row.bio, "public": row.public}


@router.put("/recruiting/profile")
def save_recruiting_profile(data: RecruitingProfileInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(RecruitingProfile).filter_by(user_id=user_id).first()
    if row is None:
        row = RecruitingProfile(user_id=user_id, sport=data.sport.strip())
        db.add(row)
    row.sport = data.sport.strip()
    row.position = data.position.strip() if data.position else None
    row.bio = data.bio.strip() if data.bio else None
    row.public = data.public
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"user_id": row.user_id, "sport": row.sport, "position": row.position, "bio": row.bio, "public": row.public}


@router.get("/kids/children")
def list_children(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = db.query(ChildProfile).filter_by(parent_user_id=user_id).order_by(ChildProfile.id).all()
    return [{"id": row.id, "nickname": row.nickname, "parent_controls_enabled": row.parent_controls_enabled,
             "progress": [{"activity_key": p.activity_key, "completed": p.completed}
                          for p in db.query(ChildProgress).filter_by(child_id=row.id).all()]} for row in rows]


@router.post("/kids/children")
def create_child(data: ChildInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = ChildProfile(parent_user_id=user_id, nickname=data.nickname.strip(), parent_controls_enabled=data.parent_controls_enabled)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "nickname": row.nickname, "parent_controls_enabled": row.parent_controls_enabled, "progress": []}


def _own_child(db: Session, user_id: int, child_id: int):
    row = db.query(ChildProfile).filter_by(id=child_id, parent_user_id=user_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Child profile not found")
    return row


@router.patch("/kids/children/{child_id}")
def update_child(child_id: int, data: ChildInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = _own_child(db, user_id, child_id)
    row.nickname = data.nickname.strip()
    row.parent_controls_enabled = data.parent_controls_enabled
    db.commit()
    return {"id": row.id, "nickname": row.nickname, "parent_controls_enabled": row.parent_controls_enabled}


@router.put("/kids/children/{child_id}/progress")
def save_child_progress(child_id: int, data: ChildProgressInput, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    _own_child(db, user_id, child_id)
    row = db.query(ChildProgress).filter_by(child_id=child_id, activity_key=data.activity_key.strip()).first()
    if row is None:
        row = ChildProgress(child_id=child_id, activity_key=data.activity_key.strip())
        db.add(row)
    row.completed = data.completed
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"activity_key": row.activity_key, "completed": row.completed}


@router.get("/community/profiles")
def list_community_profiles(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    rows = db.query(User.id, User.name).filter(User.id != user_id, User.is_suspended.is_(False)).order_by(User.name).limit(100).all()
    followed = {r.followed_id for r in db.query(SocialFollow).filter_by(follower_id=user_id).all()}
    return [{"id": row.id, "name": row.name, "following": row.id in followed} for row in rows]


@router.post("/community/follows/{target_user_id}")
def follow_user(target_user_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if target_user_id == user_id or not db.query(User).filter_by(id=target_user_id, is_suspended=False).first():
        raise HTTPException(status_code=404, detail="Profile not found")
    row = db.query(SocialFollow).filter_by(follower_id=user_id, followed_id=target_user_id).first()
    if row is None:
        db.add(SocialFollow(follower_id=user_id, followed_id=target_user_id))
        db.commit()
    return {"following": True}


@router.delete("/community/follows/{target_user_id}")
def unfollow_user(target_user_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    row = db.query(SocialFollow).filter_by(follower_id=user_id, followed_id=target_user_id).first()
    if row:
        db.delete(row)
        db.commit()
    return {"following": False}
