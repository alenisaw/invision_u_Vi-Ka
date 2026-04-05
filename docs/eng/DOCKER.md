# Docker Guide

## Active stack

The live local stack is defined in:

- `docker-compose.yml`

Services:

- `postgres`
- `backend`
- `frontend`

## Runtime behavior

- `backend` runs Alembic migrations on startup and then starts `uvicorn`
- `frontend` receives `BACKEND_URL`
- frontend authentication uses session cookies through the backend proxy
- role access is enforced on the backend through RBAC
- the main external secret for the default analytical path is `GROQ_API_KEY`

## Commands

```bash
./scripts/stack.sh up
./scripts/stack.sh down
./scripts/stack.sh reset
./scripts/stack.sh logs
```

## Service topology

```mermaid
flowchart LR
    subgraph ClientLayer["Client Layer"]
        Browser["Browser"]
        Frontend["frontend"]
    end

    subgraph ApiLayer["API Layer"]
        Backend["backend"]
    end

    subgraph DataLayer["Data Layer"]
        DB["postgres"]
    end

    Browser --> Frontend
    Frontend --> Backend
    Backend --> DB

    style ClientLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style ApiLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style DataLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```
