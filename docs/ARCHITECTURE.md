# inVision U — AI Candidate Selection System
## Full System Architecture

**Project:** Decentrathon 5.0 — AI inDrive Track
**Deadline:** April 5, 2026, 23:59
**Architecture:** Modular Monolith
**Stack:** FastAPI + Next.js + PostgreSQL + Docker

---

## 1. System Overview

An AI-driven decision-support system for the inVision U admissions committee. The system analyzes candidate applications, video transcripts, and internal test responses to produce explainable multi-dimensional scores and a ranked shortlist. **The system supports the committee — it does not replace human judgment.**

### Core Principles
- **Human-in-the-loop**: Every AI recommendation is reviewed by a human. No autonomous admit/reject.
- **Explainability-first**: Every score has traceable evidence. No black-box outputs.
- **Privacy-by-design**: PII is isolated from the scoring pipeline at the architecture level.
- **Fairness**: No demographic, geographic, or socioeconomic signals used in scoring.

---

## 2. Tech Stack

### Backend
| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | FastAPI + Python 3.11+ | Async support, Pydantic v2, fast dev |
| ORM | SQLAlchemy (async) + Alembic | Type-safe, migrations |
| Database | PostgreSQL 16 | Relational, JSONB for flexible fields |
| Validation | Pydantic v2 | Schema enforcement at boundaries |
| Background tasks | FastAPI BackgroundTasks | Simple async jobs, no Redis for MVP |
| File handling | python-multipart | Upload support |
| HTTP client | httpx (async) | API calls to LLM providers |
| Containerization | Docker + docker-compose | Local dev and deployment |

### Frontend
| Component | Technology | Reason |
|-----------|-----------|--------|
| Framework | Next.js 14 (App Router) | SSR, routing, API routes |
| Language | TypeScript | Type safety |
| UI Library | shadcn/ui + Tailwind CSS | Fast, accessible, customizable |
| Data fetching | TanStack Query v5 | Caching, background refetch |
| Charts | Recharts | Score visualization |
| Tables | TanStack Table v8 | Sortable ranking table |
| Forms | React Hook Form + Zod | Validation, upload |

### AI / ML Models

#### LLM — Signal Extraction & Explanation
| Model | Provider | Use Case | Tier |
|-------|----------|----------|------|
| `Qwen3.5-72B-Instruct` | OpenRouter | Deep signal extraction, explanation generation | Primary |
| `Qwen3.5-7B-Instruct` | OpenRouter | Fast field-level classification, consistency checks | Secondary / High-volume |
| `Llama-3.3-70B` | Groq (free) | Fallback / validation cross-check | Fallback |

**Why Qwen family:**
- Truly open-source (Apache 2.0)
- Best-in-class multilingual quality (English + Russian)
- 128k context window (fits full application + transcript)
- Available via OpenRouter pay-per-use (no subscription lock)
- Strong structured output (JSON mode)

#### Embeddings — Semantic Similarity & Program Fit
| Model | Runtime | Use Case |
|-------|---------|----------|
| `BAAI/bge-m3` | Local (GPU) via HuggingFace | Essay ↔ transcript consistency, program fit matching |
| `paraphrase-multilingual-mpnet-base-v2` | Local (CPU fallback) | Lighter alternative if VRAM constrained |

#### ASR — Video Transcription
| Model | Runtime | Use Case |
|-------|---------|----------|
| `faster-whisper large-v3` | Local (GPU, ~3GB VRAM) | Primary: RU+EN transcription |
| Groq Whisper API | API | Fallback if local fails / faster processing |

**ASR Pipeline Rules:**
- Extract audio only — video frame data never enters the pipeline
- Store: transcript text, timestamps, language tags, confidence per segment
- Flag for human review if: confidence < 0.75 on >30% of segments, duration < 60s, [unclear] segments > 20%

