from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------
# Import ALL V2 routers
# ---------------------------

from app.routers import (
    workout_log,
    daily_log,
    activity,
    body_metrics,
    hydration,
    sleep,
    weight,
    strength,
    sports_log,   # ← FULL SYSTEM FIX

    # Fitness + Nutrition
    nutrition,
    meals,
    macros,
    goals,
    recipes,
    pr,
    periodization,
    rep_logs,

    # Social + Community
    social,

    # AI Systems
    ai,
    smart_mode,
    weekly_plan,
    form_scoring,
    velocity,
    live,

    # Coaching + Team
    coach,
    team,
    invite,
    plan,
    drill,

    # Competitions
    competition,
    tournament,
    ladder,
    season,
    federation,

    # Creator Marketplace
    creator,

    # Hardware
    hardware,

    # Enterprise
    org,

    # Medical
    medical,
    medical_recovery,

    # Tactical
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
    unit
)

app = FastAPI(title="DelphiaFit Backend V2")

# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # update later for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Register ALL routers
# ---------------------------

app.include_router(workout_log.router)
app.include_router(daily_log.router)
app.include_router(activity.router)
app.include_router(body_metrics.router)
app.include_router(hydration.router)
app.include_router(sleep.router)
app.include_router(weight.router)
app.include_router(strength.router)
app.include_router(sports_log.router)  # ← FULL SYSTEM FIX

# Fitness + Nutrition
app.include_router(nutrition.router)
app.include_router(meals.router)
app.include_router(macros.router)
app.include_router(goals.router)
app.include_router(recipes.router)
app.include_router(pr.router)
app.include_router(periodization.router)
app.include_router(rep_logs.router)



# AI
app.include_router(ai.router)
app.include_router(smart_mode.router)
app.include_router(weekly_plan.router)
app.include_router(form_scoring.router)
app.include_router(velocity.router)
app.include_router(live.router)

# Coaching + Team
app.include_router(coach.router)
app.include_router(team.router)
app.include_router(invite.router)
app.include_router(plan.router)
app.include_router(drill.router)

# Competitions
app.include_router(competition.router)
app.include_router(tournament.router)
app.include_router(ladder.router)
app.include_router(season.router)
app.include_router(federation.router)

# Creator Marketplace
app.include_router(creator.router)

# Hardware
app.include_router(hardware.router)

# Enterprise
app.include_router(org.router)

# Medical
app.include_router(medical.router)
app.include_router(medical_recovery.router)

# Tactical
app.include_router(academy.router)
app.include_router(sof.router)
app.include_router(swat.router)
app.include_router(k9.router)
app.include_router(search_rescue.router)
app.include_router(disaster.router)
app.include_router(hazmat.router)
app.include_router(wildland.router)
app.include_router(maritime.router)
app.include_router(aviation.router)
app.include_router(scenario.router)
app.include_router(loadout.router)
app.include_router(instructor.router)
app.include_router(mission_replay.router)
app.include_router(certification.router)
app.include_router(unit.router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "V2"}
