# Docker Guide

## Актуальный стек

Основной локальный стек описан в:

- `docker-compose.yml`

Сервисы:

- `postgres`
- `backend`
- `frontend`

## Текущее поведение

- `backend` на старте прогоняет Alembic migrations и затем запускает `uvicorn`
- `frontend` получает `BACKEND_URL`
- аутентификация frontend идет через session cookie и backend proxy
- основной внешний секрет для стандартного model path: `GROQ_API_KEY`

## Команды

```bash
./scripts/stack.sh up
./scripts/stack.sh down
./scripts/stack.sh reset
./scripts/stack.sh logs
```

## Топология

```mermaid
flowchart LR
    Frontend["frontend"]
    Backend["backend"]
    DB["postgres"]

    Frontend --> Backend
    Backend --> DB
```
