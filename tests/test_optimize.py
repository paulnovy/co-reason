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


def test_optimize_random_ok(client: TestClient):
    v1 = _create_var(client, "o1", 0.0, 1.0)
    v2 = _create_var(client, "o2", -2.0, 2.0)

    resp = client.post(
        "/experiments/optimize",
        json={"variable_ids": [v1, v2], "n_iter": 5, "method": "random", "seed": 42},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["history"]) == 5
    assert str(v1) in data["best_point"]
    assert str(v2) in data["best_point"]
    assert "domain" in data["meta"]
    assert str(v1) in data["meta"]["domain"]
    assert str(v2) in data["meta"]["domain"]


def test_optimize_rejects_missing_domain(client: TestClient):
    r = client.post("/variables", json={"name": "unsafe_opt"})
    assert r.status_code == 201
    vid = r.json()["id"]

    resp = client.post(
        "/experiments/optimize",
        json={"variable_ids": [vid], "n_iter": 3, "method": "random"},
    )
    assert resp.status_code == 422


def test_optimize_accepts_initial_points(client: TestClient):
    v1 = _create_var(client, "o3", 0.0, 1.0)
    v2 = _create_var(client, "o4", -2.0, 2.0)

    resp = client.post(
        "/experiments/optimize",
        json={
            "variable_ids": [v1, v2],
            "n_iter": 2,
            "method": "random",
            "seed": 1,
            "initial_points": [{str(v1): 0.5, str(v2): 0.0}],
            "max_initial_points": 200,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # history = initial_points + random iterations
    assert len(data["history"]) == 3
    assert data["meta"]["initial_points"] == 1


def test_optimize_rejects_initial_points_out_of_domain(client: TestClient):
    v1 = _create_var(client, "o5", 0.0, 1.0)

    resp = client.post(
        "/experiments/optimize",
        json={
            "variable_ids": [v1],
            "n_iter": 1,
            "method": "random",
            "seed": 1,
            "initial_points": [{str(v1): 2.0}],
        },
    )
    assert resp.status_code == 422


def test_optimize_limits_initial_points(client: TestClient):
    v1 = _create_var(client, "o6", 0.0, 1.0)

    resp = client.post(
        "/experiments/optimize",
        json={
            "variable_ids": [v1],
            "n_iter": 1,
            "method": "random",
            "seed": 1,
            "initial_points": [{str(v1): 0.1}, {str(v1): 0.2}, {str(v1): 0.3}],
            "max_initial_points": 2,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["meta"]["initial_points"] == 2
    assert data["meta"]["max_initial_points"] == 2
    assert len(data["history"]) == 3