#### AI Writing Detection
- Heuristic layer: perplexity estimation via Qwen API (high perplexity = more human-like)
- Consistency check: cosine similarity (BAAI/bge-m3) between essay embeddings ↔ transcript embeddings
- Output: `authenticity_flag` (0.0–1.0 advisory score) + reasoning text
- **Never auto-reject. Advisory only.**

#### ML Scoring Layer
| Component | Library | Approach |
|-----------|---------|----------|
| Rule-based engine | Pure Python | Deterministic weights, threshold logic |
| ML aggregator | scikit-learn | GradientBoostingRegressor on synthetic data |
| Confidence intervals | scipy | Uncertainty quantification |
| Feature engineering | pandas + numpy | Sub-score aggregation |

---

## 3. Data Governance — 3-Layer Model

This is enforced at the infrastructure level, not just policy.

### Layer 1: Secure PII Vault (`candidate_pii` table)
**Never sent to LLM, embeddings model, or scoring engine.**

Fields stored here:
- Full name (last, first, patronymic)
- IIN (Individual Identification Number)
- Document number, authority, issue date
- Passport scan (file reference only)
- Home address (country, region, city, street, house, apartment)
- Phone number
- Social media handles (Instagram, Telegram, WhatsApp)
- Parent/guardian full names and phones
- Social status documents and details
- Any uploaded document files

Access: Admin panel only. Never passed to `m5_nlp`, `m6_scoring`, or any AI module.

### Layer 2: Operational Metadata (`candidate_profiles.metadata` JSONB)
**Visible to platform for validation — not used in leadership/potential scoring.**

Fields:
- `candidate_id` (UUID, anonymized)
- Date of birth → used only for age eligibility check (binary: eligible/not)
- Gender → not used in scoring
- Citizenship → used only for application category check
- Document type → administrative
- IELTS/TOEFL score → binary eligibility flag only (`language_threshold_met: bool`)
- Video link → technical reference
- File upload status flags
- Selected program name

### Layer 3: Model Input (`candidate_profiles.model_input` JSONB)
**This is the only data sent to AI models.**

Fields:
- `anonymized_id` (UUID)
- `video_transcript` (string, ASR output, redacted)
- `internal_test_answers` (array of {question_id, answer_text})
- `essay_text` (string, if present)
- `project_descriptions` (array of strings)
- `experience_summary` (string)
- `selected_program` (program name for fit context only)
- `data_quality_flags` (ASR confidence, missing fields, etc.)

**Auto-redaction applied before this layer:**
```
[NAME] → replaces names
[IIN]  → replaces IIN mentions
[DOB]  → replaces dates of birth
[PHONE] → replaces phone numbers
[SOCIAL_HANDLE] → replaces @mentions and social links
[ADDRESS] → replaces address mentions
[DOCUMENT_ID] → replaces document numbers
[RELATIVE_INFO] → replaces parent/guardian mentions
```

---

## 4. Module Architecture

### Overview Map
```
[Input: JSON / File Upload]
        ↓
M2. Candidate Intake Service
        ↓
M3. Privacy & Normalization Service
   ├── PII separation → Layer 1 storage
   ├── Metadata extraction → Layer 2
   └── Model input preparation → Layer 3 (auto-redaction)
        ↓
M4. Candidate Profile Service
   └── Assembles unified CandidateProfile
        ↓
    ┌───┴───┐
    ↓       ↓
M5. NLP   M13. ASR (if video provided)
Signal     Transcription
Extract    Service
    ↓       ↓
    └───┬───┘
        ↓
M6. Scoring & Ranking Engine
   ├── Rule-based layer
   └── ML aggregation layer
        ↓
M7. Explainability Service
   ├── Evidence extraction
   ├── Positive factors
   └── Caution flags
        ↓
M8. Reviewer Dashboard API ←→ M10. Audit Service
        ↓
[Frontend: Next.js Dashboard]
```

---

