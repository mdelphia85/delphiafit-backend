"""Static/runtime validation for the DelphiaFit FastAPI application.

Run from the repository root after installing requirements:
    python scripts/validate_backend.py

This does not mutate the configured production database. It supplies a temporary
SQLite URL before importing the app, configures SQLAlchemy mappers, imports every
application module, builds OpenAPI, and checks for duplicate HTTP method/path pairs.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{Path(tempfile.gettempdir()) / 'delphiafit_validate.db'}",
)
os.environ.setdefault("JWT_SECRET", "validation-only-secret-do-not-use-in-production")

import app  # noqa: E402
from app.database.connection import Base  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from sqlalchemy.orm import configure_mappers  # noqa: E402


def main() -> int:
    failures: list[tuple[str, str, str]] = []
    attempted = 0

    for module in pkgutil.walk_packages(app.__path__, app.__name__ + "."):
        attempted += 1
        try:
            importlib.import_module(module.name)
        except Exception as exc:  # validation should report all import failures
            failures.append((module.name, type(exc).__name__, str(exc)))

    if failures:
        print(f"Import failures: {len(failures)}")
        for module, kind, message in failures:
            print(f"  {module}: {kind}: {message}")
        return 1

    configure_mappers()
    spec = fastapi_app.openapi()

    seen: dict[tuple[str, str], str] = {}
    duplicates: list[tuple[str, str, str, str]] = []
    for route in fastapi_app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods - {"HEAD", "OPTIONS"}:
            key = (method, route.path)
            if key in seen:
                duplicates.append((method, route.path, seen[key], route.name))
            else:
                seen[key] = route.name

    print(f"Application modules imported: {attempted}")
    print(f"SQLAlchemy mappers configured: {len(Base.registry.mappers)}")
    print(f"FastAPI routes registered: {len(fastapi_app.routes)}")
    print(f"OpenAPI paths generated: {len(spec['paths'])}")
    print(f"Duplicate HTTP method/path pairs: {len(duplicates)}")

    if duplicates:
        for method, path, first, second in duplicates:
            print(f"  {method} {path}: {first} / {second}")
        return 1

    print("Backend validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
