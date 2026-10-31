import os
import tempfile

_db_file = os.path.join(tempfile.mkdtemp(), "community_area_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["JWT_SECRET"] = "unit-test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402
from app.database.migrate import run_migrations  # noqa: E402
from app.main import app  # noqa: E402

run_migrations()
client = TestClient(app)


def account(label):
    email = f"area-{label}@example.com"
    created = client.post("/auth/register", json={"name": label, "email": email, "password": "Passw0rd!x"})
    assert created.status_code == 200, created.text
    response = client.post("/auth/login", json={"email": email, "password": "Passw0rd!x"})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def creator(headers):
    response = client.post("/creator/create", headers=headers, json={"name": "Area Creator", "expertise": "sports"})
    assert response.status_code == 200, response.text
    return response.json()


def test_academy_recruiting_and_follow_records_are_authenticated_and_scoped():
    owner, other = account("academy-owner"), account("academy-other")
    assert client.get("/sports-academy/progress").status_code == 401
    saved = client.put("/sports-academy/progress", headers=owner, json={"sport": "soccer", "drill": "Passing", "completed": True})
    assert saved.status_code == 200, saved.text
    assert client.get("/sports-academy/progress", headers=owner).json() == [{"sport": "soccer", "drill": "Passing", "completed": True}]
    assert client.get("/sports-academy/progress", headers=other).json() == []

    assert client.get("/recruiting/profiles").status_code == 401
    private = client.put("/recruiting/profile", headers=owner, json={"sport": "soccer", "position": "midfielder", "bio": "Private", "public": False})
    assert private.status_code == 200
    assert client.get("/recruiting/profiles", headers=other).json() == []
    published = client.put("/recruiting/profile", headers=owner, json={"sport": "soccer", "position": "midfielder", "bio": "Published", "public": True})
    assert published.status_code == 200
    assert client.get("/recruiting/profiles", headers=other).json()[0]["bio"] == "Published"

    profiles = client.get("/community/profiles", headers=owner).json()
    target_id = next(profile["id"] for profile in profiles if profile["name"] == "academy-other")
    assert client.post(f"/community/follows/{target_id}", headers=owner).json()["following"] is True
    assert next(item for item in client.get("/community/profiles", headers=owner).json() if item["id"] == target_id)["following"]
    assert client.delete(f"/community/follows/{target_id}", headers=owner).status_code == 200
    assert not next(item for item in client.get("/community/profiles", headers=owner).json() if item["id"] == target_id)["following"]


def test_kids_profile_parent_scope_controls_and_progress_persist():
    parent, other = account("kids-parent"), account("kids-outsider")
    assert client.get("/kids/children").status_code == 401
    created = client.post("/kids/children", headers=parent, json={"nickname": "Runner", "parent_controls_enabled": True})
    assert created.status_code == 200, created.text
    child_id = created.json()["id"]
    assert client.put(f"/kids/children/{child_id}/progress", headers=parent, json={"activity_key": "movement", "completed": True}).status_code == 200
    assert client.patch(f"/kids/children/{child_id}", headers=parent, json={"nickname": "Runner", "parent_controls_enabled": False}).json()["parent_controls_enabled"] is False
    assert client.get("/kids/children", headers=parent).json()[0]["progress"][0]["completed"] is True
    assert client.get("/kids/children", headers=other).json() == []
    assert client.put(f"/kids/children/{child_id}/progress", headers=other, json={"activity_key": "movement", "completed": False}).status_code == 404
    assert client.patch(f"/kids/children/{child_id}", headers=other, json={"nickname": "Changed", "parent_controls_enabled": True}).status_code == 404


def test_federation_membership_and_competition_registration_are_scoped():
    owner, participant, outsider = account("event-owner"), account("event-participant"), account("event-outsider")
    assert client.get("/federation/list").status_code == 401
    federation = client.post("/federation/create", headers=owner, json={"name": "Local League", "sport": "track"})
    assert federation.status_code == 200, federation.text
    federation_id = federation.json()["id"]
    assert client.get(f"/federation/{federation_id}", headers=outsider).status_code == 404
    assert client.post(f"/federation/{federation_id}/join", headers=participant).status_code == 200
    assert client.get(f"/federation/{federation_id}/members", headers=participant).status_code == 200
    assert client.put(f"/federation/{federation_id}/rulebook", headers=participant, json={"rulebook": "No"}).status_code == 403

    creator(owner)
    creator(outsider)
    competition = client.post("/competition/create", headers=owner, json={"name": "Spring Meet", "sport": "track"})
    assert competition.status_code == 200, competition.text
    competition_id = competition.json()["id"]
    assert client.post(f"/competition/{competition_id}/register", headers=participant).status_code == 200
    rows = client.get("/competition/list", headers=participant).json()
    assert next(row for row in rows if row["id"] == competition_id)["registered_count"] == 1
    assert next(row for row in rows if row["id"] == competition_id)["registered"] is True
    assert client.put(f"/competition/{competition_id}/update", headers=outsider, json={"updates": {"name": "Hijack"}}).status_code == 403
    assert client.post("/tournament/create", headers=outsider, json={"competition_id": competition_id, "name": "Cup"}).status_code == 403
    tournament = client.post("/tournament/create", headers=owner, json={"competition_id": competition_id, "name": "Cup"})
    assert tournament.status_code == 200, tournament.text
    tournaments = client.get(f"/tournament/competition/{competition_id}", headers=participant)
    assert tournaments.json()[0]["name"] == "Cup"
    tournament_id = tournaments.json()[0]["id"]
    assert client.post(f"/tournament/{tournament_id}/register", headers=participant).json()["registered"] is True
    assert client.get(f"/tournament/competition/{competition_id}", headers=participant).json()[0]["registered_count"] == 1
    assert client.delete(f"/tournament/{tournament_id}/register", headers=participant).json()["registered"] is False
    assert client.delete(f"/competition/{competition_id}/register", headers=participant).json()["registered"] is False
    assert client.get("/competition/list").status_code == 401


def test_marketplace_listing_interest_and_owner_only_edits():
    seller, interested, outsider = account("market-seller"), account("market-interested"), account("market-outsider")
    listing = client.post("/creator/marketplace/listings", headers=seller, json={"title": "Training plan", "description": "Details", "category": "training", "price": 25})
    assert listing.status_code == 200, listing.text
    listing_id = listing.json()["id"]
    assert client.get("/creator/marketplace/listings").status_code == 401
    assert client.post(f"/creator/marketplace/listings/{listing_id}/interest", headers=interested, json={"message": "Tell me more"}).status_code == 200
    assert client.post(f"/creator/marketplace/listings/{listing_id}/interest", headers=interested, json={"message": "Still interested"}).status_code == 200
    assert client.get(f"/creator/marketplace/listings/{listing_id}/interests", headers=seller).json()[0]["name"] == "market-interested"
    assert client.put(f"/creator/marketplace/listings/{listing_id}", headers=outsider, json={"title": "Edited", "price": 0}).status_code == 403
    assert client.post(f"/creator/marketplace/listings/{listing_id}/interest", headers=seller, json={}).status_code == 400


def test_community_area_migrations_are_idempotent():
    run_migrations()
    run_migrations()


def test_creator_seasons_ladders_and_tournaments_are_owner_scoped():
    owner, outsider = account("season-owner"), account("season-outsider")
    creator(owner)
    creator(outsider)
    assert client.post("/season/create", headers=owner, json={"name": "2026 Track", "year": 2026, "sport": "track"}).status_code == 200
    season = client.post("/season/create", headers=owner, json={"name": "Winter", "year": 2026})
    assert season.status_code == 200, season.text
    season_id = season.json()["id"]
    assert client.put(f"/season/{season_id}/update", headers=outsider, json={"updates": {"name": "Stolen"}}).status_code == 403
    competition = client.post("/competition/create", headers=owner, json={"name": "Seasoned Meet", "season_id": season_id})
    assert competition.status_code == 200, competition.text
    competition_id = competition.json()["id"]
    assert client.post("/competition/create", headers=outsider, json={"name": "Wrong Season", "season_id": season_id}).status_code == 403
    assert client.post("/ladder/create", headers=owner, json={"competition_id": competition_id, "name": "Open Ladder"}).status_code == 200
    ladder = client.post("/ladder/create", headers=owner, json={"competition_id": competition_id, "name": "Season Ladder"})
    assert ladder.status_code == 200, ladder.text
    ladder_id = ladder.json()["id"]
    assert client.put(f"/ladder/{ladder_id}/update", headers=outsider, json={"updates": {"name": "Hijacked"}}).status_code == 403
    tournament = client.post("/tournament/create", headers=owner, json={"competition_id": competition_id, "name": "Date Test", "start_date": "2026-11-15T10:00:00"})
    assert tournament.status_code == 200, tournament.text
    tournament_id = tournament.json()["id"]
    assert client.put(f"/tournament/{tournament_id}/update", headers=outsider, json={"updates": {"name": "Hijacked"}}).status_code == 403
