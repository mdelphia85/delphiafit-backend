from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Register all SQLAlchemy models before routers configure relationships.
from app import models as _models

# Legacy/core routers that existed before the V2 expansion.
from app.routers import sports
from app.routers import auth as auth_router
from app.routers import users as users_router
from app.routers.admin import auth as admin_auth
from app.routers.admin import analytics as admin_analytics
from app.routers.admin import announcements as admin_announcements
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import logs as admin_logs
from app.routers.admin import messages as admin_messages
from app.routers.admin import users as admin_users
from app.routers.admin import config as admin_config
from app.routers.admin import system as admin_system
from app.routers.tactical import firefighters as tactical_firefighters
from app.routers.tactical import ems as tactical_ems
from app.routers.tactical import police as tactical_police
from app.routers.tactical import military as tactical_military

# V2 fitness, nutrition, social, AI, coaching, competition, and operations routers.
from app.routers import (
    workout_log,
    daily_log,
    activity,
    body_metrics,
    hydration,
    sleep,
    weight,
    strength,
    sports_log,
    nutrition,
    meals,
    macros,
    goals,
    recipes,
    pr,
    periodization,
    rep_logs,
    recovery,
    progress,
    nutrition_plan,
    social,
    ai,
    live,
    coach,
    team,
    invite,
    competition,
    tournament,
    ladder,
    season,
    federation,
    creator,
    hardware,
    org,
    medical,
    medical_recovery,
    academy,
    sof,
    swat,
    k9,
    search_rescue,
    disaster,
    hazmat,
    wildland,
    maritime,
    aviation,
    scenario,
    loadout,
    instructor,
    mission_replay,
    certification,
    unit,
    staff,
    frontend_compat,
)

app = FastAPI(title="DelphiaFit Backend V2", redirect_slashes=False)

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

# Core/public routes.
app.include_router(sports.router, prefix="/sports")
app.include_router(auth_router.router, prefix="/auth")
app.include_router(users_router.router)

# Admin routes.
app.include_router(admin_auth.router)
app.include_router(admin_analytics.router)
app.include_router(admin_announcements.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_logs.router)
app.include_router(admin_messages.router)
app.include_router(admin_users.router)
app.include_router(admin_config.router)
app.include_router(admin_system.router)

# Existing tactical routes.
app.include_router(tactical_firefighters.router)
app.include_router(tactical_ems.router)
app.include_router(tactical_police.router)
app.include_router(tactical_military.router)

# V2 route modules. Each module owns its own prefix.
_v2_routers = [
    workout_log.router,
    daily_log.router,
    activity.router,
    body_metrics.router,
    hydration.router,
    sleep.router,
    weight.router,
    strength.router,
    sports_log.router,
    nutrition.router,
    meals.router,
    macros.router,
    goals.router,
    recipes.router,
    pr.router,
    periodization.router,
    rep_logs.router,
    recovery.router,
    progress.router,
    nutrition_plan.router,
    social.router,
    ai.router,
    live.router,
    coach.router,
    team.router,
    invite.router,
    competition.router,
    tournament.router,
    ladder.router,
    season.router,
    federation.router,
    creator.router,
    hardware.router,
    org.router,
    medical.router,
    medical_recovery.router,
    academy.router,
    sof.router,
    swat.router,
    k9.router,
    search_rescue.router,
    disaster.router,
    hazmat.router,
    wildland.router,
    maritime.router,
    aviation.router,
    scenario.router,
    loadout.router,
    instructor.router,
    mission_replay.router,
    certification.router,
    unit.router,
    staff.router,
    frontend_compat.router,
]

for router in _v2_routers:
    app.include_router(router)

@app.get("/")
def root():
    return {"status": "backend is running", "version": "V2"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "V2"}
