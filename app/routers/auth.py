from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import hashlib
import os
import secrets
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.models.login_log import LoginLog
from app.database.connection import get_db
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.services.email_delivery import send_user_password_reset

router = APIRouter(tags=["Auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ---------------------------------------------------------
# LOGIN (PUBLIC)
# ---------------------------------------------------------
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": str(db_user.id), "email": db_user.email, "actor_type": "user"})

    db.add(LoginLog(user_id=db_user.id, timestamp=datetime.utcnow()))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer"
    }



@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    debug_token = None
    delivered = False
    if user:
        raw_token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = _token_hash(raw_token)
        user.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        try:
            delivered = send_user_password_reset(user.email, raw_token)
        except Exception:
            delivered = False
        if os.getenv("PASSWORD_RESET_DEBUG_RETURN_TOKEN", "false").lower() in {"1", "true", "yes"}:
            debug_token = raw_token

    response = {"message": "If that account exists, reset instructions have been sent.", "delivery_configured": delivered}
    if debug_token:
        response["debug_token"] = debug_token
    return response


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    if len(data.new_password) < 10:
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")
    user = db.query(User).filter(User.email == data.email).first()
    if (
        not user
        or not user.password_reset_token_hash
        or not user.password_reset_expires_at
        or user.password_reset_expires_at < datetime.utcnow()
        or not secrets.compare_digest(user.password_reset_token_hash, _token_hash(data.token))
    ):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(data.new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    db.commit()
    return {"message": "Password reset successful"}

# ---------------------------------------------------------
# AUTH ME
# ---------------------------------------------------------
@router.get("/me")
def get_me(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    user_id = token_data.get("sub")
    email = token_data.get("email")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = db.query(User).filter(User.id == int(user_id)).first() if user_id else None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "id": user.id,
        "email": user.email
    }

# ---------------------------------------------------------
# REMOVED: OLD /admin/login ROUTE
# ---------------------------------------------------------
# The admin login now lives ONLY in:
# app/routers/admin/auth.py
# and correctly returns {"is_admin": True}
