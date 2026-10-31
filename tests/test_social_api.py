import os
import tempfile
from datetime import datetime

import pytest

_db_file = os.path.join(tempfile.mkdtemp(), "social_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)


def make_user(email):
    registered = client.post("/auth/register", json={"name": email, "email": email, "password": "Passw0rd!x"})
    assert registered.status_code == 200, registered.text
    login = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_social_routes_require_authentication():
    assert client.get("/social/posts").status_code == 401
    assert client.post("/social/groups", params={"name": "Private"}).status_code == 401
    assert client.post("/social/posts", params={"content": "Hi"}).status_code == 401


def test_posts_comments_and_reactions_persist_and_enforce_author_ownership():
    alice, bob = make_user("social-alice@example.com"), make_user("social-bob@example.com")
    created = client.post("/social/posts", headers=alice, params={"content": "First post"})
    assert created.status_code == 200, created.text
    post_id = created.json()["id"]

    assert client.put(f"/social/posts/{post_id}", headers=bob, params={"content": "Changed"}).status_code == 403
    comment = client.post(f"/social/posts/{post_id}/comments", headers=bob, params={"content": "Good work"})
    assert comment.status_code == 200, comment.text
    comment_id = comment.json()["id"]
    assert client.put(f"/social/comments/{comment_id}", headers=alice, params={"content": "Edited"}).status_code == 403
    assert client.put(f"/social/comments/{comment_id}", headers=bob, params={"content": "Edited"}).status_code == 200
    assert client.post(f"/social/posts/{post_id}/reactions", headers=bob, params={"reaction_type": "like"}).status_code == 200
    assert client.post(f"/social/posts/{post_id}/reactions", headers=bob, params={"reaction_type": "like"}).status_code == 200

    feed = client.get("/social/posts", headers=bob)
    assert feed.status_code == 200, feed.text
    item = next(row for row in feed.json() if row["id"] == post_id)
    assert item["content"] == "First post"
    assert [row["content"] for row in item["comments"]] == ["Edited"]
    assert len(item["reactions"]) == 1
    assert client.delete(f"/social/posts/{post_id}", headers=bob).status_code == 403
    assert client.delete(f"/social/posts/{post_id}", headers=alice).status_code == 200
    assert all(row["id"] != post_id for row in client.get("/social/posts", headers=bob).json())


def test_groups_are_user_scoped_and_join_operations_are_idempotent():
    alice, bob, cara = (make_user(f"groups-{name}@example.com") for name in ("alice", "bob", "cara"))
    created = client.post("/social/groups", headers=alice, params={"name": "Local Runners", "description": "Easy runs"})
    assert created.status_code == 200, created.text
    group_id = created.json()["id"]
    assert any(group["id"] == group_id for group in client.get("/social/groups", headers=alice).json())
    assert any(group["id"] == group_id for group in client.get("/social/groups/discover", headers=bob).json())
    assert client.get(f"/social/groups/{group_id}/members", headers=bob).status_code == 404

    for _ in range(2):
        joined = client.post(f"/social/groups/{group_id}/join", headers=bob)
        assert joined.status_code == 200
    assert len(client.get(f"/social/groups/{group_id}/members", headers=bob).json()) == 2
    assert client.post("/social/posts", headers=bob, params={"content": "Group post", "group_id": group_id}).status_code == 200
    assert client.get(f"/social/posts/group/{group_id}", headers=cara).status_code == 404
    assert client.delete(f"/social/groups/{group_id}/leave", headers=bob).status_code == 200
    assert client.get(f"/social/posts/group/{group_id}", headers=bob).status_code == 404


def test_leaderboard_uses_persisted_sports_logs_and_requires_authentication():
    alice, bob = make_user("ranking-alice@example.com"), make_user("ranking-bob@example.com")
    assert client.get("/sports/logs/leaderboard").status_code == 401
    now = datetime.utcnow().isoformat()
    for minutes in (35, 25):
        saved = client.post("/sports/logs/", headers=alice, json={"sport": "running", "duration_minutes": minutes, "date": now})
        assert saved.status_code == 200, saved.text
    saved = client.post("/sports/logs/", headers=bob, json={"sport": "cycling", "duration_minutes": 20, "date": now})
    assert saved.status_code == 200, saved.text
    rows = client.get("/sports/logs/leaderboard?period=weekly", headers=bob).json()
    assert rows[0]["name"] == "ranking-alice@example.com"
    assert rows[0]["minutes"] == 60 and rows[0]["sessions"] == 2
    assert rows[1]["minutes"] == 20
    assert client.get("/sports/logs/leaderboard?period=invalid", headers=bob).status_code == 400
