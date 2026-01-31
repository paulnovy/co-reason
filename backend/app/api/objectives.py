from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ObjectiveKind(str, Enum):
    maximize_variable = "maximize_variable"
    minimize_variable = "minimize_variable"


class ObjectiveSpec(BaseModel):
    kind: ObjectiveKind = Field(...)
    variable_id: int = Field(..., ge=1)
    weight: float = Field(1.0)
    label: Optional[str] = None


def score_point(point: Dict[str, Any], obj: ObjectiveSpec) -> float:
    x = float(point[str(obj.variable_id)])
    if obj.kind == ObjectiveKind.maximize_variable:
        return obj.weight * x
    if obj.kind == ObjectiveKind.minimize_variable:
        return -obj.weight * x
    # Defensive fallback
    raise ValueError(f"Unsupported objective kind: {obj.kind}")
