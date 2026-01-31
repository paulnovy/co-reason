from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class DoEInsight:
    summary: str
    bullets: List[str]
    meta: Dict[str, Any]


def summarize_doe_points(variable_ids: List[int], points: List[Dict[str, float]]) -> DoEInsight:
    # Compute per-variable min/max across points
    stats: Dict[str, Dict[str, float]] = {}
    for vid in variable_ids:
        key = str(vid)
        vals = [float(p[key]) for p in points if key in p]
        if not vals:
            continue
        stats[key] = {"min": min(vals), "max": max(vals)}

    bullets = [
        "DOE wygenerowano bezpiecznie w granicach domen zmiennych (twarde min/max).",
        f"Liczba punktów: {len(points)}.",
    ]

    for vid in variable_ids:
        key = str(vid)
        if key in stats:
            bullets.append(f"Zmienna {key}: zakres w DOE ≈ [{stats[key]['min']:.4f}, {stats[key]['max']:.4f}].")
        else:
            bullets.append(f"Zmienna {key}: brak danych w punktach (sprawdź payload).")

    summary = "DOE — szybkie podsumowanie"
    return DoEInsight(summary=summary, bullets=bullets, meta={"stats": stats})
