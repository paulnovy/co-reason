# Product Optimizer — Sprint 1 (Thin Vertical Slice)

## Cel
Zbudować pierwszy cienki „end‑to‑end” slice, który dowodzi kluczowej wartości: użytkownik tworzy model, uruchamia bezpieczny DOE i dostaje zrozumiałe insighty.

## Zakres (must‑have)
1) **Model creation**
- CRUD zmiennych + relacji (już jest).
- Każda zmienna ma: typ (category), constraints (min/max/unit), provenance (source+confidence).

2) **DOE (safe)**
- Endpoint backendu: `POST /experiments/doe`.
- Wejście: lista `variable_id` + liczba punktów + metoda (`sobol` lub `lhs`).
- Silnik generuje punkty **tylko w domenie** (twarde min/max). Jeśli domena nieznana → reject/"unsafe".
- Wyjście: macierz punktów + metadane (seed, metoda).

3) **Insight (narrative, kontrolowany szablon)**
- Endpoint backendu: `POST /experiments/doe/insight`.
- Wejście: DOE points + opcjonalne wyniki (jeśli mamy funkcję celu później).
- Wyjście: krótka narracja wg template (bez "silent writes").

4) **Frontend (MVP)**
- Widok listy zmiennych (stable) + przycisk „Run DOE”.
- Modal: wybór zmiennych + metoda + liczba punktów.
- Wynik: tabela + proste wykresy (na start można tabela + placeholder wykresów).
- UI pokazuje provenance (kolor) w całym flow.

## Safety / Trust
- Backend enforce: domain clipping/reject.
- Provenance zawsze widoczna.
- AI nie może generować wartości poza domeną; jeśli brak domeny → "unsafe".

## Out of scope
- Optymalizacja (Sprint 2)
- Pełny AI Assistant panel
- Zaawansowane wykresy
