import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import Base, app, get_db


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        with TestSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_item(client):
    response = client.post(
        "/items",
        json={
            "name": "Keyboard",
            "description": "USB keyboard",
            "quantity": 5,
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Keyboard"
    assert response.json()["quantity"] == 5


def test_list_items(client):
    client.post("/items", json={"name": "Mouse", "quantity": 3})
    response = client.get("/items")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Mouse"


def test_get_missing_item(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_update_item(client):
    created = client.post(
        "/items",
        json={"name": "Monitor", "quantity": 2},
    )
    item_id = created.json()["id"]

    response = client.put(
        f"/items/{item_id}",
        json={"quantity": 4},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 4
    assert response.json()["name"] == "Monitor"


def test_delete_item(client):
    created = client.post(
        "/items",
        json={"name": "Webcam", "quantity": 1},
    )
    item_id = created.json()["id"]

    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_reject_negative_quantity(client):
    response = client.post(
        "/items",
        json={"name": "Keyboard", "quantity": -1},
    )
    assert response.status_code == 422
