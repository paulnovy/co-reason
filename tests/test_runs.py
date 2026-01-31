import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db_base import Base
from backend.app.deps import get_db


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from backend.app.models import variable as _variable  # noqa: F401
    from backend.app.models import relationship as _relationship  # noqa: F401
    from backend.app.models import experiment_run as _experiment_run  # noqa: F401

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


def test_runs_create_list_get(client: TestClient):
    r = client.post(
        "/runs",
        json={
            "run_type": "doe",
            "title": "test doe",
            "request_json": {"x": 1},
            "response_json": {"y": 2},
        },
    )
    assert r.status_code == 200
    created = r.json()
    assert created["id"]

    r = client.get("/runs")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(item["id"] == created["id"] for item in data["items"])

    r = client.get(f"/runs/{created['id']}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == created["id"]


def test_runs_filter_by_type(client: TestClient):
    client.post("/runs", json={"run_type": "doe", "request_json": {}, "response_json": {}})
    client.post("/runs", json={"run_type": "optimize", "request_json": {}, "response_json": {}})

    r = client.get("/runs?run_type=doe")
    assert r.status_code == 200
    assert all(item["run_type"] == "doe" for item in r.json()["items"])

    r = client.get("/runs?run_type=optimize")
    assert r.status_code == 200
    assert all(item["run_type"] == "optimize" for item in r.json()["items"])
