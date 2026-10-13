import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import init_db
from app.routers import (
    athlete_auth,
    athlete_invites,
    athlete_log,
    athlete_plan,
    athlete_profile,
    athletes,
    auth,
    coach_invites,
    coach_plan,
    coach_reports,
    coach_roster,
    health,
    workout_logs,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not os.getenv("TESTING"):
        init_db()
    yield


app = FastAPI(
    title="Training Planner API",
    version="0.1.0",
    lifespan=lifespan,
)

class _WebNoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/web"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


app.add_middleware(_WebNoCacheMiddleware)

_cors = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors.split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static = Path(__file__).resolve().parent.parent / "static"
if _static.is_dir():
    app.mount("/web", StaticFiles(directory=_static, html=True), name="web")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(athlete_auth.router)
app.include_router(athlete_profile.router)
app.include_router(athlete_invites.router)
app.include_router(athlete_plan.router)
app.include_router(athlete_log.router)
app.include_router(coach_invites.router)
app.include_router(coach_roster.router)
app.include_router(athletes.router)
app.include_router(workout_logs.router)
app.include_router(coach_plan.router)
app.include_router(coach_reports.router)
