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

AI-assisted admissions decision-support system for inVision U. The repository contains a FastAPI backend, a Next.js committee workspace, PostgreSQL persistence, demo fixtures, scoring assets, and synchronized English/Russian documentation for the current runtime state.

---

## Document Structure

- [Overview](#overview)
- [Runtime Stages](#runtime-stages)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Docker](#docker)

---

## Overview

The platform supports the work of the admissions committee from candidate submission to committee review. The current implementation includes:

- a video-first input flow with required `contacts.email` and `content.video_url`
- optional ASR transcription for interview audio or video
- privacy separation before any model-facing processing
- structured signal extraction from safe candidate content
- candidate scoring, confidence estimation, and ranking
- explanation blocks with evidence and caution signals
- role-based committee review for `admin`, `chair`, and `reviewer`
- PostgreSQL-backed persistence for candidates, scores, explanations, committee decisions, and audit events
- a local Docker stack for `postgres + backend + frontend`

The system remains human-in-the-loop: AI outputs are advisory, committee recommendations are auditable, and the final decision belongs to the admissions workflow rather than to the model layer.

---

## Runtime Stages

The current pipeline is documented as runtime stages rather than as internal `M*` package names:

- `Input Intake` - validates incoming candidate payloads and creates the base candidate record
- `ASR` - produces transcript text from candidate audio or video material when media is available
- `Privacy` - separates PII, operational metadata, and safe model content
- `Profile` - assembles the canonical candidate profile from safe and operational layers
- `Extraction` - extracts structured decision signals from text and transcript evidence
- `AI Detect` - adds supplementary authenticity and AI-assisted-writing checks
- `Scoring` - computes the candidate score, confidence, ranking, and recommendation bands
- `Explanation` - produces reviewer-facing summaries, factor blocks, and caution markers
- `Review` - exposes committee workspaces, chair decisions, and audit history
- `Storage` - persists candidates, projections, scores, explanations, and committee events

Supporting layers:

- `Gateway` - public API entrypoint and pipeline orchestration
- `Demo Layer` - demo fixtures and demo execution routes

Internal code packages still use `m*` names for now. The public documentation uses stage names and keeps package mapping in the module catalog.

---

## Repository Layout

```text
.agent/
  memory/                  local project memory and notes for agent work
backend/
  app/
    core/                  configuration, database, security, dependencies
    modules/               backend runtime packages
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

Create a local env file from `.env.example` and set `GROQ_API_KEY` for the active Llama-based pipeline path. The embedding backend runs locally.

Install backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Run the backend:

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

Current UI behavior:

- `/login` is the default entry route
- `/candidates` shows the live candidate pool split into `raw` and `processed`
- `/dashboard` shows processed candidate ranking and candidate detail views
- `/upload` handles form submission, JSON submission, and demo scenario launch
- `/admin/users` manages committee accounts and roles
- `/audit` is available to administrators for audit review

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

---
