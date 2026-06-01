from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.user import User
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

# -----------------------------
# Admin Login Schema
# -----------------------------
class AdminLogin(BaseModel):
    email: str
    password: str


# -----------------------------
# POST /admin/login
# -----------------------------
@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials"
        )

    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin"
        )

    token = create_access_token({"sub": user.email, "is_admin": True})

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# -----------------------------
# GET /admin/me
# -----------------------------
@router.get("/me")
def admin_me(
    token_data: dict = Depends(decode_access_token),
    db: Session = Depends(get_db)
):
    email = token_data.get("sub")
    is_admin = token_data.get("is_admin")

    if not email or not is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token"
        )

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name
    }


# -----------------------------
# Admin-only dependency
# -----------------------------
def verify_admin(token_data: dict = Depends(decode_access_token)):
    if not token_data.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return token_data
