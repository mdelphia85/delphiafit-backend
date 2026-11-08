import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Query, sessionmaker
from fastapi.testclient import TestClient


POSTGRES_TEST_URL = os.getenv("DISPOSABLE_POSTGRES_TEST_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="Set DISPOSABLE_POSTGRES_TEST_URL to run PostgreSQL concurrency tests",
)


def test_overlapping_password_changes_reject_stale_write(monkeypatch):
    url = make_url(POSTGRES_TEST_URL)
    if url.get_backend_name() != "postgresql" or not (url.database or "").casefold().endswith("test"):
        pytest.skip("DISPOSABLE_POSTGRES_TEST_URL must name a PostgreSQL test database")

    from app.auth.hashing import hash_password
    from app.database.connection import Base, get_db
    from app.main import app
    from app.models.user import User

    engine = create_engine(POSTGRES_TEST_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        with TestSession() as db:
            yield db

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    email = f"auth-race-{uuid4().hex}@example.com"
    original_password = "OriginalPassword123!"
    account_password = "FirstChangePassword456!"
    stale_password = "StaleChangePassword789!"
    winning_password = "WinningPassword321!"
    first_row_locked = threading.Event()
    competing_lock_attempted = threading.Event()
    release_first_update = threading.Event()

    try:
        with TestSession() as db:
            db.add(User(name="Concurrency Test", email=email, hashed_password=hash_password(original_password)))
            db.commit()
            initial_token_version = db.query(User).filter(User.email == email).one().token_version

        with TestClient(app) as client:
            original_login = client.post(
                "/auth/login",
                json={"email": email, "password": original_password},
            )
            assert original_login.status_code == 200
            original_headers = {"Authorization": f"Bearer {original_login.json()['access_token']}"}

            real_first = Query.first
            lock_query_count = 0
            lock_query_count_guard = threading.Lock()

            def control_update_order(query):
                nonlocal lock_query_count
                if getattr(query, "_for_update_arg", None) is None:
                    return real_first(query)

                with lock_query_count_guard:
                    lock_query_count += 1
                    lock_order = lock_query_count

                if lock_order == 1:
                    row = real_first(query)
                    if row is None:
                        raise AssertionError("First password change did not lock its account row")
                    first_row_locked.set()
                    if not release_first_update.wait(timeout=15):
                        raise TimeoutError("Timed out waiting to release the first password-change transaction")
                    return row

                if lock_order == 2:
                    competing_lock_attempted.set()
                return real_first(query)

            monkeypatch.setattr(Query, "first", control_update_order)

            def change_password(new_password):
                with TestClient(app) as concurrent_client:
                    return concurrent_client.post(
                        "/account/change-password",
                        headers=original_headers,
                        json={
                            "current_password": original_password,
                            "new_password": new_password,
                        },
                    )

            with ThreadPoolExecutor(max_workers=2) as pool:
                first_change = pool.submit(change_password, account_password)
                assert first_row_locked.wait(timeout=10), "First password change did not acquire the row lock"
                second_change = pool.submit(change_password, stale_password)
                try:
                    assert competing_lock_attempted.wait(timeout=10), (
                        "Competing password change did not attempt the row lock"
                    )
                    deadline = time.monotonic() + 10
                    with engine.connect() as observer:
                        while time.monotonic() < deadline:
                            waiting_on_row_lock = observer.execute(
                                text(
                                    """
                                    SELECT EXISTS (
                                        SELECT 1
                                        FROM pg_stat_activity
                                        WHERE datname = current_database()
                                          AND pid <> pg_backend_pid()
                                          AND state = 'active'
                                          AND wait_event_type = 'Lock'
                                          AND query ILIKE '%FOR UPDATE%'
                                    )
                                    """
                                )
                            ).scalar_one()
                            if waiting_on_row_lock:
                                break
                            time.sleep(0.05)
                        else:
                            raise AssertionError(
                                "Competing password change did not block on the held PostgreSQL row lock"
                            )
                finally:
                    release_first_update.set()

                first_response = first_change.result(timeout=15)
                second_response = second_change.result(timeout=15)

            assert first_response.status_code == 200, first_response.text
            assert second_response.status_code == 401, second_response.text
            assert client.get("/ai/records", headers=original_headers).status_code == 401

            with TestSession() as db:
                user = db.query(User).filter(User.email == email).one()
                assert user.token_version == initial_token_version + 1

            winning_login = client.post(
                "/auth/login",
                json={"email": email, "password": account_password},
            )
            assert winning_login.status_code == 200, winning_login.text
            winning_token = winning_login.json()["access_token"]
            winning_headers = {"Authorization": f"Bearer {winning_token}"}
            assert client.get("/ai/records", headers=winning_headers).status_code == 200

            later_change = client.post(
                "/account/change-password",
                headers=winning_headers,
                json={
                    "current_password": account_password,
                    "new_password": winning_password,
                },
            )
            assert later_change.status_code == 200, later_change.text
            assert client.get("/ai/records", headers=winning_headers).status_code == 401

            with TestSession() as db:
                user = db.query(User).filter(User.email == email).one()
                assert user.token_version == initial_token_version + 2

            fresh_login = client.post(
                "/auth/login",
                json={"email": email, "password": winning_password},
            )
            assert fresh_login.status_code == 200, fresh_login.text
            fresh_headers = {"Authorization": f"Bearer {fresh_login.json()['access_token']}"}
            assert client.get("/ai/records", headers=fresh_headers).status_code == 200
    finally:
        release_first_update.set()
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override
        engine.dispose()
