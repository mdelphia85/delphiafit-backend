# force rebuild
# force rebuild

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# ⭐ AUTH ROUTES
from app.routers import auth as auth_router
from app.routers import register as register_router

# ⭐ ADMIN ROUTERS
from app.routers.admin import analytics as admin_analytics
from app.routers.admin import announcements as admin_announcements
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import logs as admin_logs
from app.routers.admin import messages as admin_messages
from app.routers.admin import users as admin_users

# ⭐ TACTICAL ROUTERS
from app.routers.tactical import firefighters as tactical_firefighters
from app.routers.tactical import ems as tactical_ems
from app.routers.tactical import police as tactical_police
from app.routers.tactical import military as tactical_military

# ⭐ USER ROUTES
from app.routers import users as user_routes

# ⭐ SPORTS ROUTES
from app.routers import sports

app = FastAPI()

# ⭐ FIX REDIRECT LOOP + ALLOW RAILWAY PROXY
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# ⭐ CORS CONFIG
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

# ⭐ ROUTES
app.include_router(sports.router)
app.include_router(auth_router.router, prefix="/auth")
app.include_router(user_routes.router)
app.include_router(admin_analytics.router)
app.include_router(admin_announcements.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_logs.router)
app.include_router(admin_messages.router)
app.include_router(admin_users.router)
app.include_router(tactical_firefighters.router)
app.include_router(tactical_ems.router)
app.include_router(tactical_police.router)
app.include_router(tactical_military.router)

# ⭐ DATABASE INIT
from app.database.connection import Base, engine
Base.metadata.create_all(bind=engine)
