from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ObjectiveKind(str, Enum):
    maximize_variable = "maximize_variable"
    minimize_variable = "minimize_variable"
    linear = "linear"


class LinearTerm(BaseModel):
    variable_id: int = Field(..., ge=1)
    weight: float = Field(...)


class ObjectiveSpec(BaseModel):
    kind: ObjectiveKind = Field(...)

    # for maximize/minimize variable
    variable_id: Optional[int] = Field(None, ge=1)
    weight: float = Field(1.0)

    # for linear objective
    terms: List[LinearTerm] = Field(default_factory=list)

    label: Optional[str] = None


def score_point(point: Dict[str, Any], obj: ObjectiveSpec) -> float:
    """Deterministic scoring (no LLM).

    - maximize_variable: +weight*x
    - minimize_variable: -weight*x
    - linear: sum_i weight_i * x_i
    """

    if obj.kind in (ObjectiveKind.maximize_variable, ObjectiveKind.minimize_variable):
        if obj.variable_id is None:
            raise ValueError("objective.variable_id is required")
        x = float(point[str(obj.variable_id)])
        if obj.kind == ObjectiveKind.maximize_variable:
            return float(obj.weight) * x
        return -float(obj.weight) * x

    if obj.kind == ObjectiveKind.linear:
        if not obj.terms:
            raise ValueError("objective.terms must be non-empty")
        score = 0.0
        for t in obj.terms:
            score += float(t.weight) * float(point[str(t.variable_id)])
        return score

    raise ValueError(f"Unsupported objective kind: {obj.kind}")
