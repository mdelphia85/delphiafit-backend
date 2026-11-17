"""Verify concurrent scanner saves on a disposable PostgreSQL test database."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url


def test_concurrent_saves_keep_one_history_record(monkeypatch):
    database_url = os.getenv("DISPOSABLE_POSTGRES_TEST_URL")
    if not database_url:
        pytest.skip("Set DISPOSABLE_POSTGRES_TEST_URL to run scanner concurrency tests")
    database = make_url(database_url)
    if database.get_backend_name() != "postgresql" or not (database.database or "").endswith("test"):
        pytest.skip("Scanner concurrency requires a disposable PostgreSQL test database")

    from app.database.connection import Base, get_db
    from app.main import app
    from app.routers import food_scan
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def isolated_db():
        with sessions() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    email = f"scanner-race-{uuid4().hex}@example.com"
    password = uuid4().hex
    history_path = "/nutrition-scanner/history"
    with TestClient(app) as client:
        registered = client.post("/auth/register", json={
            "name": "Scanner QA", "email": email, "password": password
        })
        assert registered.status_code == 200
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Synchronize both authenticated requests before the database row lock.
        # Waiting for a second history read would deadlock the corrected endpoint.
        entered_save = Barrier(2)
        original_validate = food_scan._validate_barcode

        def synchronize_before_lock(barcode):
            original_validate(barcode)
            entered_save.wait(timeout=10)

        monkeypatch.setattr(food_scan, "_validate_barcode", synchronize_before_lock)

        def save():
            return client.post(history_path, json={"barcode": "036000291452"}, headers=headers)

        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(save)
                second = executor.submit(save)
                responses = [first.result(timeout=20), second.result(timeout=20)]

            assert [response.status_code for response in responses] == [200, 200]
            assert responses[0].json()["id"] == responses[1].json()["id"]
            assert len(client.get(history_path, headers=headers).json()) == 1
        finally:
            engine.dispose()
