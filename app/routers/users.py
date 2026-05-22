from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------
# GET ALL USERS (ADMIN)
# ---------------------------------------------------------
@router.get("/", response_model=list[UserResponse])
def get_all_users(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    # Optional: restrict to admin later
    users = db.query(User).all()
    return users


# ---------------------------------------------------------
# GET SINGLE USER BY ID
# ---------------------------------------------------------
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# ---------------------------------------------------------
# UPDATE USER
# ---------------------------------------------------------
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated: UserCreate,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = updated.name
    user.email = updated.email
    user.hashed_password = user.hashed_password  # password updates handled elsewhere

    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------------
# DELETE USER
# ---------------------------------------------------------
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"detail": "User deleted successfully"}
