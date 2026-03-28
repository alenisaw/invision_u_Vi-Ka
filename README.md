# inVision U Candidate Selection System

AI-assisted decision-support platform for the inVision U admissions process.
The system ingests candidate applications, isolates sensitive data, extracts structured signals, computes explainable scores, and prepares reviewer-facing ranking outputs.

## Core Principles

- Privacy by design: PII is separated before AI or scoring modules see candidate data.
- Explainability first: every recommendation should be traceable to signals and evidence.
- Human in the loop: the system supports reviewers and does not replace final human judgment.
- Modular architecture: each stage of the pipeline is isolated as a dedicated service module.

## Architecture Overview

```mermaid
flowchart LR
    Candidate["Candidate Input"]
    Frontend["Next.js Frontend"]
    M1["M1 API Gateway"]
    M2["M2 Intake"]
    M3["M3 Privacy and Normalization"]
    L1["Layer 1: PII Vault"]
    L2["Layer 2: Operational Metadata"]
    L3["Layer 3: Model Input"]
    M4["M4 Candidate Profile"]
    M5["M5 NLP Signal Extraction"]
    M13["M13 ASR Transcription"]
    M6["M6 Scoring and Ranking"]
    M7["M7 Explainability"]
    M8["M8 Reviewer Dashboard API"]
    M10["M10 Audit Service"]
    Reviewer["Reviewer"]

    Candidate --> Frontend
    Frontend --> M1
    M1 --> M2
    M2 --> M3
    M3 --> L1
    M3 --> L2
    M3 --> L3
    L3 --> M4
    M4 --> M5
    L3 --> M13
    M13 --> M5
    M5 --> M6
    M6 --> M7
    M7 --> M8
    M8 --> Frontend
    Reviewer --> Frontend
    M1 --> M10
    M6 --> M10
    M8 --> M10
```

## Current Repository Focus

- `backend/` contains the FastAPI backend, scoring logic, privacy layer, profile assembly, and storage models.
- `frontend/` is the planned dashboard workspace for upload, ranking, and reviewer detail flows.
- `docs/ARCHITECTURE.md` contains the full architecture definition and module responsibilities.
- `docs/API.md` describes the current and planned API surface.

## Key Backend Modules

- `M1 Gateway`: request entry point and pipeline orchestration.
- `M2 Intake`: candidate intake validation and record creation.
- `M3 Privacy`: three-layer data separation and redaction.
- `M4 Profile`: unified candidate profile assembly.
- `M5 NLP`: signal extraction contract and heuristic extraction path.
- `M6 Scoring`: rule-based and ML-assisted candidate scoring.
- `M7 Explainability`: explanation handoff and reviewer-facing reasoning layer.
- `M8 Dashboard API`: ranking, shortlist, and candidate detail endpoints.
- `M10 Audit`: governance and traceability support.

## Minimal Working Element

The repository already includes a minimally working backend scoring element for Stage 1:

- canonical signal scoring endpoint: `POST /api/v1/pipeline/score-signals`
- intake endpoint: `POST /api/v1/candidates/intake`
- scoring engine and synthetic evaluation tests under `backend/tests/m6_scoring/`

## Documentation

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- API reference: [docs/API.md](docs/API.md)
