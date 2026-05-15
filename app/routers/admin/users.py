from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.admin.auth import verify_admin

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("/")
def get_all_users(db: Session = Depends(get_db), admin=Depends(verify_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/reset-streak")
def reset_streak(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.streak = 0
    db.commit()
    db.refresh(user)

    return {"status": "success", "user": user}


@router.patch("/{user_id}/admin")
def toggle_admin(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)

    return {"status": "success", "user": user}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(verify_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"status": "deleted", "id": user_id}
