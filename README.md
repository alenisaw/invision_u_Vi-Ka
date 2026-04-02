# inVision U Candidate Selection System
![Python](https://img.shields.io/badge/Python-3.10.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Llama_4_Scout_17B_16E_Instruct-4285F4)
![ASR](https://img.shields.io/badge/ASR-Whisper_Large_V3_Turbo-F57C00)
![Embeddings](https://img.shields.io/badge/Embeddings-Jina_v5_%7C_BGE--M3-7B1FA2)
![ML](https://img.shields.io/badge/ML-GradientBoostingRegressor-2E7D32)

---

AI-assisted admissions decision-support system for inVision U. The repository contains a FastAPI backend, a Next.js reviewer frontend, PostgreSQL persistence, demo fixtures, scoring evaluation assets, and synchronized English/Russian project documentation.

---

## Document Structure

- [Overview](#overview)
- [Implemented Modules](#implemented-modules)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Docker](#docker)

---

## Overview

The system ingests candidate submissions, isolates sensitive data, prepares safe model input, extracts structured evaluation signals, computes explainable scores, and exposes reviewer-facing ranking and detail views.

The current branch is a full-stack implementation with:

- synchronous pipeline submission through `POST /api/v1/pipeline/submit`
- Groq-backed `M5` extraction by default with `meta-llama/llama-4-scout-17b-16e-instruct`
- local embeddings through `jinaai/jina-embeddings-v5-text-nano`
- localized reviewer dashboard, candidate pool, upload, shortlist, and audit pages in `frontend/`
- PostgreSQL-backed persistence for candidate layers, scores, explanations, reviewer actions, and audit logs
- a local Docker stack for `postgres + backend + frontend`

The platform remains human-in-the-loop: recommendation categories are advisory and reviewer overrides are logged.

---

## Implemented Modules

- `M0 Demo`: demo candidate fixtures and demo-run endpoints
- `M1 Gateway`: API routing and backend pipeline orchestration
- `M2 Intake`: candidate intake validation and initial persistence
- `M3 Privacy`: three-layer separation of PII, metadata, and model-safe content
- `M4 Profile`: unified candidate profile assembly
- `M5 NLP`: structured signal extraction from safe candidate content
- `M6 Scoring`: program-aware scoring, ranking, confidence, and review routing
- `M7 Explainability`: reviewer-facing summaries, factor blocks, cautions, and evidence
- `M8 Dashboard`: reviewer-facing dashboard API with safe candidate identity projection
- `M9 Storage`: SQLAlchemy models and repository layer
- `M10 Audit`: reviewer overrides, reviewer actions, and audit feed APIs
- `M13 ASR`: interview transcription and transcript quality analysis

---

## Repository Layout

```text
.agent/
  memory/                  local project memory and notes for agent work
backend/
  app/
    core/                  configuration, database, security, dependencies
    modules/               backend modules M0-M13
    schemas/               shared API envelopes
  tests/                   unit, integration, and evaluation tests
docs/
  eng/                     English documentation
  rus/                     Russian documentation
frontend/
  src/                     Next.js app router, pages, components, proxy
  e2e/                     Playwright smoke coverage
scripts/
  stack.sh                 docker compose helper
```

---

## Quick Start

Create a local env file from `.env.example` and set `GROQ_API_KEY` for the active Llama-based pipeline path. The embedding model runs locally without a Jina API key.

The local embedding model is downloaded from Hugging Face on first use and then reused from the local cache.

Install backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Run the backend from the repository root:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Run backend tests:

```bash
cd backend
python -m pytest tests -q
```

Reviewer dashboard access:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/dashboard/stats
```

Reviewer routes under `dashboard/*` and `audit/*` require `X-API-Key`.
When using the Next.js frontend, the built-in proxy under `/api/backend/*` injects the reviewer key server-side for those routes.

Current UI behavior:

- `/candidates` shows the live candidate pool split into `raw` and `processed`
- demo fixtures are launched from `/upload`, not mixed into the live candidate list
- upload is video-first: `contacts.email` and `content.video_url` are required, `content.essay_text` is optional
- when essay text is missing, narrative extraction can fall back to the ASR transcript

Run the M6 evaluation bundle:

```bash
python backend/tests/m6_scoring/run_evaluation.py
```

---

## Documentation

English:

- [Architecture](docs/eng/ARCHITECTURE.md)
- [API Reference](docs/eng/API.md)
- [Scoring Policy](docs/eng/SCORING.md)
- [Module Catalog](docs/eng/MODULES.md)
- [Docker Guide](docs/eng/DOCKER.md)

Russian:

- [Architecture RU](docs/rus/ARCHITECTURE.md)
- [API RU](docs/rus/API.md)
- [Scoring RU](docs/rus/SCORING.md)
- [Module Catalog RU](docs/rus/MODULES.md)
- [Docker Guide RU](docs/rus/DOCKER.md)

---

## Docker

The repository includes a runnable whole-project Docker Compose setup:

- [docker-compose.yml](docker-compose.yml)

Start everything:

```bash
./scripts/stack.sh up
```

Run in background:

```bash
./scripts/stack.sh up -d
```

Stop containers:

```bash
./scripts/stack.sh down
```

Reset containers and database volume:

```bash
./scripts/stack.sh reset
```

The stack exposes:

- `frontend` on `http://localhost:3000`
- `backend` on `http://localhost:8000`
- `postgres` on `localhost:5432`

`docker-compose.template.yml` remains in the repository as an older scaffold, but the active local stack is `docker-compose.yml`.

---

Projet Documentation