### M1. API Gateway & Orchestration Service
**Owner: Backend Engineer**

Responsibilities:
- Single entry point for all client requests
- Request validation and authentication (API key for MVP)
- Pipeline orchestration: coordinates M2→M3→M4→M5→M6→M7
- Error handling and response envelope
- Rate limiting (in-memory for MVP)

Key endpoints:
```
POST /api/v1/pipeline/submit          # Submit candidate, trigger full pipeline
POST /api/v1/pipeline/batch           # Submit multiple candidates
GET  /api/v1/pipeline/status/{job_id} # Check async job status
```

Pipeline execution modes:
- **Sync** (single candidate): runs full pipeline, returns result in one response (up to ~30s)
- **Async** (batch): returns job_id, status polling endpoint

---

### M2. Candidate Intake Service
**Owner: Backend Engineer**

Responsibilities:
- Accept candidate data in JSON format (primary) or form upload
- Parse and validate against intake schema
- Handle file uploads (video link extraction, document metadata)
- Create initial `candidates` DB record
- Return `candidate_id` for downstream processing

Input schema (JSON):
```json
{
  "personal": {
    "last_name": "...", "first_name": "...", "patronymic": "...",
    "date_of_birth": "YYYY-MM-DD", "gender": "M/F",
    "citizenship": "...", "iin": "...",
    "document_type": "...", "document_no": "...",
    "document_authority": "...", "document_date": "..."
  },
  "contacts": {
    "phone": "...", "instagram": "...", "telegram": "...", "whatsapp": "..."
  },
  "parents": {
    "father": {"last_name": "...", "first_name": "...", "phone": "..."},
    "mother": {"last_name": "...", "first_name": "...", "phone": "..."}
  },
  "address": {
    "country": "...", "region": "...", "city": "...",
    "street": "...", "house": "...", "apartment": "..."
  },
  "academic": {
    "selected_program": "Innovative IT Product Design and Development",
    "language_exam_type": "IELTS",
    "language_score": 7.0
  },
  "content": {
    "video_url": "https://...",
    "essay_text": "...",
    "project_descriptions": ["...", "..."],
    "experience_summary": "..."
  },
  "social_status": {
    "has_social_benefit": false,
    "benefit_type": null
  },
  "internal_test": {
    "answers": [
      {"question_id": "q1", "answer": "A"},
      ...
    ]
  }
}
```

---

### M3. Privacy & Normalization Service
**Owner: Backend Engineer**

Responsibilities:
- Separate intake data into 3 layers
- Store Layer 1 (PII) in encrypted `candidate_pii` table
- Build Layer 2 (operational metadata)
- Build Layer 3 (model input) with auto-redaction
- Normalize text: strip HTML, fix encoding, lowercase where appropriate
- Compute completeness score and missing data flags
- Validate language eligibility (binary check only)

Redaction logic (applied to all text before Layer 3):
```python
REDACTION_PATTERNS = {
    r'\bIIN\s*[\d-]+': '[IIN]',
    r'\b\d{12}\b': '[IIN]',
    r'@[\w.]+': '[SOCIAL_HANDLE]',
    r'\+?[\d\s()\-]{10,15}': '[PHONE]',
    # Names: replaced using NER (spaCy or API-based)
    # Addresses: replaced using pattern + NER
}
```

---

### M4. Candidate Profile Service
**Owner: Backend Engineer**

Responsibilities:
- Assemble unified `CandidateProfile` from 3 layers
- Compute `data_completeness_score` (0.0–1.0)
- Tag missing critical fields for human review
- Provide clean interface for downstream modules

CandidateProfile structure:
```python
@dataclass
class CandidateProfile:
    candidate_id: UUID
    selected_program: str
    model_input: ModelInput       # Layer 3 only
    metadata: CandidateMetadata   # Layer 2
    completeness: float           # 0.0–1.0
    data_flags: list[DataFlag]    # Missing/low quality fields
    created_at: datetime
```

