"""
FastAPI application entrypoint.

`create_all` is a convenience net for local dev only — it never alters
existing tables, only creates missing ones, so it can't handle schema
changes. The real migration path (used in Docker/production, see
entrypoint.sh) is `alembic upgrade head`, verified in this project against
an actual PostgreSQL instance, not just SQLite.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    routes_ats,
    routes_auth,
    routes_dashboard,
    routes_interview,
    routes_predictions,
    routes_resume,
    routes_roadmap,
    routes_skillgap,
    routes_users,
)
from app.core.config import get_settings
from app.database.session import Base, engine

logging.basicConfig(level=logging.INFO)
settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Streamlit runs on a different port than FastAPI locally, so the browser
# treats them as different origins — CORS must explicitly allow that.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_users.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_resume.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_predictions.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_ats.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_skillgap.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_roadmap.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_interview.router, prefix=settings.API_V1_PREFIX)
app.include_router(routes_dashboard.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}
