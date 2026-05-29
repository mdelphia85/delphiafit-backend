from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# ⭐ ROUTERS
from app.routers import sports
from app.routers import auth as auth_router
from app.routers import users as user_routes

from app.routers.admin import analytics as admin_analytics
from app.routers.admin import announcements as admin_announcements
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import logs as admin_logs
from app.routers.admin import messages as admin_messages
from app.routers.admin import users as admin_users

from app.routers.tactical import firefighters as tactical_firefighters
from app.routers.tactical import ems as tactical_ems
from app.routers.tactical import police as tactical_police
from app.routers.tactical import military as tactical_military

# ⭐ DATABASE
from app.database.connection import Base, engine


app = FastAPI()


# ---------------------------------------------------------
# ⭐ CORS MUST BE FIRST
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# ⭐ FORCE HTTPS (FIXES 307 → HTTP REDIRECT)
# ---------------------------------------------------------
app.add_middleware(HTTPSRedirectMiddleware)


# ---------------------------------------------------------
# ⭐ ROOT
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"status": "backend is running"}


# ---------------------------------------------------------
# ⭐ ROUTERS
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# ⭐ DATABASE INIT
# ---------------------------------------------------------
Base.metadata.create_all(bind=engine)