---

### M5. NLP Signal Extraction Service
**Owner: NLP Engineer**

**This module never receives Layer 1 data. Input is Layer 3 only.**

Responsibilities:
- Call Qwen3.5-72B-Instruct via OpenRouter with structured prompts
- Extract signals from: video transcript, essay, test answers, project descriptions
- Return standardized signal JSON for M6

Signals extracted:

| Signal Group | Signal | Source |
|-------------|--------|--------|
| Leadership | leadership_indicators, responsibility_examples, team_leadership | transcript, essay |
| Growth | growth_trajectory, challenges_overcome, learning_agility | transcript, essay, experience |
| Motivation | motivation_clarity, goal_specificity, program_alignment | transcript, essay |
| Initiative | proactivity_examples, self_started_projects, agency_signals | essay, projects, transcript |
| Consistency | essay_transcript_consistency, claims_evidence_match | cross-source |
| Authenticity | ai_writing_risk, voice_consistency, specificity_score | essay, transcript |
| Thinking | decision_making_style, ethical_reasoning, civic_orientation | test answers |
| Communication | clarity_score, structure_score, idea_articulation | transcript |

Each signal:
```json
{
  "signal_name": "leadership_indicators",
  "value": 0.78,
  "confidence": 0.85,
  "evidence": ["Quote or example from source text"],
  "source": "video_transcript",
  "reasoning": "Candidate described leading a team of 5 in school project..."
}
```

LLM prompt strategy:
- Use **structured output mode** (JSON schema) for all Qwen calls
- One call per signal group (batch related signals)
- Temperature: 0.1 (deterministic extraction)
- System prompt includes explicit bias prohibition rules

AI Writing Detection:
```python
def detect_ai_writing(essay: str, transcript: str) -> AuthenticitySignal:
    # 1. Perplexity estimation via LLM logprobs (Qwen API)
    # 2. Embedding cosine similarity: essay vs transcript
    # 3. Specificity check: concrete examples vs generic statements
    # 4. Voice consistency: vocabulary overlap, sentence patterns
    return AuthenticitySignal(
        ai_risk_score=0.0-1.0,
        voice_consistency=0.0-1.0,
        advisory_flag="possible_ai_use" | "authentic" | "review_needed",
        reasoning="..."
    )
```

---

### M6. Scoring & Ranking Engine
**Owner: ML Engineer**

**Input: M5 signal JSON. Never receives raw candidate data.**

Architecture: 2-layer hybrid

#### Layer A: Rule-based scoring
```python
SCORING_WEIGHTS = {
    # Aligned with hackathon judging criteria and ТЗ priorities
    "leadership_potential":    0.20,  # Primary: detect future leaders
    "growth_trajectory":       0.18,  # Primary: journey over achievements
    "motivation_clarity":      0.15,  # Program fit and genuine drive
    "initiative_agency":       0.15,  # Self-starters
    "learning_agility":        0.12,  # Ability to grow in university
    "communication_clarity":   0.10,  # Can articulate ideas
    "ethical_reasoning":       0.05,  # Values alignment
    "program_fit":             0.05,  # Relevance to selected program
}
```

Missing data penalty:
```python
def apply_missing_data_penalty(score: float, completeness: float) -> float:
    if completeness < 0.5:
        return score * 0.7  # significant penalty
    elif completeness < 0.75:
        return score * 0.85
    return score
```

#### Layer B: ML aggregation
- Model: `GradientBoostingRegressor` (scikit-learn)
- Training: synthetic data (200–500 labeled profiles generated for demo)
- Features: all signal values + confidence scores + completeness
- Output: calibrated final score

