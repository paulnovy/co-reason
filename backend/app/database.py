import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .db_base import Base

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://optimizer:optimizer_pass@localhost:5432/optimizer_db",
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables (dev/test only; prefer Alembic in prod)."""
    # Import models so they register with Base.metadata
    from .models import variable as _variable  # noqa: F401
    from .models import relationship as _relationship  # noqa: F401
    Base.metadata.create_all(bind=engine)
