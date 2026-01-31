from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..db_base import Base


class ExperimentRunType(str, PyEnum):
    DOE = "doe"
    OPTIMIZE = "optimize"


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    run_type: Mapped[ExperimentRunType] = mapped_column(
        Enum(ExperimentRunType, name="experiment_run_type_enum", create_type=True),
        nullable=False,
        index=True,
    )

    # simple label for UI/history
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # payload + result snapshots
    # Use generic JSON so tests can run on SQLite; Postgres will store as JSON/JSONB depending on dialect.
    request_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ExperimentRun(id={self.id}, type={self.run_type.value})>"
