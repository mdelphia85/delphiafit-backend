from fastapi import APIRouter
from pydantic import BaseModel
import sqlite3
import hashlib

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
async def register_user(data: RegisterRequest):
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

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (data.name, data.email, hashed_pw)
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "Account created"}
    except sqlite3.IntegrityError:
        conn.close()
        return {"success": False, "message": "Email already exists"}
