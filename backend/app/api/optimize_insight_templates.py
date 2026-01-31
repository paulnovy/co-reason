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
    objective = meta.get("objective") if isinstance(meta, dict) else None
    domain = meta.get("domain") if isinstance(meta, dict) else None

    bullets.append("Optymalizacja wykonana bezpiecznie w granicach domen zmiennych (twarde min/max).")
    variable_names = meta.get("variable_names") if isinstance(meta, dict) else None

    if isinstance(objective, dict) and objective.get("kind"):
        kind = str(objective.get("kind"))
        if kind == "linear" and isinstance(objective.get("terms"), list):
            # Render a short human-readable linear objective
            parts = []
            for t in objective.get("terms")[:5]:
                if not isinstance(t, dict):
                    continue
                vid = str(t.get("variable_id"))
                w = t.get("weight")
                name = variable_names.get(vid) if isinstance(variable_names, dict) else None
                try:
                    w = float(w)
                    w_str = f"{w:.3g}"
                except Exception:
                    w_str = str(w)
                parts.append(f"{w_str}·{name or ('var ' + vid)}")
            more = "" if len(objective.get("terms")) <= 5 else f" (+{len(objective.get('terms'))-5} more)"
            norm = objective.get("normalize")
            norm_suffix = "" if not norm else f" (normalize={norm})"
            bullets.append("Cel: linear: " + " + ".join(parts) + more + norm_suffix + ".")
        elif kind == "target" and objective.get("variable_id") is not None:
            vid = str(objective.get("variable_id"))
            tgt = objective.get("target")
            loss = objective.get("loss") or "abs"
            vname = variable_names.get(vid) if isinstance(variable_names, dict) else None
            name = vname or ("var " + vid)
            bullets.append(f"Cel: target ({name}) → {tgt} (loss={loss}).")
        elif objective.get("variable_id"):
            vid = str(objective.get("variable_id"))
            vname = None
            if isinstance(variable_names, dict):
                vname = variable_names.get(vid)
            if vname:
                bullets.append(f"Cel: {kind} ({vname}, variable_id={vid}).")
            else:
                bullets.append(f"Cel: {kind} (variable_id={vid}).")
        else:
            bullets.append(f"Cel: {kind}.")
    if seeded is not None:
        bullets.append(f"Seedowanie punktami startowymi: {seeded}.")
    if n_iter:
        bullets.append(f"Iteracje (random search): {n_iter}.")
    if best_score is not None:
        try:
            bullets.append(f"Najlepszy score: {float(best_score):.4f}.")
        except Exception:
            bullets.append(f"Najlepszy score: {best_score}.")

    # Render best_point values
    for vid in variable_ids:
        key = str(vid)
        if key in best_point:
            unit = ""
            if isinstance(domain, dict):
                unit = str((domain.get(key) or {}).get("unit") or "")
            bullets.append(f"Best point — zmienna {key}: {float(best_point[key]):.4f}{unit}.")
        else:
            bullets.append(f"Best point — zmienna {key}: brak wartości (sprawdź payload).")

    return OptimizeInsight(
        summary="Optimize — szybkie podsumowanie",
        bullets=bullets,
        meta={"variable_ids": variable_ids},
    )
