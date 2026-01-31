# Product Optimizer — Loop Runner

Cel: praca autonomiczna w krótkich iteracjach, ale z twardym STOP o pełnej godzinie.

## Zasada
- Każda iteracja kończy się **zaplanowaniem kolejnej** (chain-of-events).
- Bezpiecznik: **nie planuj nic po najbliższej pełnej godzinie**.
- Raport wychodzi o pełnej godzinie.

## Mechanika (OpenClaw cron)
Używamy one-shot jobów (`schedule.kind=at`).
Po wykonaniu iteracji agent:
1) sprawdza aktualny czas i czas następnej pełnej godziny,
2) jeśli do pełnej godziny zostało >= N minut → dodaje kolejny job na +N minut,
3) jeśli < N minut → stop (czeka na pełną godzinę i review z Pawłem).

## Parametry
- tickMinutes: 5 (domyślnie)
- stopAtFullHour: true

## Pliki
- spec.md / implementation_plan.md — source of truth
- prompt.md — instrukcja iteracji
