from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class OptimizeInsight:
    summary: str
    bullets: List[str]
    meta: Dict[str, Any]


def summarize_optimize_result(variable_ids: List[int], best_point: Dict[str, float], meta: Dict[str, Any]) -> OptimizeInsight:
    bullets: List[str] = []

    n_iter = int(meta.get("n_iter") or meta.get("iterations") or 0) if isinstance(meta, dict) else 0
    best_score = meta.get("best_score") if isinstance(meta, dict) else None
    seeded = meta.get("initial_points") if isinstance(meta, dict) else None

    bullets.append("Optymalizacja wykonana bezpiecznie w granicach domen zmiennych (twarde min/max).")
    if seeded is not None:
        bullets.append(f"Seedowanie punktami startowymi: {seeded}.")
    if n_iter:
        bullets.append(f"Iteracje (random search): {n_iter}.")
    if best_score is not None:
        try:
            bullets.append(f"Najlepszy score (stub): {float(best_score):.4f}.")
        except Exception:
            bullets.append(f"Najlepszy score (stub): {best_score}.")

    # Render best_point values
    for vid in variable_ids:
        key = str(vid)
        if key in best_point:
            bullets.append(f"Best point — zmienna {key}: {float(best_point[key]):.4f}.")
        else:
            bullets.append(f"Best point — zmienna {key}: brak wartości (sprawdź payload).")

    return OptimizeInsight(
        summary="Optimize — szybkie podsumowanie",
        bullets=bullets,
        meta={"variable_ids": variable_ids},
    )
