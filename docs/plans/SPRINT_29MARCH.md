# Sprint Plan: Day 1–3 (March 27–29)
## Decentrathon 5.0 — Stage #1 Deliverables

**Deadline: March 29, 23:59**

### What must be submitted by March 29
1. **GitHub repository** with code (public, README included)
2. **Architecture solution** — `docs/ARCHITECTURE.md` (done)
3. **Minimally working element** — at least one of: working Logic / API endpoint / module

---

## Stage #1 Goal (minimum to pass filtering)

> "Отсеивает команды без реального старта"

We need to demonstrate that the project has started and is architecturally sound.
**Minimum viable demo by March 29:**
- Backend is running (FastAPI + PostgreSQL via docker-compose)
- `POST /api/v1/pipeline/submit` accepts a candidate JSON and returns a score
- At least M2 (Intake), M3 (Privacy), M4 (Profile), M5 (NLP — 1 signal group), M6 (basic scoring) working end-to-end
- Frontend scaffold is running with at least the Upload page and a stub Ranking table
- Architecture document committed

---

## Day-by-Day Plan

---

### Day 1 — March 27 (Thursday): Setup + Scaffold

**Goal: Everything runs. No logic yet, but infra is live.**

#### Backend Engineer
| Task | Priority | Est. |
|------|----------|------|
| Init FastAPI project structure (full directory per ARCHITECTURE.md) | MUST | 1h |
| Set up docker-compose (PostgreSQL + backend + frontend) | MUST | 1h |
| Write all SQLAlchemy ORM models (M9 — all tables) | MUST | 2h |
| Set up Alembic + first migration | MUST | 30m |
| Create `.env.example`, config.py, database.py | MUST | 30m |
| Implement M2 Intake router + schema (Pydantic v2) | MUST | 2h |
| Stub endpoints for M1 Gateway (returns mock response) | MUST | 30m |
| Write basic README with setup instructions | MUST | 30m |

**End of Day 1 Backend output:**
- `docker-compose up` starts backend + postgres
- `POST /api/v1/candidates/intake` saves candidate to DB, returns candidate_id
- All tables exist in DB

#### Frontend Engineer
| Task | Priority | Est. |
|------|----------|------|
| Init Next.js 14 project (TypeScript, Tailwind, shadcn/ui) | MUST | 30m |
| Set up project structure per ARCHITECTURE.md | MUST | 30m |
| Create layout: Sidebar + Header with navigation | MUST | 1h |
| Create Upload page — form with all fields (using mock submit) | MUST | 2h |
| Create Dashboard page skeleton — table with mock data | MUST | 1h |
| Create Candidate Detail page skeleton — score cards | MUST | 1h |
| Set up typed API client (`lib/api.ts`) with backend base URL | MUST | 30m |
| Add Dockerfile for frontend | MUST | 30m |

**End of Day 1 Frontend output:**
- `localhost:3000` opens, navigation works
- Upload form renders with all fields
- Dashboard shows mock ranked table
- Detail page shows mock score cards

#### NLP Engineer
| Task | Priority | Est. |
|------|----------|------|
| Define signal extraction schema (all signal types as Pydantic models) | MUST | 1.5h |
| Write `m5_nlp/client.py` — OpenRouter async HTTP client | MUST | 1.5h |
| Write system prompt + user prompt for Leadership signal group | MUST | 2h |
| Test leadership prompt against 2-3 mock transcripts manually | MUST | 1h |
| Write `m13_asr/transcriber.py` — faster-whisper integration stub | SHOULD | 1h |
| Define output JSON format (matches M6 input schema) | MUST | 30m |

**End of Day 1 NLP output:**
- OpenRouter client works, can call Qwen2.5-72B
- Leadership signals can be extracted from a sample transcript
- Signal output schema agreed and documented

#### ML Engineer
| Task | Priority | Est. |
|------|----------|------|
| Define scoring weights (per ARCHITECTURE.md scoring table) | MUST | 1h |
| Implement rule-based scoring engine (`m6_scoring/rules.py`) | MUST | 2h |
| Define sub-score schema and output format (matches M7 input) | MUST | 1h |
| Write `synthetic_data.py` — generate 50 synthetic candidate profiles | MUST | 2h |
| Implement confidence calculation logic stub | SHOULD | 1h |
| Define `recommendation_status` mapping (thresholds) | MUST | 30m |

