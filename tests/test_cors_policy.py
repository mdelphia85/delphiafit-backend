"""CORS production isolation and owner configuration regression."""
import os

os.environ.setdefault("JWT_SECRET", "test-only-cors-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.main import get_cors_origins, PRODUCTION_FRONTEND_ORIGINS


def test_localhost_allowed_outside_railway_production(monkeypatch):
    monkeypatch.delenv("RAILWAY_ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("STAGING_FRONTEND_ORIGIN", raising=False)
    assert "http://localhost:5173" in get_cors_origins()


def test_railway_production_never_allows_localhost_origin(monkeypatch):
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_NAME", "production")
    monkeypatch.delenv("STAGING_FRONTEND_ORIGIN", raising=False)
    origins = get_cors_origins()
    assert "http://localhost:5173" not in origins
    assert all(origin in origins for origin in PRODUCTION_FRONTEND_ORIGINS)
