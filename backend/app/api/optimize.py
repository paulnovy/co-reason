from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.variable import Variable


class OptimizeMethod(str, Enum):
    random = "random"


class OptimizeRequest(BaseModel):
    variable_ids: List[int] = Field(..., min_length=1)
    n_iter: int = Field(30, ge=1, le=5000)
    method: OptimizeMethod = Field(OptimizeMethod.random)
    seed: Optional[int] = None
    initial_points: List[Dict[str, float]] = Field(default_factory=list)


class OptimizeResponse(BaseModel):
    method: OptimizeMethod
    n_iter: int
    variable_ids: List[int]
    best_point: Dict[str, Any]
    history: List[Dict[str, Any]]
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

    bounds = [(float(v.min_value), float(v.max_value)) for v in ordered]
    bounds_by_id = {str(v.id): (float(v.min_value), float(v.max_value)) for v in ordered}

    def score_point(p: Dict[str, Any]) -> float:
        score = 0.0
        for (v, (lo, hi)) in zip(ordered, bounds):
            x = float(p[str(v.id)])
            score += (x - lo) / (hi - lo) if hi > lo else 0.0
        return score

    history: List[Dict[str, Any]] = []
    best_score = float("-inf")
    best_point: Dict[str, Any] = {}

    # Optional initial points (e.g., from DOE)
    for p_in in req.initial_points:
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
            "objective": "stub:maximize_normalized_sum",
            "best_score": best_score,
            "initial_points": len(req.initial_points),
            "variable_order": [v.id for v in ordered],
            "domain": {
                str(v.id): {"min": v.min_value, "max": v.max_value, "unit": v.unit}
                for v in ordered
            },
        },
    )
