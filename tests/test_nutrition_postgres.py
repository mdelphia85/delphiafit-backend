"""Concurrent nutrition-write idempotency against disposable PostgreSQL."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url


def test_two_simultaneous_nutrition_saves_share_one_row(monkeypatch):
    url = os.getenv("DISPOSABLE_POSTGRES_TEST_URL")
    if not url:
        pytest.skip("Disposable PostgreSQL not configured")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").endswith("test"):
        pytest.skip("Test requires a disposable PostgreSQL test database")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.connection import Base, get_db
    from app.main import app
    from app.routers import nutrition

    engine = create_engine(url)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def isolated_db():
        with sessions() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    with TestClient(app) as client:
        email, password = f"nutrition-race-{uuid4().hex}@example.com", uuid4().hex
        assert client.post("/auth/register", json={
            "name": "Nutrition race QA", "email": email, "password": password
        }).status_code == 200
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid4())}
        gate = Barrier(2)
        # Meet at validation before either transaction locks the user row.
        original_fullmatch = nutrition._KEY_FORMAT.fullmatch
        # Use wrapper around the helper rather than mutating the compiled regex.
        original_create = nutrition._create_idempotently

        def coordinated_create(db, user_id, payload, key):
            gate.wait(timeout=10)
            return original_create(db, user_id, payload, key)

        monkeypatch.setattr(nutrition, "_create_idempotently", coordinated_create)

        def save():
            return client.post("/nutrition/", headers=headers, json={"calories": 135, "protein": 9})

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(save)
            second = executor.submit(save)
            results = [first.result(timeout=20), second.result(timeout=20)]
        assert all(r.status_code == 200 for r in results), [r.text for r in results]
        assert results[0].json()["id"] == results[1].json()["id"]
        assert len(client.get("/nutrition/", headers=headers).json()) == 1
    engine.dispose()
