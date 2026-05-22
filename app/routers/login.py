from fastapi import APIRouter
from pydantic import BaseModel
import sqlite3
import hashlib

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login")
async def login_user(data: LoginRequest):
    conn = sqlite3.connect("data/app.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    hashed_pw = hash_password(data.password)

    cursor.execute(
        "SELECT id, password FROM users WHERE email = ?",
        (data.email,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"success": False, "message": "Invalid email or password"}

    user_id, stored_pw = user

    if stored_pw != hashed_pw:
        return {"success": False, "message": "Invalid email or password"}

    return {"success": True, "user_id": user_id}
