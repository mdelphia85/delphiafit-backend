from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router

# ⭐ ADMIN ROUTERS
from app.routers.admin import analytics as admin_analytics
from app.routers.admin import announcements as admin_announcements
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import logs as admin_logs
from app.routers.admin import messages as admin_messages
from app.routers.admin import users as admin_users

app = FastAPI()

# ⭐ UPDATED CORS CONFIG — FIXES YOUR PRODUCTION CORS BLOCK
origins = [
    "http://localhost:5173",
    "https://delphiafit-web.vercel.app",
    "https://www.delphiafit.com",
    "https://delphiafit.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "backend is running"}

# ⭐ USER AUTH ROUTES
app.include_router(auth_router)

# ⭐ ADMIN ROUTES (only the ones that still exist)
app.include_router(admin_analytics.router)
app.include_router(admin_announcements.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_logs.router)
app.include_router(admin_messages.router)
app.include_router(admin_users.router)

# ⭐ DATABASE INIT
from app.database.connection import Base, engine
Base.metadata.create_all(bind=engine)
