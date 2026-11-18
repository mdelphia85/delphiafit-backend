from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import get_active_access_token
from app.routers.admin.auth import verify_admin
from app.crud.user import StaleUserCredentials
from app.crud.user import delete_user as delete_user_record
from app.crud.user import get_user as get_user_record
from app.crud.user import get_users, update_user as update_user_record
from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


def _token_user_id(token_data: dict) -> int:
    try:
        return int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")


def _require_self_or_admin(user_id: int, token_data: dict, db: Session) -> None:
    if token_data.get("actor_type") not in (None, "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account required")

    token_user_id = _token_user_id(token_data)
    if token_user_id == user_id:
        user = db.query(User).filter(User.id == token_user_id).first()
        if not user or token_data.get("email") != user.email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")
        return

    verify_admin(request=None, token_data=token_data, db=db)


@router.get("/", response_model=list[UserResponse])
def get_all_users(
    admin: dict = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    return get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data, db)
    user = get_user_record(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated: UserUpdate,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data, db)
    expected_token_version = (
        token_data.get("token_version", 0)
        if token_data.get("actor_type") in (None, "user") and _token_user_id(token_data) == user_id
        else None
    )
    try:
        user = update_user_record(db, user_id, updated, expected_token_version)
    except StaleUserCredentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    token_data: dict = Depends(get_active_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data, db)
    if not delete_user_record(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}
