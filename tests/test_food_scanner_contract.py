"""Exercise scanner HTTP contracts with real JWTs and isolated SQLite records."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def scanner_client(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database.connection import Base, get_db
    from app.main import app

    engine = create_engine(f"sqlite:///{tmp_path / 'scanner.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def isolated_db():
        with sessions() as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    with TestClient(app) as client:
        yield client
    engine.dispose()


def sign_in(client):
    email = f"scanner-{uuid4().hex}@example.com"
    password = uuid4().hex
    registration = client.post("/auth/register", json={
        "name": "Synthetic Scanner QA", "email": email, "password": password,
    })
    assert registration.status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.parametrize("barcode", ["036000291452", "3017620422003"])
def test_lookup_validates_and_does_not_record_consumption(scanner_client, monkeypatch, barcode):
    from app.routers import food_scan

    client = scanner_client
    product = {"barcode": barcode, "name": "Synthetic QA product"}
    monkeypatch.setattr(food_scan, "get_product", lambda code: product if code == barcode else None)
    assert client.get(f"/nutrition-scanner/product/{barcode}").status_code == 401

    headers = sign_in(client)
    assert client.get("/nutrition-scanner/product/no-product", headers=headers).status_code == 422
    lookup = client.get(f"/nutrition-scanner/product/{barcode}", headers=headers)
    assert lookup.status_code == 200
    assert lookup.json() == product
    assert client.get("/nutrition-scanner/history", headers=headers).json() == []
    assert client.get("/nutrition/", headers=headers).json() == []


def test_history_deduplicates_and_is_private(scanner_client):
    client = scanner_client
    owner, other = sign_in(client), sign_in(client)
    path = "/nutrition-scanner/history"
    payload = {"barcode": "036000291452"}
    first = client.post(path, json=payload, headers=owner)
    assert first.status_code == 200
    second = client.post(path, json=payload, headers=owner)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert client.get(path, headers=owner).json() == [second.json()]
    assert client.get(path, headers=other).json() == []
    record_path = f"{path}/{first.json()['id']}"
    assert client.delete(record_path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).json() == []