**End of Day 1 ML output:**
- Rule-based engine takes M5 signal JSON → produces score JSON
- 50 synthetic profiles generated (used later for ML model training)
- Scoring schema agreed with NLP engineer

---

### Day 2 — March 28 (Friday): Core Modules + Integration

**Goal: Pipeline M2→M3→M4→M5→M6 works end-to-end (even if slow/basic)**

#### Backend Engineer
| Task | Priority | Est. |
|------|----------|------|
| Implement M3 Privacy Service — Layer 1/2/3 separation logic | MUST | 2.5h |
| Implement auto-redaction (`m3_privacy/redactor.py`) — regex patterns | MUST | 1.5h |
| Implement M4 Profile Assembler — builds CandidateProfile from layers | MUST | 1.5h |
| Wire M1 Orchestrator to call M2→M3→M4→M5→M6 in sequence | MUST | 2h |
| Add async background task for pipeline execution | SHOULD | 1h |
| Write `GET /api/v1/pipeline/status/{job_id}` endpoint | SHOULD | 30m |

**End of Day 2 Backend output:**
- `POST /api/v1/pipeline/submit` → triggers full pipeline
- Candidate goes through intake → privacy separation → profile assembly
- PII stored separately from model input

#### Frontend Engineer
| Task | Priority | Est. |
|------|----------|------|
| Connect Upload form to real backend API | MUST | 1.5h |
| Add loading states and error handling on Upload page | MUST | 1h |
| Implement TanStack Query for Dashboard data fetching | MUST | 1.5h |
| Build RankingTable component with sorting (by RPI score) | MUST | 2h |
| Add StatusBadge component for recommendation statuses | MUST | 1h |
| Build ScoreRadar chart (Recharts radar for sub-scores) | SHOULD | 1.5h |

**End of Day 2 Frontend output:**
- Upload form submits to backend, shows success/error
- Dashboard fetches real (or mock) candidates from API
- Ranking table sorts by score, shows status badges

#### NLP Engineer
| Task | Priority | Est. |
|------|----------|------|
| Implement all remaining signal group prompts (Growth, Motivation, Initiative) | MUST | 2h |
| Implement Consistency check prompt (essay ↔ transcript) | MUST | 1.5h |
| Implement AI writing detection (`ai_detector.py`) | MUST | 1.5h |
| Implement embeddings client (`embeddings.py`) — BAAI/bge-m3 local | MUST | 1h |
| Write main signal extractor orchestrator (`extractor.py`) | MUST | 1.5h |
| Test full M5 extraction on 3 complete mock candidate profiles | MUST | 1h |

**End of Day 2 NLP output:**
- `extract_signals(model_input) → NLPSignals` works for full profile
- All 8 signal groups extracted
- AI writing detection returns advisory score

#### ML Engineer
| Task | Priority | Est. |
|------|----------|------|
| Generate 200 synthetic labeled profiles (expand from 50) | MUST | 1.5h |
| Train GradientBoostingRegressor on synthetic data | MUST | 1.5h |
| Save model artifact (`scoring_model.pkl`) | MUST | 30m |
| Implement hybrid scoring: rules + ML aggregation | MUST | 2h |
| Implement ranking logic (`ranker.py`) — sort by RPI, generate shortlist | MUST | 1.5h |
| Write M6 service layer — callable from M1 Orchestrator | MUST | 1h |

**End of Day 2 ML output:**
- `score_candidate(signals) → CandidateScore` works
- Ranking works across multiple candidates
- Shortlist generation works

---

### Day 3 — March 29 (Saturday): Integration + GitHub + Architecture Submit

**Goal: End-to-end demo works. Code is on GitHub. Architecture committed.**

#### All Engineers — Morning (9:00–13:00)

**Integration session (everyone together)**:
1. Test full pipeline: submit candidate JSON → get score + explanation
2. Fix integration bugs between M5 output format and M6 input
3. Fix frontend → backend API connection issues
4. Verify docker-compose brings everything up cleanly

#### Backend Engineer — Afternoon
| Task | Priority | Est. |
|------|----------|------|
| Implement M7 Explainability Service (basic version) | MUST | 2h |
| Wire M7 into pipeline after M6 | MUST | 30m |
| Implement `GET /api/v1/dashboard/ranking` — returns scored + ranked list | MUST | 1h |
| Implement `GET /api/v1/dashboard/candidates/{id}` — full detail | MUST | 1h |
| Write comprehensive README (setup, API, examples) | MUST | 1h |

