# inVision U Architecture Diagrams

These diagrams are derived from [ARCHITECTURE.md](./ARCHITECTURE.md).

They describe the intended system architecture and the expected product flow.
Use them as a visual companion to the detailed architecture document.

GitHub supports Mermaid diagrams directly in Markdown, so this file should render in the repository UI without extra tooling.

## 1. System Overview

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

## 2. Candidate Submission Pipeline

```mermaid
sequenceDiagram
    actor Candidate
    participant FE as Frontend
    participant API as M1 API Gateway
    participant Intake as M2 Intake
    participant Privacy as M3 Privacy
    participant Profile as M4 Profile
    participant ASR as M13 ASR
    participant NLP as M5 NLP
    participant Score as M6 Scoring
    participant Explain as M7 Explainability
    participant Dash as M8 Dashboard API

    Candidate->>FE: Submit application
    FE->>API: POST /api/v1/pipeline/submit
    API->>Intake: Validate payload and create candidate
    Intake-->>API: candidate_id
    API->>Privacy: Split into 3 privacy layers
    Privacy-->>API: Layer 1, Layer 2, Layer 3
    API->>Profile: Build CandidateProfile
    alt Video is provided
        API->>ASR: Transcribe interview
        ASR-->>API: Transcript and quality flags
    end
    API->>NLP: Extract signals from safe input
    NLP-->>API: SignalEnvelope
    API->>Score: Compute score and ranking fields
    Score-->>API: CandidateScore
    API->>Explain: Build explanation and evidence
    Explain-->>API: CandidateExplanation
    API->>Dash: Persist dashboard-ready data
    API-->>FE: Score, status, and explanation
```

## 3. Privacy-by-Design Model

```mermaid
flowchart TD
    Raw["Raw Candidate Payload"]
    M3["M3 Privacy and Normalization"]

    subgraph Layer1["Layer 1: Secure PII Vault"]
        PII1["Full name"]
        PII2["IIN and document data"]
        PII3["Address and contacts"]
        PII4["Parent or guardian data"]
    end

    subgraph Layer2["Layer 2: Operational Metadata"]
        META1["Age eligibility"]
        META2["Language threshold flag"]
        META3["Has video"]
        META4["Completeness and data flags"]
    end

    subgraph Layer3["Layer 3: Safe Model Input"]
        SAFE1["Redacted transcript"]
        SAFE2["Essay text"]
        SAFE3["Project descriptions"]
        SAFE4["Internal test answers"]
        SAFE5["Experience summary"]
    end

    AI["AI and ML Modules"]

    Raw --> M3
    M3 --> Layer1
    M3 --> Layer2
    M3 --> Layer3
    Layer3 --> AI

    Layer1 -. never sent .-> AI
    Layer2 -. not used for leadership scoring .-> AI
```

## 4. Scoring and Explainability Flow

```mermaid
flowchart LR
    Profile["CandidateProfile"]
    Signals["M5 SignalEnvelope"]
    Rules["Rule-based Scoring"]
    ML["ML Aggregation"]
    Confidence["Confidence and Uncertainty"]
    Score["CandidateScore"]
    Explain["M7 Explainability"]
    Dashboard["Reviewer Dashboard"]

    Profile --> Signals
    Signals --> Rules
    Signals --> ML
    Rules --> Confidence
    ML --> Confidence
    Confidence --> Score
    Score --> Explain
    Signals --> Explain
    Explain --> Dashboard
```

## 5. Reviewer Workflow

```mermaid
flowchart TD
    Ranking["Ranking Page"]
    Detail["Candidate Detail Page"]
    Explanation["Explanation Block"]
    Evidence["Evidence List"]
    Override["Reviewer Override"]
    Shortlist["Shortlist Decision"]
    Audit["Audit Log"]

    Ranking --> Detail
    Detail --> Explanation
    Detail --> Evidence
    Detail --> Override
    Override --> Shortlist
    Override --> Audit
    Shortlist --> Audit
```

## 6. Core Data Model

```mermaid
erDiagram
    candidates ||--o| candidate_pii : has
    candidates ||--o| candidate_metadata : has
    candidates ||--o| candidate_model_inputs : has
    candidates ||--o| nlp_signals : has
    candidates ||--o| candidate_scores : has
    candidates ||--o| candidate_explanations : has
    candidates ||--o{ reviewer_actions : has

    candidates {
        uuid id PK
        uuid intake_id
        string selected_program
        string pipeline_status
        timestamp created_at
        timestamp updated_at
    }

    candidate_pii {
        uuid id PK
        uuid candidate_id FK
        bytes encrypted_data
        timestamp created_at
    }

    candidate_metadata {
        uuid id PK
        uuid candidate_id FK
        boolean age_eligible
        boolean language_threshold_met
        boolean has_video
        float data_completeness
        jsonb data_flags
        timestamp created_at
    }

    candidate_model_inputs {
        uuid id PK
        uuid candidate_id FK
        text video_transcript
        text essay_text
        jsonb internal_test_answers
        jsonb project_descriptions
        text experience_summary
        float asr_confidence
        jsonb asr_flags
        timestamp created_at
    }

    nlp_signals {
        uuid id PK
        uuid candidate_id FK
        jsonb signals
        string model_used
        int processing_time_ms
        timestamp created_at
    }

    candidate_scores {
        uuid id PK
        uuid candidate_id FK
        jsonb sub_scores
        float review_priority_index
        string recommendation_status
        float confidence
        boolean shortlist_eligible
        int ranking_position
        string scoring_version
        timestamp created_at
    }

    candidate_explanations {
        uuid id PK
        uuid candidate_id FK
        text summary
        jsonb positive_factors
        jsonb caution_flags
        jsonb data_quality_notes
        text reviewer_guidance
        timestamp created_at
    }

    reviewer_actions {
        uuid id PK
        uuid candidate_id FK
        string reviewer_id
        string action_type
        string previous_status
        string new_status
        text comment
        timestamp created_at
    }
```

## Usage Notes

- Prefer linking this file from the repository root `README.md`.
- Keep `ARCHITECTURE.md` as the source of truth and update diagrams when module responsibilities change.
- If a diagram stops rendering on GitHub, it usually means Mermaid syntax needs a small cleanup rather than a platform issue.
