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


def test_doe_insight_ok(client: TestClient):
    resp = client.post(
        "/experiments/doe/insight",
        json={
            "variable_ids": [1, 2],
            "points": [{"1": 0.1, "2": 0.2}, {"1": 0.3, "2": 0.4}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]
    assert len(data["bullets"]) >= 2
    assert "stats" in data["meta"]


def test_doe_insight_rejects_duplicate_ids(client: TestClient):
    resp = client.post(
        "/experiments/doe/insight",
        json={"variable_ids": [1, 1], "points": [{"1": 0.1}]},
    )
    assert resp.status_code == 422
