from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.experiment_run import ExperimentRun, ExperimentRunType


router = APIRouter(prefix="/runs", tags=["runs"])


class RunType(str, Enum):
    doe = "doe"
    optimize = "optimize"


class CreateRunRequest(BaseModel):
    run_type: RunType
    title: Optional[str] = None
    request_json: Dict[str, Any] = Field(default_factory=dict)
    response_json: Dict[str, Any] = Field(default_factory=dict)


class RunResponse(BaseModel):
    id: int
    run_type: RunType
    title: Optional[str]
    request_json: Dict[str, Any]
    response_json: Dict[str, Any]
    created_at: str
    updated_at: str


class DeleteRunResponse(BaseModel):
    ok: bool = True


class RunListResponse(BaseModel):
    items: List[RunResponse]
    total: int
    skip: int
    limit: int


def _to_response(r: ExperimentRun) -> RunResponse:
    return RunResponse(
        id=r.id,
        run_type=RunType(r.run_type.value),
        title=r.title,
        request_json=r.request_json or {},
        response_json=r.response_json or {},
        created_at=r.created_at.isoformat().replace("+00:00", "Z"),
        updated_at=r.updated_at.isoformat().replace("+00:00", "Z"),
    )


@router.post("", response_model=RunResponse)
def create_run(payload: CreateRunRequest, db: Session = Depends(get_db)) -> RunResponse:
    obj = ExperimentRun(
        run_type=ExperimentRunType(payload.run_type.value),
        title=payload.title,
        request_json=payload.request_json,
        response_json=payload.response_json,
        is_active=True,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return _to_response(obj)


@router.get("", response_model=RunListResponse)
def list_runs(
    run_type: Optional[RunType] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> RunListResponse:
    q = db.query(ExperimentRun).filter(ExperimentRun.is_active == True)
    if run_type is not None:
        q = q.filter(ExperimentRun.run_type == ExperimentRunType(run_type.value))

    total = q.count()
    items = q.order_by(ExperimentRun.created_at.desc()).offset(skip).limit(limit).all()

    return RunListResponse(
        items=[_to_response(r) for r in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)) -> RunResponse:
    obj = db.query(ExperimentRun).filter(ExperimentRun.id == run_id, ExperimentRun.is_active == True).first()
    if obj is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="run not found")
    return _to_response(obj)


@router.delete("/{run_id}", response_model=DeleteRunResponse)
def delete_run(run_id: int, db: Session = Depends(get_db)) -> DeleteRunResponse:
    obj = db.query(ExperimentRun).filter(ExperimentRun.id == run_id, ExperimentRun.is_active == True).first()
    if obj is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="run not found")

    obj.is_active = False
    db.add(obj)
    db.commit()
    return DeleteRunResponse(ok=True)
