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

    # Import models so tables exist
    from backend.app.models import variable as _variable  # noqa: F401
    from backend.app.models import relationship as _relationship  # noqa: F401

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


def _create_var(client: TestClient, name: str, lo: float, hi: float) -> int:
    r = client.post("/variables", json={"name": name, "min_value": lo, "max_value": hi})
    assert r.status_code == 201
    return r.json()["id"]


def test_doe_sobol_points_within_domain(client: TestClient):
    v1 = _create_var(client, "v1", 0.0, 10.0)
    v2 = _create_var(client, "v2", -5.0, 5.0)

    resp = client.post(
        "/experiments/doe",
        json={"variable_ids": [v1, v2], "n_points": 8, "method": "sobol", "seed": 123},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["method"] == "sobol"
    assert len(data["points"]) == 8

    for p in data["points"]:
        assert 0.0 <= p[str(v1)] <= 10.0
        assert -5.0 <= p[str(v2)] <= 5.0


def test_doe_rejects_duplicate_ids(client: TestClient):
    v1 = _create_var(client, "vdup", 0.0, 1.0)
    resp = client.post(
        "/experiments/doe",
        json={"variable_ids": [v1, v1], "n_points": 10, "method": "sobol"},
    )
    assert resp.status_code == 422


def test_doe_rejects_missing_domain(client: TestClient):
    # create a variable without domain
    r = client.post("/variables", json={"name": "unsafe"})
    assert r.status_code == 201
    vid = r.json()["id"]

    resp = client.post(
        "/experiments/doe",
        json={"variable_ids": [vid], "n_points": 4, "method": "sobol"},
    )
    assert resp.status_code == 422
