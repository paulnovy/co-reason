# Notes for next iteration

## Frontend visual check
- Headless Chrome screenshots from the mini-PC render as white (likely JS not executing in headless mode for Vite dev / HMR), so they are not a reliable visual check.
- Better approach for true visual validation: attach an interactive Chrome tab via OpenClaw browser relay (extension) or use a non-headless browser session.

## Current UX state
- Baseline: variable list (stable) backed by `/variables`.
- Feature flag approach: keep baseline stable; run graph/DOE UI behind flag/route.

## Sprint 1 plan reminder
- Task 2: implement DOE point generation (Sobol first) with strict domain enforcement (min/max required).
- Task 3: tests for out-of-domain reject + deterministic seed.
- Task 4/5: Front modal "Run DOE" + results table.

## Implementation ideas (DOE)
- Use `scipy.stats.qmc.Sobol` if scipy is acceptable dependency; otherwise implement simple LHS first.
- Domain enforcement rule: every variable must have both min_value and max_value; otherwise mark unsafe and reject request with 422.
- Output points schema: list of dicts keyed by variable_id or variable_name (decide and standardize; prefer variable_id string keys for stability).
