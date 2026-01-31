# Product Optimizer — Sprint 2 (Optimization stub + provenance UX polish)

## Cel
Zrobić następny cienki slice: po DOE użytkownik może uruchomić **bezpieczną optymalizację** (na razie stub + sanity constraints) oraz zobaczyć provenance konsekwentnie w UI.

## Zakres (must-have)
1) **Optimization (safe stub)**
- Endpoint: `POST /experiments/optimize`
- Wejście: `variable_ids`, `objective` (na razie placeholder), `n_iter`, `method` (na start: random within domain)
- Twarde constraints: każdy variable musi mieć min/max.
- Wyjście: `best_point`, `history` (lista punktów), meta.

2) **Frontend provenance polish**
- W widoku listy oraz w wynikach DOE/insight: oznaczyć provenance kolorem (HARD_DATA/USER_INPUT/AI_SUGGESTION/MIXED).

## Safety
- Backend zawsze waliduje domain. Brak domeny → reject.

## Out of scope
- Pełna BO/DEAP (to Sprint 3)
- Zaawansowane wykresy
