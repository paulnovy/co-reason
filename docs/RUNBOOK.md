# Runbook — Product Optimizer

## URLs
- Front: http://<host>:5173
- API: http://<host>:8000/docs

## Experiments endpoints (Sprint 1–3)
### DOE
- `POST /experiments/doe` — generate safe DOE points (sobol|lhs) within strict min/max
- `POST /experiments/doe/insight` — controlled-template narrative summary (**no LLM**)

### Optimize
- `POST /experiments/optimize` — random search within strict domain, supports:
  - `objective` (maximize/minimize variable)
  - `initial_points` (seed, e.g. from DOE) + strict domain validation
  - `max_initial_points` (server-side cap)
- `POST /experiments/optimize/insight` — controlled-template narrative summary (**no LLM**)

### Runs history
- `POST /runs` — persist run snapshot (request_json + response_json)
- `GET /runs` — list runs (filter: `run_type=doe|optimize`)
- `GET /runs/{id}` — fetch full run
- `DELETE /runs/{id}` — soft delete

## systemd user services
Recommended approach: run backend + frontend as `systemd --user` services.

### Install
```bash
mkdir -p ~/.config/systemd/user
cp scripts/systemd/product-optimizer-*.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now product-optimizer-api product-optimizer-front
```

### Restart
```bash
systemctl --user restart product-optimizer-api
systemctl --user restart product-optimizer-front
```

### Status
```bash
systemctl --user status product-optimizer-api product-optimizer-front
```

### Logs
```bash
journalctl --user -u product-optimizer-api -n 200 -f
journalctl --user -u product-optimizer-front -n 200 -f
```

## DB (PostgreSQL)
`docker-compose.yml` provides a dev Postgres instance.

```bash
sudo docker compose up -d db
```

## Quick smoke test (Sprint 3 DoD)
1) Front loads variables:
- open: `http://<host>:5173`
- verify: the list of Variables renders.

2) DOE run:
- click **Run DOE**
- select variables, Generate
- verify: table shows points and **Generate insight** works
- verify: a new entry appears in **Run history**

3) Optimize run (seed DOE):
- click **Run Optimize**
- click **Use DOE vars**
- verify objective var is included
- Run
- verify: best point + seeded count shown; **Generate insight** works
- verify: a new entry appears in **Run history**

4) History restore + replay:
- click a run entry → verify DOE/Optimize panel restores
- click **Replay** on a run → verify it creates a new "(replay)" run
- click **Delete** → verify run disappears from list

## DB note (dev vs prod)
API currently calls `init_db()` on startup (dev-friendly) to ensure tables exist. Production should use Alembic migrations.

## Troubleshooting
### Front tries port 5174
Port 5173 is already in use. Stop the old process, then restart the systemd service.

### API down
Restart the api unit:
```bash
systemctl --user restart product-optimizer-api
```
