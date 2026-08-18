from typing import List, Optional

from sqlalchemy.orm import Session

from app.auth.hashing import hash_password
from app.database.connection import Base
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, data: UserCreate) -> User:
    user = User(name=data.name, email=data.email, hashed_password=hash_password(data.password))
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
    changes = data.model_dump(exclude_unset=True)
    password = changes.pop("password", None)
    if password:
        user.hashed_password = hash_password(password)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def _delete_unconstrained_user_rows(db: Session, user_id: int) -> None:
    """Remove user-scoped rows that use user_id without a users FK.

    FK-backed rows are handled by ORM cascades on User. This covers legacy/V2
    log tables that historically stored user_id as a plain integer.
    """
    for table in reversed(Base.metadata.sorted_tables):
        if table.name == "users" or "user_id" not in table.c:
            continue
        user_col = table.c.user_id
        points_to_users = any(
            fk.column.table.name == "users" for fk in user_col.foreign_keys
        )
        if not points_to_users:
            db.execute(table.delete().where(user_col == user_id))


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False
    _delete_unconstrained_user_rows(db, user_id)
    db.delete(user)
    db.commit()
    return True
