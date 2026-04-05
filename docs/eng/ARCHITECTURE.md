# System Architecture

---

## Document Structure

- [System Overview](#system-overview)
- [Diagram 1. End-to-End Stage Flow](#diagram-1-end-to-end-stage-flow)
- [Architectural Principles](#architectural-principles)
- [Runtime Stages](#runtime-stages)
- [Public Stage Map](#public-stage-map)
- [Data Management Model](#data-management-model)
- [Diagram 2. Data Separation Layers](#diagram-2-data-separation-layers)
- [Diagram 3. Committee Workflow](#diagram-3-committee-workflow)
- [Diagram 4. Frontend and API Surface](#diagram-4-frontend-and-api-surface)
- [Repository Structure](#repository-structure)

---

## System Overview

The inVision U admissions platform is a modular monolith for admissions decision support. The repository contains both the FastAPI backend and the Next.js committee workspace.

The current runtime operates as a synchronous request-response pipeline:

- candidate input enters through the input intake stage or through the full gateway pipeline
- `ASR` runs when public audio or video material is available
- `Privacy` separates PII before any model-facing processing
- `Profile`, `Extraction`, `AI Detect`, `Scoring`, and `Explanation` assemble the analytical view
- `Review` exposes committee actions, chair approval, and audit visibility
- all state is persisted in PostgreSQL

The platform is explicitly human-in-the-loop:

- it does not make an autonomous admissions decision
- it surfaces confidence, evidence, and caution signals
- it keeps sensitive data outside model-facing stages
- it records committee actions and final decisions

---

## Diagram 1. End-to-End Stage Flow

```mermaid
flowchart LR
    subgraph InputLayer["Input Layer"]
        Candidate["Candidate Submission"]
        Demo["Demo Scenario"]
        Gateway["Gateway"]
        Intake["Input Intake"]
    end

    subgraph ProcessingLayer["Processing Layer"]
        ASR["ASR"]
        Privacy["Privacy"]
        Profile["Profile"]
        Extraction["Extraction"]
        AIDetect["AI Detect"]
        Scoring["Scoring"]
        Explanation["Explanation"]
    end

    subgraph DecisionLayer["Decision Layer"]
        Workspace["Committee Workspace"]
        Review["Review"]
    end

    subgraph StorageLayer["Persistence Layer"]
        DB["PostgreSQL"]
    end

    Candidate --> Gateway
    Demo --> Gateway
    Gateway --> Intake
    Intake --> ASR
    Intake --> Privacy
    ASR --> Privacy
    Privacy --> Profile
    Profile --> Extraction
    Extraction --> AIDetect
    Extraction --> Scoring
    AIDetect -. supplementary signals .-> Scoring
    Scoring --> Explanation
    Explanation --> Workspace
    Workspace --> Review

    Intake -. persist .-> DB
    Privacy -. persist .-> DB
    Profile -. persist .-> DB
    Extraction -. persist .-> DB
    Scoring -. persist .-> DB
    Explanation -. persist .-> DB
    Review -. persist .-> DB

    style InputLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style ProcessingLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style DecisionLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style StorageLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Architectural Principles

### Privacy by Design

PII is isolated before any model-facing processing. AI and ML stages operate only on safe content and operationally permitted metadata.

### Explainability First

Scores must remain reviewable. Committee users see factor blocks, caution markers, evidence snippets, and final explanation summaries rather than a single opaque output.

### Human in the Loop

Recommendations are advisory. Final admissions handling stays inside the committee workflow, where reviewer recommendations and chair decisions are recorded explicitly.

### Session Auth and RBAC

Protected routes use HTTP-only session cookies and backend role checks for `admin`, `chair`, and `reviewer`. Role visibility determines who can manage users, see global audit data, or view committee decisions.

### Synchronous Core Pipeline

The default local stack uses synchronous orchestration inside the API process. The active Docker stack does not require a separate worker tier for the baseline review workflow.

---

## Runtime Stages

### Gateway

Public API entrypoint and orchestration layer for synchronous pipeline execution, batch submission, and committee-facing backend routes.

### Input Intake

The input stage validates candidate payloads, computes initial completeness, and creates the base candidate record. It is documented as an input stage rather than as a standalone analytical module.

### ASR

Consumes public audio or video links and produces transcript text plus transcript quality metadata when media is available.

### Privacy

Splits the candidate record into PII, operational metadata, and safe model content.

### Profile

Builds the canonical candidate profile from operational and safe layers.

### Extraction

Converts safe text, transcript material, and related evidence into structured decision signals.

### AI Detect

Adds supplementary authenticity and AI-assisted-writing indicators. These signals do not replace committee judgment; they act as caution inputs for scoring and explanation.

### Scoring

Computes candidate score, confidence, ranking, recommendation category, and review routing.

### Explanation

Transforms score and evidence into reviewer-facing narrative, factor blocks, and caution summaries.

### Review

Powers candidate workspaces, committee recommendations, chair decisions, and audit visibility.

### Storage

Persists candidate layers, projections, score outputs, explanation outputs, and committee events.

---

## Public Stage Map

The documentation uses public stage names. Current package mapping in code:

| Public stage | Current package |
|---|---|
| `Gateway` | `backend/app/modules/gateway` |
| `Input Intake` | `backend/app/modules/intake` |
| `ASR` | `backend/app/modules/asr` |
| `Privacy` | `backend/app/modules/privacy` |
| `Profile` | `backend/app/modules/profile` |
| `Extraction` | `backend/app/modules/extraction` |
| `AI Detect` | `backend/app/modules/extraction/ai_detector.py` |
| `Scoring` | `backend/app/modules/scoring` |
| `Explanation` | `backend/app/modules/explanation` |
| `Review` | `backend/app/modules/workspace` and `backend/app/modules/review` |
| `Storage` | `backend/app/modules/storage` |
| `Demo Layer` | `backend/app/modules/demo` |

---

## Data Management Model

### Layer 1: Secure PII

Stores encrypted or protected identity data: legal names, contacts, addresses, document references, and related administrative data.

### Layer 2: Operational Metadata

Stores workflow-visible metadata such as selected program, completeness, data flags, and intake-derived eligibility markers.

### Layer 3: Safe Analytical Content

Stores redacted transcript text, essay text when present, transcript-derived fallback content, internal answers, and safe evidence for downstream analytical stages.

---

## Diagram 2. Data Separation Layers

```mermaid
flowchart TD
    Raw["Candidate Payload"]
    Privacy["Privacy"]

    subgraph PII["Layer 1: Secure PII"]
        L1A["Identity and Contacts"]
        L1B["Address and Documents"]
        L1C["Family and Guardians"]
    end

    subgraph Metadata["Layer 2: Operational Metadata"]
        L2A["Program and Intake Metadata"]
        L2B["Completeness and Flags"]
        L2C["Workflow State"]
    end

    subgraph Safe["Layer 3: Safe Analytical Content"]
        L3A["Transcript Text"]
        L3B["Essay or Transcript Fallback"]
        L3C["Internal Answers"]
        L3D["Evidence for Extraction"]
    end

    subgraph Models["Analytical Stages"]
        Profile["Profile"]
        Extraction["Extraction"]
        AIDetect["AI Detect"]
        Scoring["Scoring"]
        Explanation["Explanation"]
    end

    Raw --> Privacy
    Privacy --> PII
    Privacy --> Metadata
    Privacy --> Safe
    Safe --> Profile
    Profile --> Extraction
    Extraction --> AIDetect
    Extraction --> Scoring
    AIDetect -. caution signals .-> Scoring
    Scoring --> Explanation
    PII -. never sent .-> Models

    style PII fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Metadata fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Safe fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Models fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Diagram 3. Committee Workflow

```mermaid
flowchart LR
    Candidate["Candidate Detail"]
    Reviewer["Reviewer"]
    Chair["Chair"]
    Admin["Admin"]
    Recommendation["Reviewer Recommendation"]
    Final["Final Chair Decision"]
    Audit["Audit Feed"]

    Candidate --> Reviewer
    Candidate --> Chair

    Reviewer --> Recommendation
    Recommendation -. visible to chair .-> Chair
    Chair --> Final
    Final -. visible to reviewer as final result .-> Reviewer
    Recommendation -. visible to admin .-> Admin
    Final -. visible to admin .-> Admin
    Recommendation --> Audit
    Final --> Audit

    style Recommendation fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Final fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Audit fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Diagram 4. Frontend and API Surface

```mermaid
flowchart LR
    subgraph UI["Frontend Workspace"]
        Login["/login"]
        Pool["/candidates"]
        Ranking["/dashboard"]
        Detail["/dashboard/[id]"]
        Upload["/upload"]
        Users["/admin/users"]
        AuditPage["/audit"]
    end

    subgraph API["Backend API"]
        Auth["Auth"]
        Gateway["Gateway"]
        Review["Review"]
        Admin["Admin"]
    end

    Login --> Auth
    Pool --> Review
    Ranking --> Review
    Detail --> Review
    Upload --> Gateway
    Users --> Admin
    AuditPage --> Admin

    style UI fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style API fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Repository Structure

```text
backend/app/core/             config, db session, auth, RBAC dependencies
backend/app/modules/          runtime packages for gateway, stages, review, storage
backend/tests/                unit, integration, and evaluation coverage
frontend/src/app/             Next.js routes and API proxy
frontend/src/components/      shared UI and candidate-review components
docs/eng/                     English project documentation
docs/rus/                     Russian project documentation
```
