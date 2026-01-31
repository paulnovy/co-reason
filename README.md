# Product Optimizer (co-reason)

Human‑AI Co‑Reasoning Workspace for progressive modeling, trustworthy DOE, and optimization of complex physical/hybrid systems.

## Current status (Sprint 0)
- FastAPI backend with Variables + Relationships models (provenance + domain constraints).
- React frontend (Vite) running in LAN (baseline: variables list; graph work-in-progress behind feature flag).
- PostgreSQL supported (docker compose), tests use SQLite.

## Quick start (dev)

### Prereqs
- Python 3.11+ (venv)
- Node 18+ / npm
- Optional: Docker for PostgreSQL

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# optional: start postgres
cd ..
sudo docker compose up -d db

# init tables (dev)
cd backend
python -c "from app.database import init_db; init_db()"

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Frontend: http://localhost:5173

### Tests
```bash
./backend/venv/bin/python -m pytest -q
```

## Running as supervised services (recommended)
We run the dev services as `systemd --user` services so the assistant can restart safely without breaking its work loop.

See:
- `scripts/systemd/product-optimizer-api.service`
- `scripts/systemd/product-optimizer-front.service`
- `docs/RUNBOOK.md`

## License
TBD
