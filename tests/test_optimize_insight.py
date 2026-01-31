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


def test_optimize_insight_ok(client: TestClient):
    resp = client.post(
        "/experiments/optimize/insight",
        json={
            "variable_ids": [1, 2],
            "best_point": {"1": 0.1, "2": 0.2},
            "meta": {"best_score": 0.3, "initial_points": 2, "n_iter": 5},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]
    assert len(data["bullets"]) >= 2


def test_optimize_insight_target_explains_score(client: TestClient):
    resp = client.post(
        "/experiments/optimize/insight",
        json={
            "variable_ids": [1],
            "best_point": {"1": 0.1},
            "meta": {
                "best_score": -0.2,
                "objective": {"kind": "target", "variable_id": 1, "target": 0.3, "loss": "abs"},
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any("score = -|x-target|" in b for b in data["bullets"])


def test_optimize_insight_rejects_duplicate_ids(client: TestClient):
    resp = client.post(
        "/experiments/optimize/insight",
        json={"variable_ids": [1, 1], "best_point": {"1": 0.1}, "meta": {}},
    )
    assert resp.status_code == 422
