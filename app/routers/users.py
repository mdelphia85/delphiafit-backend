from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_access_token
from app.crud.user import delete_user as delete_user_record
from app.crud.user import get_user as get_user_record
from app.crud.user import get_users, update_user as update_user_record
from app.database.connection import get_db
from app.schemas.user import UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


def _token_user_id(token_data: dict) -> int:
    try:
        return int(token_data.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")


def _require_self_or_admin(user_id: int, token_data: dict) -> None:
    if _token_user_id(token_data) != user_id and not token_data.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this user")


@router.get("/", response_model=list[UserResponse])
def get_all_users(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
):
    if not token_data.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data)
    user = get_user_record(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated: UserUpdate,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data)
    user = update_user_record(db, user_id, updated)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db),
):
    _require_self_or_admin(user_id, token_data)
    if not delete_user_record(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}