Sub-scores produced:
```json
{
  "candidate_id": "uuid",
  "sub_scores": {
    "leadership_potential": 0.78,
    "growth_trajectory": 0.82,
    "motivation_clarity": 0.71,
    "initiative_agency": 0.69,
    "learning_agility": 0.85,
    "communication_clarity": 0.73,
    "ethical_reasoning": 0.80,
    "program_fit": 0.76
  },
  "review_priority_index": 0.77,
  "recommendation_status": "STRONG_RECOMMEND",
  "confidence": 0.83,
  "uncertainty_flag": false,
  "shortlist_eligible": true,
  "ranking_position": null
}
```

Recommendation statuses:
| Status | Threshold | Meaning |
|--------|-----------|---------|
| `STRONG_RECOMMEND` | RPI ≥ 0.75 | Priority review, likely admit |
| `RECOMMEND` | 0.60 ≤ RPI < 0.75 | Solid candidate, review recommended |
| `REVIEW_NEEDED` | 0.45 ≤ RPI < 0.60 | Uncertain, human review required |
| `LOW_SIGNAL` | RPI < 0.45 or completeness < 0.5 | Insufficient data or weak signals |
| `MANUAL_REVIEW` | Any uncertainty_flag = true | Edge cases, flagged issues |

---

### M7. Explainability Service
**Owner: NLP Engineer (evidence layer) + ML Engineer (score aggregation)**

Responsibilities:
- Generate human-readable explanation for each score
- Extract top positive factors with evidence quotes
- Extract caution flags with reasoning
- Format for dashboard display

Output:
```json
{
  "candidate_id": "uuid",
  "summary": "Candidate demonstrates strong growth trajectory and initiative...",
  "positive_factors": [
    {
      "factor": "Strong leadership indicators",
      "evidence": "Led a youth volunteer project organizing 40+ participants",
      "source": "video_transcript",
      "score_contribution": "+0.12"
    }
  ],
  "caution_flags": [
    {
      "flag": "Essay-transcript consistency gap",
      "description": "Written essay uses noticeably different vocabulary from spoken presentation",
      "severity": "advisory",
      "action": "human_review"
    }
  ],
  "data_quality_notes": [
    "Video transcript confidence: 0.91 (high)",
    "Internal test: fully completed"
  ],
  "reviewer_guidance": "Pay attention to the gap between written and spoken communication styles."
}
```

---

### M8. Reviewer Dashboard Service (API layer)
**Owner: Backend Engineer (API) + Frontend Engineer (UI)**

API endpoints:
```
GET  /api/v1/dashboard/ranking              # Full ranked candidate list
GET  /api/v1/dashboard/shortlist            # Shortlist only
GET  /api/v1/dashboard/candidates/{id}      # Full candidate detail
GET  /api/v1/dashboard/candidates/{id}/explanation
POST /api/v1/dashboard/candidates/{id}/override  # Reviewer override
GET  /api/v1/dashboard/stats                # Summary stats
GET  /api/v1/dashboard/export/shortlist     # CSV/JSON export
```

---

### M9. Storage Layer
**Owner: Backend Engineer**

Database: PostgreSQL 16

