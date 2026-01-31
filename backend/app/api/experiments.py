from enum import Enum
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models.variable import Variable


class DoEMethod(str, Enum):
    sobol = "sobol"
    lhs = "lhs"


class DoERequest(BaseModel):
    variable_ids: List[int] = Field(..., min_length=1, description="IDs of variables included in DOE")
    n_points: int = Field(20, ge=1, le=5000, description="Number of DOE points to generate")
    method: DoEMethod = Field(DoEMethod.sobol, description="Sampling method")
    seed: int | None = Field(None, description="Optional RNG seed")


class DoEResponse(BaseModel):
    method: DoEMethod
    n_points: int
    variable_ids: List[int]
    points: List[Dict[str, Any]] = Field(default_factory=list, description="List of experiment points")
    meta: Dict[str, Any] = Field(default_factory=dict)


class DoEInsightRequest(BaseModel):
    variable_ids: List[int]
    points: List[Dict[str, float]]


class DoEInsightResponse(BaseModel):
    summary: str
    bullets: List[str]
    meta: Dict[str, Any] = Field(default_factory=dict)


router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("/doe", response_model=DoEResponse)
def run_doe(req: DoERequest, db: Session = Depends(get_db)) -> DoEResponse:
    """Generate safe DOE points within strict variable domain constraints."""

    if len(set(req.variable_ids)) != len(req.variable_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="variable_ids must be unique",
        )

    variables = (
        db.query(Variable)
        .filter(Variable.id.in_(req.variable_ids), Variable.is_active == True)
        .all()
    )

    if len(variables) != len(req.variable_ids):
        found = {v.id for v in variables}
        missing = [vid for vid in req.variable_ids if vid not in found]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"missing_variable_ids": missing},
        )

    # Preserve input order
    by_id = {v.id: v for v in variables}
    ordered = [by_id[vid] for vid in req.variable_ids]

    # Strict domain constraints: min and max must be known
    unsafe = [v.id for v in ordered if v.min_value is None or v.max_value is None]
    if unsafe:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"unsafe_variable_ids": unsafe, "reason": "min_value and max_value are required"},
        )

    bounds = [(float(v.min_value), float(v.max_value)) for v in ordered]

    points: List[Dict[str, Any]] = []

    if req.method == DoEMethod.sobol:
        from scipy.stats import qmc

        d = len(bounds)
        sampler = qmc.Sobol(d=d, scramble=True, seed=req.seed)
        # SciPy Sobol supports arbitrary n via .random()
        unit = sampler.random(n=req.n_points)

        for row in unit:
            p: Dict[str, Any] = {}
            for (v, u, (lo, hi)) in zip(ordered, row, bounds):
                val = lo + (hi - lo) * float(u)
                p[str(v.id)] = val
            points.append(p)

    elif req.method == DoEMethod.lhs:
        from scipy.stats import qmc

        d = len(bounds)
        sampler = qmc.LatinHypercube(d=d, seed=req.seed)
        unit = sampler.random(n=req.n_points)

        for row in unit:
            p: Dict[str, Any] = {}
            for (v, u, (lo, hi)) in zip(ordered, row, bounds):
                val = lo + (hi - lo) * float(u)
                p[str(v.id)] = val
            points.append(p)

    else:
        raise HTTPException(status_code=422, detail="Unknown DOE method")

    return DoEResponse(
        method=req.method,
        n_points=req.n_points,
        variable_ids=req.variable_ids,
        points=points,
        meta={
            "variable_order": [v.id for v in ordered],
            "domain": {str(v.id): {"min": v.min_value, "max": v.max_value, "unit": v.unit} for v in ordered},
        },
    )


@router.post("/doe/insight", response_model=DoEInsightResponse)
def doe_insight(req: DoEInsightRequest) -> DoEInsightResponse:
    """Controlled-template narrative for DOE results (no LLM; trust-first)."""

    if len(set(req.variable_ids)) != len(req.variable_ids):
        raise HTTPException(status_code=422, detail="variable_ids must be unique")

    from .insight_templates import summarize_doe_points

    insight = summarize_doe_points(req.variable_ids, req.points)
    return DoEInsightResponse(summary=insight.summary, bullets=insight.bullets, meta=insight.meta)
