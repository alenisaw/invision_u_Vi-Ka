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
- frontend-аутентификация использует session cookie через backend proxy
- доступ по ролям ограничивается на backend через RBAC
- основной внешний секрет для стандартного аналитического пути: `GROQ_API_KEY`

## Команды

```bash
./scripts/stack.sh up
./scripts/stack.sh down
./scripts/stack.sh reset
./scripts/stack.sh logs
```

## Топология сервисов

```mermaid
flowchart LR
    subgraph ClientLayer["Клиентский слой"]
        Browser["Browser"]
        Frontend["frontend"]
    end

    subgraph ApiLayer["API слой"]
        Backend["backend"]
    end

    subgraph DataLayer["Слой данных"]
        DB["postgres"]
    end

    Browser --> Frontend
    Frontend --> Backend
    Backend --> DB

    style ClientLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style ApiLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style DataLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```