#### Frontend Engineer — Afternoon
| Task | Priority | Est. |
|------|----------|------|
| Connect Candidate Detail page to real API | MUST | 1.5h |
| Build ExplanationBlock component (positive factors + caution flags) | MUST | 1.5h |
| Add EvidenceList — quotes from transcript/essay | SHOULD | 1h |
| Polish overall UI — consistent spacing, colors, typography | SHOULD | 1h |

#### NLP Engineer — Afternoon
| Task | Priority | Est. |
|------|----------|------|
| Implement Evidence extraction for M7 (top 3 evidence quotes per signal) | MUST | 1.5h |
| Complete ASR transcriber with quality flags | SHOULD | 1.5h |
| Create 5 realistic mock candidate profiles (used in demo) | MUST | 1h |

#### ML Engineer — Afternoon
| Task | Priority | Est. |
|------|----------|------|
| Implement uncertainty flags (confidence < threshold → MANUAL_REVIEW) | MUST | 1h |
| Implement missing data penalty logic | MUST | 1h |
| Write basic evaluation: precision/recall on synthetic test set | SHOULD | 1.5h |
| Document scoring logic in `docs/SCORING.md` | SHOULD | 1h |

#### All Engineers — Evening (18:00–20:00): Final Submission
1. All code committed and pushed to GitHub
2. `README.md` complete with: project description, setup instructions, API examples
3. `docs/ARCHITECTURE.md` committed
4. docker-compose tested from clean state
5. At least one working demo flow recorded or documented
6. Repository link ready for submission

---

## Deliverables Checklist for March 29

### Must Have (Stage #1 pass)
- [ ] GitHub repository is public with all code
- [ ] `README.md` has setup instructions + what the project does
- [ ] `docs/ARCHITECTURE.md` committed
- [ ] `docker-compose up` starts the full system
- [ ] `POST /api/v1/pipeline/submit` accepts JSON and returns score
- [ ] At least 1 working module demonstrably functional
- [ ] Frontend opens and shows something real

### Should Have (stronger impression)
- [ ] Full M2→M3→M4→M5→M6→M7 pipeline working end-to-end
- [ ] Dashboard shows ranked list of demo candidates
- [ ] Candidate detail shows sub-scores + explanation
- [ ] 3-layer privacy separation implemented and documented
- [ ] 5 mock candidate profiles for demo

### Nice to Have (bonus)
- [ ] ASR transcription working
- [ ] AI writing detection advisory signal
- [ ] Reviewer override flow
- [ ] Audit log endpoint
- [ ] Export shortlist to CSV

---

## Demo Scenario for March 29

1. Open `localhost:3000`
2. Navigate to **Upload** page
3. Paste JSON for demo candidate #1 (motivated student with clear leadership story)
4. Submit — pipeline runs (~10-15 seconds)
5. Navigate to **Dashboard** — see candidate ranked
6. Click candidate — see:
   - Radar chart with 8 sub-scores
   - `STRONG_RECOMMEND` status badge
   - Explanation: "Strong leadership indicators, clear growth trajectory..."
   - Evidence: quote from their video transcript
   - Caution flag: "Essay-transcript voice consistency requires review" (advisory)
7. Add to **Shortlist**
8. Navigate to **Shortlist** page — see export button

This demonstrates: data intake → privacy handling → NLP analysis → scoring → explainable output → human dashboard.

---

## Risk Register

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| OpenRouter API latency / errors | Medium | Pre-cache results for demo candidates; use Groq fallback |
| BAAI/bge-m3 GPU memory issues | Low | Fall back to `paraphrase-multilingual-mpnet-base-v2` (smaller) |
| M5→M6 JSON format mismatch | High | NLP + ML engineers agree schema on Day 1 EOD |
| Docker networking issues | Medium | Test docker-compose Day 1, fix before Day 2 |
| Frontend-backend CORS | Low | Set CORS in FastAPI from Day 1 |
| Pipeline too slow for demo | Medium | Pre-run pipeline for demo candidates, cache results |

---

## Communication Protocol for Team

- **Schema changes**: any changes to signal JSON or score JSON must be communicated immediately (affects 3 people)
- **Blocked?**: post in team chat within 15 min of being blocked — don't waste hours solo
- **Day 2 EOD sync**: 30-min call — confirm integration works, adjust Day 3 priorities
- **Day 3 12:00 freeze**: no new features after noon on Day 3 — only fixes and polish
