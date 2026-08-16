from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, data: UserCreate) -> User:
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=data.hashed_password,
        role=data.role,
        active=data.active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session) -> List[User]:
    return db.query(User).all()


def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
    user = get_user(db, user_id)
    if not user:
        return None

    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True