Tables:
```sql
-- Candidate base record
candidates (
  id UUID PRIMARY KEY,
  intake_id UUID,
  selected_program VARCHAR,
  pipeline_status VARCHAR,  -- pending/processing/completed/failed
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

-- Layer 1: PII (separate, access-controlled)
candidate_pii (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  encrypted_data BYTEA,  -- AES-256 encrypted JSON blob
  created_at TIMESTAMP
)

-- Layer 2: Operational metadata
candidate_metadata (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  age_eligible BOOLEAN,
  language_threshold_met BOOLEAN,
  language_exam_type VARCHAR,
  has_video BOOLEAN,
  data_completeness FLOAT,
  data_flags JSONB,
  created_at TIMESTAMP
)

-- Layer 3: Model input (redacted)
candidate_model_inputs (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  video_transcript TEXT,
  essay_text TEXT,
  internal_test_answers JSONB,
  project_descriptions JSONB,
  experience_summary TEXT,
  asr_confidence FLOAT,
  asr_flags JSONB,
  created_at TIMESTAMP
)

-- NLP signals
nlp_signals (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  signals JSONB,  -- full signal JSON from M5
  model_used VARCHAR,
  processing_time_ms INTEGER,
  created_at TIMESTAMP
)

-- Scores
candidate_scores (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  sub_scores JSONB,
  review_priority_index FLOAT,
  recommendation_status VARCHAR,
  confidence FLOAT,
  shortlist_eligible BOOLEAN,
  ranking_position INTEGER,
  scoring_version VARCHAR,
  created_at TIMESTAMP
)

-- Explanations
candidate_explanations (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  summary TEXT,
  positive_factors JSONB,
  caution_flags JSONB,
  data_quality_notes JSONB,
  reviewer_guidance TEXT,
  created_at TIMESTAMP
)

-- Reviewer actions
reviewer_actions (
  id UUID PRIMARY KEY,
  candidate_id UUID REFERENCES candidates(id),
  reviewer_id VARCHAR,
  action_type VARCHAR,  -- override/comment/shortlist_add/shortlist_remove
  previous_status VARCHAR,
  new_status VARCHAR,
  comment TEXT,
  created_at TIMESTAMP
)

-- Audit log
audit_log (
  id UUID PRIMARY KEY,
  entity_type VARCHAR,
  entity_id UUID,
  action VARCHAR,
  actor VARCHAR,
  details JSONB,
  created_at TIMESTAMP
)

-- Programs catalog
programs (
  id UUID PRIMARY KEY,
  name VARCHAR,
  description TEXT,
  key_competencies JSONB,
  created_at TIMESTAMP
)
```

---

### M10. Audit & Governance Service
**Owner: Backend Engineer (API) + Frontend Engineer (UI)**

Responsibilities:
- Log all actions: pipeline runs, scoring events, reviewer overrides
- Provide audit trail endpoint
- Track model version for reproducibility
- Generate transparency report

---

### M11. Batch Worker Service
**Owner: Backend Engineer (Phase 3)**

For MVP: FastAPI BackgroundTasks handles async processing.
Phase 3: Celery + Redis if needed for heavy batch processing.

---

### M12. Telegram Bot Service *(Phase 4 — post-MVP)*
**Owner: Backend Engineer**
- python-telegram-bot or aiogram
- Candidate self-submission flow
- Status check for reviewers

---

### M13. ASR / Transcription Service
**Owner: NLP Engineer**

Pipeline:
```
video_url input
    ↓
Download audio (yt-dlp or requests)
    ↓
Extract audio track (ffmpeg)
    ↓
faster-whisper large-v3 (GPU)
    ↓
Confidence scoring per segment
    ↓
Language detection + tagging
    ↓
[unclear] flagging for low-confidence segments
    ↓
Auto-redaction pass (names, IIN, phones)
    ↓
Return: transcript, timestamps, confidence, flags
```

Quality flags:
- `low_audio_quality`: SNR below threshold
- `short_duration`: < 60 seconds
- `low_asr_confidence`: mean confidence < 0.75
- `unclear_segments_high`: > 20% segments flagged
- `no_speech_detected`: no voice found
- `requires_human_review`: any critical flag triggered

---

## 5. Directory Structure

