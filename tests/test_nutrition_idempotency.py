"""Nutrition write idempotency regression with authenticated isolated records."""
import os
from uuid import uuid4

os.environ.setdefault("JWT_SECRET", "qa-only-nutrition-token-secret")
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database.connection import Base, get_db
    from app.main import app

    engine = create_engine(f"sqlite:///{tmp_path / 'nutrition-requests.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def isolated_db():
        with factory() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()


def user_headers(client):
    email = f"nutrition-qa-{uuid4().hex}@example.com"
    password = uuid4().hex
    response = client.post("/auth/register", json={
        "name": "Nutrition QA", "email": email, "password": password
    })
    assert response.status_code == 200, response.text
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_retry_returns_same_log_without_duplicate(client):
    headers = user_headers(client)
    headers["Idempotency-Key"] = str(uuid4())
    payload = {"calories": 120, "protein": 12, "carbs": 11, "fats": 3}
    one = client.post("/nutrition/", headers=headers, json=payload)
    two = client.post("/nutrition/", headers=headers, json=payload)
    assert one.status_code == two.status_code == 200
    assert one.json()["id"] == two.json()["id"]
    records = client.get("/nutrition/", headers=headers).json()
    assert len(records) == 1
    assert records[0]["calories"] == 120


def test_retry_with_changed_body_conflicts(client):
    headers = user_headers(client)
    headers["Idempotency-Key"] = str(uuid4())
    original = client.post("/nutrition/", headers=headers, json={"calories": 120})
    assert original.status_code == 200
    conflict = client.post("/nutrition/", headers=headers, json={"calories": 240})
    assert conflict.status_code == 409
    assert len(client.get("/nutrition/", headers=headers).json()) == 1


def test_keys_are_isolated_by_account(client):
    key = str(uuid4())
    user_one = {**user_headers(client), "Idempotency-Key": key}
    user_two = {**user_headers(client), "Idempotency-Key": key}
    one = client.post("/nutrition/", headers=user_one, json={"calories": 100})
    two = client.post("/nutrition/", headers=user_two, json={"calories": 100})
    assert one.status_code == two.status_code == 200
    assert one.json()["user_id"] != two.json()["user_id"]


def test_legacy_no_key_preserves_distinct_log_entries(client):
    headers = user_headers(client)
    for _ in range(2):
        assert client.post("/nutrition/", headers=headers, json={"calories": 100}).status_code == 200
    assert len(client.get("/nutrition/", headers=headers).json()) == 2


def test_invalid_key_rejected_without_write(client):
    headers = {**user_headers(client), "Idempotency-Key": "bad"}
    assert client.post("/nutrition/", headers=headers, json={"calories": 100}).status_code == 422
    assert client.get("/nutrition/", headers=headers).json() == []
