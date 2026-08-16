from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.posts import Post


def create_post(db: Session, data: dict) -> Post:
    post = Post(**data)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: int) -> Optional[Post]:
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts(db: Session) -> List[Post]:
    return db.query(Post).all()


def update_post(db: Session, post_id: int, data: dict) -> Optional[Post]:
    post = get_post(db, post_id)
    if not post:
        return None

    for field, value in data.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: int) -> bool:
    post = get_post(db, post_id)
    if not post:
        return False

    db.delete(post)
    db.commit()
    return True