```
invisionu/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, router registration
│   │   ├── core/
│   │   │   ├── config.py              # Settings (env vars, model configs)
│   │   │   ├── database.py            # SQLAlchemy async engine + session
│   │   │   ├── dependencies.py        # FastAPI DI (db session, auth)
│   │   │   └── security.py            # PII encryption/decryption utils
│   │   ├── modules/
│   │   │   ├── m1_gateway/
│   │   │   │   ├── router.py          # Main orchestration endpoints
│   │   │   │   └── orchestrator.py    # Pipeline coordination logic
│   │   │   ├── m2_intake/
│   │   │   │   ├── router.py
│   │   │   │   ├── schemas.py         # Pydantic intake schema
│   │   │   │   └── service.py
│   │   │   ├── m3_privacy/
│   │   │   │   ├── redactor.py        # Auto-redaction logic
│   │   │   │   ├── separator.py       # Layer 1/2/3 separation
│   │   │   │   └── service.py
│   │   │   ├── m4_profile/
│   │   │   │   ├── assembler.py       # CandidateProfile builder
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   ├── m5_nlp/
│   │   │   │   ├── client.py          # OpenRouter API client
│   │   │   │   ├── prompts/
│   │   │   │   │   ├── leadership.py
│   │   │   │   │   ├── growth.py
│   │   │   │   │   ├── motivation.py
│   │   │   │   │   ├── initiative.py
│   │   │   │   │   ├── consistency.py
│   │   │   │   │   └── authenticity.py
│   │   │   │   ├── extractor.py       # Main signal extraction orchestrator
│   │   │   │   ├── ai_detector.py     # AI writing detection
│   │   │   │   ├── embeddings.py      # BAAI/bge-m3 local embeddings
│   │   │   │   └── service.py
│   │   │   ├── m6_scoring/
│   │   │   │   ├── rules.py           # Rule-based scoring engine
│   │   │   │   ├── ml_model.py        # sklearn GBR model
│   │   │   │   ├── synthetic_data.py  # Synthetic training data generator
│   │   │   │   ├── confidence.py      # Uncertainty quantification
│   │   │   │   ├── ranker.py          # Ranking + shortlist logic
│   │   │   │   └── service.py
│   │   │   ├── m7_explainability/
│   │   │   │   ├── evidence.py        # Evidence extraction
│   │   │   │   ├── factors.py         # Positive/caution factor generator
│   │   │   │   └── service.py
│   │   │   ├── m8_dashboard/
│   │   │   │   ├── router.py          # Dashboard API endpoints
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   ├── m9_storage/
│   │   │   │   ├── models.py          # SQLAlchemy ORM models (all tables)
│   │   │   │   └── repository.py      # DB operations per entity
│   │   │   ├── m10_audit/
│   │   │   │   ├── router.py
│   │   │   │   ├── logger.py          # Audit trail writer
│   │   │   │   └── service.py
│   │   │   └── m13_asr/
│   │   │       ├── transcriber.py     # faster-whisper integration
│   │   │       ├── downloader.py      # Video/audio download
│   │   │       ├── quality_checker.py # ASR quality flags
│   │   │       └── service.py
│   │   └── schemas/
│   │       └── common.py             # Shared response envelopes
│   ├── alembic/                      # DB migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Redirect to /dashboard
│   │   │   ├── upload/
│   │   │   │   └── page.tsx          # Candidate upload/intake form
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx          # Main ranking table
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx      # Candidate detail + explanation
│   │   │   ├── shortlist/
│   │   │   │   └── page.tsx          # Shortlist view + export
│   │   │   └── audit/
│   │   │       └── page.tsx          # Audit log / transparency
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui primitives
│   │   │   ├── candidate/
│   │   │   │   ├── CandidateCard.tsx
│   │   │   │   ├── ScoreRadar.tsx    # Recharts radar chart for sub-scores
│   │   │   │   ├── ExplanationBlock.tsx
│   │   │   │   ├── EvidenceList.tsx
│   │   │   │   └── OverridePanel.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── RankingTable.tsx
│   │   │   │   ├── StatusBadge.tsx
│   │   │   │   └── FilterPanel.tsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       └── Header.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                # Typed API client
│   │   │   └── utils.ts
│   │   └── types/
│   │       └── index.ts              # Shared TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── docs/
    ├── ARCHITECTURE.md               # This file
    └── plans/
        └── SPRINT_29MARCH.md         # Sprint plan Day 1-3
```

---

