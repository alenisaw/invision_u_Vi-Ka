# inVision U Candidate Selection System
![Python](https://img.shields.io/badge/Python-3.10.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-template-2496ED?logo=docker&logoColor=white)
![LLM](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-4285F4)
![ASR](https://img.shields.io/badge/ASR-Whisper_Large_V3_Turbo-F57C00)
![Embeddings](https://img.shields.io/badge/Embeddings-Jina_v5_%7C_BGE--M3-7B1FA2)
![ML](https://img.shields.io/badge/ML-GradientBoostingRegressor-2E7D32)

---

AI-assisted admissions decision-support backend for inVision U. The repository contains candidate intake, privacy separation, ASR transcription, NLP signal extraction, scoring, ranking, and explainability modules designed for human-in-the-loop review.

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

The system ingests candidate submissions, isolates sensitive data, prepares safe model input, extracts structured evaluation signals, computes explainable scores, and produces reviewer-facing explanations. It supports the admissions committee and does not make fully autonomous final decisions.

---

## Implemented Modules

- `M1 Gateway`: API routing and backend pipeline orchestration.
- `M2 Intake`: candidate intake validation and initial persistence.
- `M3 Privacy`: three-layer separation of PII, metadata, and model-safe content.
- `M4 Profile`: unified candidate profile assembly.
- `M5 NLP`: structured signal extraction from safe candidate content.
- `M6 Scoring`: program-aware scoring, ranking, confidence, and review routing.
- `M7 Explainability`: reviewer-facing summaries, factor blocks, cautions, and evidence.
- `M8 Dashboard`: reviewer-facing dashboard API with safe candidate identity projection.
- `M10 Audit`: reviewer overrides, reviewer actions, and audit feed APIs.
- `M13 ASR`: interview transcription and transcript quality analysis.

---

## Repository Layout

```text
backend/
  app/
    core/                  configuration, database, security
    modules/               backend modules
    schemas/               shared API envelopes
  tests/                   unit, integration, and evaluation tests
docs/
  eng/                     English documentation
  rus/                     Russian documentation
frontend/
  STYLE_GUIDE.md           visual reference from the frontend branch
```

---

## Quick Start

Install backend dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Run the backend:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run backend tests:

```bash
cd backend && python -m pytest tests -q
```

Reviewer dashboard access:

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/dashboard/stats
```

`M8` dashboard endpoints require the `X-API-Key` header.
Candidate names are returned only through a reviewer projection layer that derives a safe `name` from encrypted PII. Raw snapshots, contacts, documents, addresses, and family data are never exposed by reviewer routes.

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

- [Архитектура](docs/rus/ARCHITECTURE.md)
- [API](docs/rus/API.md)
- [Скоринг и правила решений](docs/rus/SCORING.md)
- [Каталог модулей](docs/rus/MODULES.md)
- [Docker Guide RU](docs/rus/DOCKER.md)

---

## Docker

The repository includes a whole-repository Docker template:

- [docker-compose.template.yml](docker-compose.template.yml)

It defines placeholders for:

- `postgres`
- `backend`
- `frontend`
- `M8 Dashboard`
- `M10 Audit`

---

Projet Documentation
