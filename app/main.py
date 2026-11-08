from urllib.parse import parse_qsl
from urllib.parse import urlsplit
import ipaddress
import logging
import os
import re
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    nutrition_coach,
    social,
    community_area,
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
    tactical_progress,
    user_data,
    insights,
    account,
)

app = FastAPI(title="DelphiaFit Backend V2", redirect_slashes=False)
logger = logging.getLogger(__name__)

_SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "auth_token",
    "authorization",
    "client_secret",
    "code",
    "invite_token",
    "invitation_token",
    "password",
    "password_reset_token",
    "refresh_token",
    "reset_token",
    "secret",
    "session_token",
    "token",
}


@app.middleware("http")
async def redact_sensitive_query_strings(request, call_next):
    query_string = request.scope.get("query_string", b"")
    if query_string:
        query = query_string.decode("latin-1")
        if any(key.casefold() in _SENSITIVE_QUERY_KEYS for key, _ in parse_qsl(query, keep_blank_values=True)):
            request.scope["query_string"] = b""
    return await call_next(request)


@app.middleware("http")
async def sanitize_unhandled_errors(request: Request, call_next):
    request_id = uuid.uuid4().hex
    request.state.request_id = request_id
    try:
        return await call_next(request)
    except Exception as exc:
        logger.error(
            "Unhandled request failure request_id=%s exception_type=%s",
            request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


PRODUCTION_FRONTEND_ORIGINS = (
    "https://delphiafit-web.vercel.app",
    "https://www.delphiafit.com",
    "https://delphiafit.com",
)
DEVELOPMENT_FRONTEND_ORIGINS = ("http://localhost:5173",)
_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_staging_frontend_origin(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    candidate = value.strip()
    try:
        parsed = urlsplit(candidate)
        hostname = parsed.hostname
        port = parsed.port
    except (UnicodeError, ValueError):
        hostname = None
        port = None

    if (
        not hostname
        or parsed.scheme.casefold() != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or "?" in candidate
        or "#" in candidate
        or "\\" in candidate
        or any(character.isspace() for character in candidate)
        or "*" in candidate
    ):
        raise RuntimeError(
            "STAGING_FRONTEND_ORIGIN must be a single HTTPS origin without credentials, path, query, or fragment"
        )

    normalized_host = hostname.rstrip(".").encode("idna").decode("ascii").casefold()
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError:
        labels = normalized_host.split(".")
        if len(normalized_host) > 253 or not all(_DNS_LABEL.fullmatch(label) for label in labels):
            raise RuntimeError("STAGING_FRONTEND_ORIGIN must contain a valid HTTPS hostname") from None
        host_for_origin = normalized_host
    else:
        host_for_origin = f"[{address.compressed}]" if address.version == 6 else address.compressed

    port_suffix = f":{port}" if port is not None and port != 443 else ""
    return f"https://{host_for_origin}{port_suffix}"


def get_cors_origins(staging_origin: str | None = None) -> list[str]:
    if staging_origin is None:
        staging_origin = os.getenv("STAGING_FRONTEND_ORIGIN")
    normalized_staging_origin = normalize_staging_frontend_origin(staging_origin)
    origins = [*DEVELOPMENT_FRONTEND_ORIGINS, *PRODUCTION_FRONTEND_ORIGINS]
    if normalized_staging_origin and normalized_staging_origin not in origins:
        origins.append(normalized_staging_origin)
    return origins


origins = get_cors_origins()

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
    nutrition_coach.router,
    social.router,
    community_area.router,
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
    tactical_progress.router,
    user_data.router,
    insights.router,
    account.router,
]

for router in _v2_routers:
    app.include_router(router)

@app.get("/")
def root():
    return {"status": "backend is running", "version": "V2"}


@app.get("/health")
def health():
    return {"status": "ok", "version": "V2"}
