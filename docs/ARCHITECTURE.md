# Architecture (Sprint 0)

## Principles
- Progressive modeling and layered variables.
- Trust-first UX: provenance everywhere.
- AI suggestions are never silently applied.

## Backend
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL (dev via docker)

Core entities:
- `Variable` (type, domain constraints, provenance, hierarchy)
- `Relationship` (directed, type/direction/shape, confidence)

## Frontend
- Vite + React + TypeScript
- ReactFlow for graph canvas

## Safety
- Domain constraints enforced server-side.
- Out-of-domain values must be clipped/rejected by backend when DOE/optimization is implemented.
