import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base
from backend.app.deps import get_db


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


def test_create_variable_success(client):
    resp = client.post("/variables", json={"name": "var1", "min": 0, "max": 10})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "var1"


def test_create_variable_invalid_range(client):
    resp = client.post("/variables", json={"name": "var2", "min": 5, "max": 1})
    assert resp.status_code == 422


def test_create_variable_duplicate(client):
    client.post("/variables", json={"name": "dup", "min": 0, "max": 5})
    resp = client.post("/variables", json={"name": "dup", "min": 0, "max": 5})
    assert resp.status_code == 409


def test_list_variables(client):
    client.post("/variables", json={"name": "a", "min": 0, "max": 2})
    client.post("/variables", json={"name": "b", "min": 1, "max": 3})
    resp = client.get("/variables")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
