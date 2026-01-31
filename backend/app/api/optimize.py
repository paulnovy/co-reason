from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.variable import Variable
from .objectives import ObjectiveSpec, ObjectiveKind


class OptimizeMethod(str, Enum):
    random = "random"


class OptimizeRequest(BaseModel):
    variable_ids: List[int] = Field(..., min_length=1)
    n_iter: int = Field(30, ge=1, le=5000)
    method: OptimizeMethod = Field(OptimizeMethod.random)
    seed: Optional[int] = None
    # IMPORTANT: set variable_id explicitly in the request; default is placeholder and will be rejected.
    objective: ObjectiveSpec = Field(default_factory=lambda: ObjectiveSpec(kind=ObjectiveKind.maximize_variable, variable_id=0))
    initial_points: List[Dict[str, float]] = Field(default_factory=list)
    max_initial_points: int = Field(200, ge=0, le=5000)


class OptimizeResponse(BaseModel):
    method: OptimizeMethod
    n_iter: int
    variable_ids: List[int]
    best_point: Dict[str, Any]
    history: List[Dict[str, Any]]
    meta: Dict[str, Any] = Field(default_factory=dict)


class OptimizeInsightRequest(BaseModel):
    variable_ids: List[int]
    best_point: Dict[str, float]
    meta: Dict[str, Any] = Field(default_factory=dict)


class OptimizeInsightResponse(BaseModel):
    summary: str
    bullets: List[str]
    meta: Dict[str, Any] = Field(default_factory=dict)


router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest, db: Session = Depends(get_db)) -> OptimizeResponse:
    if len(set(req.variable_ids)) != len(req.variable_ids):
        raise HTTPException(status_code=422, detail="variable_ids must be unique")

    variables = (
        db.query(Variable)
        .filter(Variable.id.in_(req.variable_ids), Variable.is_active == True)
        .all()
    )
    if len(variables) != len(req.variable_ids):
        found = {v.id for v in variables}
        missing = [vid for vid in req.variable_ids if vid not in found]
        raise HTTPException(status_code=404, detail={"missing_variable_ids": missing})

    by_id = {v.id: v for v in variables}
    ordered = [by_id[vid] for vid in req.variable_ids]

    unsafe = [v.id for v in ordered if v.min_value is None or v.max_value is None]
    if unsafe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"unsafe_variable_ids": unsafe, "reason": "min_value and max_value are required"},
        )

    import random

    rng = random.Random(req.seed)

    # Objective validation
    if req.objective.variable_id not in req.variable_ids:
        raise HTTPException(
            status_code=422,
            detail={"reason": "objective.variable_id must be included in variable_ids", "variable_id": req.objective.variable_id},
        )

    bounds = [(float(v.min_value), float(v.max_value)) for v in ordered]
    bounds_by_id = {str(v.id): (float(v.min_value), float(v.max_value)) for v in ordered}

    from .objectives import score_point as score_by_objective

    def score_point(p: Dict[str, Any]) -> float:
        # For now: explicit objective (maximize/minimize variable)
        return float(score_by_objective(p, req.objective))

    history: List[Dict[str, Any]] = []
    best_score = float("-inf")
    best_point: Dict[str, Any] = {}

    # Optional initial points (e.g., from DOE)
    if req.max_initial_points == 0:
        initial_iter = []
    else:
        initial_iter = req.initial_points[: req.max_initial_points]

    for p_in in initial_iter:
        p: Dict[str, Any] = {}
        for v in ordered:
            key = str(v.id)
            if key not in p_in:
                raise HTTPException(status_code=422, detail={"reason": "initial_points missing key", "missing_key": key})
            x = float(p_in[key])
            lo, hi = bounds_by_id[key]
            if x < lo or x > hi:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"reason": "initial_points out of domain", "variable_id": v.id, "value": x, "min": lo, "max": hi},
                )
            p[key] = x
        history.append(p)
        s = score_point(p)
        if s > best_score:
            best_score = s
            best_point = p

    # Random search iterations (stub)
    for _ in range(req.n_iter):
        p = {str(v.id): (lo + (hi - lo) * rng.random()) for (v, (lo, hi)) in zip(ordered, bounds)}
        history.append(p)
        s = score_point(p)
        if s > best_score:
            best_score = s
            best_point = p

    return OptimizeResponse(
        method=req.method,
        n_iter=req.n_iter,
        variable_ids=req.variable_ids,
        best_point=best_point,
        history=history,
        meta={
            "objective": req.objective.model_dump(),
            "best_score": best_score,
            "initial_points": len(initial_iter),
            "max_initial_points": req.max_initial_points,
            "n_iter": req.n_iter,
            "variable_order": [v.id for v in ordered],
            "domain": {
                str(v.id): {"min": v.min_value, "max": v.max_value, "unit": v.unit}
                for v in ordered
            },
        },
    )


@router.post("/optimize/insight", response_model=OptimizeInsightResponse)
def optimize_insight(req: OptimizeInsightRequest) -> OptimizeInsightResponse:
    """Controlled-template narrative for optimize results (no LLM)."""
    if len(set(req.variable_ids)) != len(req.variable_ids):
        raise HTTPException(status_code=422, detail="variable_ids must be unique")

    from .optimize_insight_templates import summarize_optimize_result

    insight = summarize_optimize_result(req.variable_ids, req.best_point, req.meta)
    return OptimizeInsightResponse(summary=insight.summary, bullets=insight.bullets, meta=insight.meta)