## 6. Team Distribution & Ownership

| Module | Owner | Phase |
|--------|-------|-------|
| M1. API Gateway & Orchestration | Backend Engineer | 1 |
| M2. Candidate Intake Service | Backend Engineer | 1 |
| M3. Privacy & Normalization | Backend Engineer | 2 |
| M4. Candidate Profile Service | Backend Engineer | 2 |
| M5. NLP Signal Extraction | NLP Engineer | 3 |
| M6. Scoring & Ranking Engine | ML Engineer | 4 |
| M7. Explainability Service | NLP (evidence) + ML (aggregation) | 5 |
| M8. Reviewer Dashboard | Backend (API) + Frontend (UI) | 1+5+6 |
| M9. Storage Layer | Backend Engineer | 1 |
| M10. Audit & Governance | Backend (API) + Frontend (UI) | 5 |
| M11. Batch Worker | Backend Engineer | 7 |
| M12. Telegram Bot | Backend Engineer | 8 |
| M13. ASR / Transcription | NLP Engineer | 3 |

---

## 7. API Response Envelope

All API responses follow this format:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-03-27T15:00:00Z",
    "version": "1.0.0"
  }
}
```

Error response:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Video transcript is required",
    "details": { ... }
  }
}
```

---

## 8. Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/invisionu

# LLM API
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_PRIMARY_MODEL=qwen/qwen-3.5-72b-instruct
LLM_FAST_MODEL=qwen/qwen-3.5-7b-instruct
LLM_FALLBACK_MODEL=meta-llama/llama-3.3-70b-instruct

# Groq (ASR + LLM fallback)
GROQ_API_KEY=gsk_...

# Security
PII_ENCRYPTION_KEY=...  # 32-byte key for AES-256
API_SECRET_KEY=...       # For API auth

# Model settings
ASR_MODEL=large-v3
ASR_DEVICE=cuda          # or cpu
EMBEDDING_MODEL=BAAI/bge-m3

# App settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## 9. Docker Compose

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: invisionu
      POSTGRES_PASSWORD: password
      POSTGRES_DB: invisionu
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://invisionu:password@postgres:5432/invisionu
    env_file:
      - .env
    depends_on:
      - postgres
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 10. Implementation Phases Summary

| Phase | Days | Modules | Output |
|-------|------|---------|--------|
| 1. Core scaffold | Day 1-2 | M1, M2, M9 + Frontend skeleton | Working API + DB + pages |
| 2. Normalization | Day 2-3 | M3, M4 | CandidateProfile with 3-layer data |
| 3. NLP + ASR | Day 3-4 | M5, M13 | Signal JSON from real text |
| 4. Scoring | Day 3-4 | M6 | Scores + ranking |
| 5. Explainability | Day 4-5 | M7 + M8 override + M10 | Full explanation block |
| 6. Full UI polish | Day 5-6 | M8 complete | Demo-ready dashboard |
| 7. Batch processing | Day 7 | M11 | Batch upload support |
| 8. Extensions | Day 8-9 | M12, M14 | Telegram bot, engagement |

---

## 11. Scoring Criteria → Architecture Mapping

| Judging Criterion | Points | Covered By |
|-------------------|--------|-----------|
| Problem & Value | 10 | Documentation, presentation |
| Data & Candidate Representation | 15 | M3, M4, M5 — 3-layer model, signal extraction |
| Baseline & Improvements | 10 | M6 — rule-based baseline + ML improvement |
| Model & Validation | 20 | M6 — synthetic data, evaluation metrics |
| Fairness & Explainability | 15 | M3 (PII isolation), M7 (explanation), M8 (HITL override) |
| Demo & UX | 10 | M8 frontend — dashboard, ranking, detail |
| Reliability & Privacy | 10 | M3 (3-layer), M9 (encryption), M10 (audit) |
| Documentation | 10 | README, this architecture doc |
| **Total** | **100** | |
