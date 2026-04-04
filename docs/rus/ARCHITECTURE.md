# Архитектура системы

---

## Структура документа

- [Обзор системы](#обзор-системы)
- [Диаграмма 1. Общая схема](#диаграмма-1-общая-схема)
- [Архитектурные принципы](#архитектурные-принципы)
- [Реализованный backend flow](#реализованный-backend-flow)
- [Ответственность модулей](#ответственность-модулей)
- [Подробный каталог модулей](#подробный-каталог-модулей)
- [Стек моделей](#стек-моделей)
- [Модель управления данными](#модель-управления-данными)
- [Диаграмма 2. Privacy-by-Design](#диаграмма-2-privacy-by-design)
- [Диаграмма 3. Базовая модель данных](#диаграмма-3-базовая-модель-данных)
- [Структура репозитория](#структура-репозитория)

---

## Обзор системы

Система отбора кандидатов inVision U — это модульный монолит для admissions decision support. В текущем репозитории лежат и FastAPI backend, и Next.js reviewer frontend.

Живая ветка сейчас работает как синхронный request-response pipeline:

- анкета кандидата попадает в `M2` или в полный pipeline через `M1`
- при наличии `video_url` вызывается `M13` для транскрибации интервью
- до model-facing обработки данные проходят privacy-разделение в `M3`
- `M4`, `M5`, `M6` и `M7` собирают профиль, сигналы, score и explainability
- reviewer-чтение и reviewer-действия идут через `M8` и `M10`
- все состояния сохраняются в PostgreSQL

Платформа остается human-in-the-loop:

- не принимает финальное автономное решение о зачислении
- явно показывает confidence, uncertainty и review-routing поля
- изолирует чувствительные данные до model-facing обработки
- логирует overrides и reviewer actions

---

## Диаграмма 1. Общая схема

```mermaid
flowchart LR
    Candidate["Подача кандидата"]
    Demo["M0 Demo Fixtures"]
    Frontend["Next.js Frontend"]
    Proxy["Next.js Proxy /api/backend/*"]
    Gateway["M1 Gateway"]
    Intake["M2 Intake"]
    Privacy["M3 Privacy"]
    L1["Layer 1: PII Vault"]
    L2["Layer 2: Operational Metadata"]
    L3["Layer 3: Model Input"]
    Profile["M4 Profile"]
    NLP["M5 NLP"]
    ASR["M13 ASR"]
    Score["M6 Scoring"]
    Explain["M7 Explainability"]
    Dashboard["M8 Dashboard"]
    Audit["M10 Audit"]
    DB["PostgreSQL"]
    Reviewer["Reviewer"]

    Candidate --> Frontend
    Demo --> Gateway
    Frontend --> Proxy
    Proxy --> Gateway
    Gateway --> Intake
    Intake --> Privacy
    Privacy --> L1
    Privacy --> L2
    Privacy --> L3
    L3 --> Profile
    Gateway --> ASR
    ASR --> Privacy
    Profile --> NLP
    NLP --> Score
    Score --> Explain
    Dashboard --> Frontend
    Reviewer --> Frontend
    Gateway --> DB
    Privacy --> DB
    Profile --> DB
    NLP --> DB
    Score --> DB
    Explain --> DB
    Dashboard --> DB
    Audit --> DB
```

---

## Архитектурные принципы

### Privacy by Design

PII изолируется до любой model-facing обработки. AI/ML-модули работают только с безопасным Layer 3.

### Explainability First

Score должен оставаться разбираемым. Для reviewer выводятся evidence, positive factors, caution blocks и routing logic.

### Human in the Loop

Recommendation categories носят advisory-характер. Поля `manual_review_required`, `human_in_loop_required` и `review_recommendation` сохраняют контроль за reviewer.

### Синхронная оркестрация

Текущая ветка исполняет основной pipeline синхронно внутри API-процесса. В основном compose-стеке нет Redis-очереди и отдельного worker-слоя.

### Reviewer-safe доступ

Защищенные маршруты используют session auth с HTTP-only cookie. Доступ ограничивается через backend RBAC для ролей `admin`, `chair` и `reviewer`, поэтому общий reviewer key больше не нужен.

---

## Реализованный backend flow

Реализованный backend flow в текущей ветке:

0. `M0 Demo` дает готовые demo fixtures.
1. `M2 Intake` валидирует payload и создает базовую запись кандидата.
2. `M13 ASR` опционально транскрибирует интервью, если указан `video_url`.
3. `M3 Privacy` разделяет входные данные на PII, operational metadata и safe model input.
4. `M4 Profile` собирает единый `CandidateProfile`.
5. `M5 NLP` извлекает канонический `SignalEnvelope`.
6. `M6 Scoring` считает program-aware score, ranking fields и reviewer-routing output.
7. `M7 Explainability` формирует summary, positive factors, caution blocks и reviewer guidance.
8. `M8 Dashboard` отдает reviewer-facing read API поверх сохраненных score/explanation/raw content.
9. `M10 Audit` хранит overrides, reviewer actions и audit feed.

---

## Ответственность модулей

Подробная документация по каждому модулю вынесена в:

- [`docs/rus/MODULES.md`](MODULES.md)

---

## Подробный каталог модулей

Для полного описания модулей, их входов, выходов и файлов смотри:

- [`docs/rus/MODULES.md`](MODULES.md)

---

## Стек моделей

### NLP

| Модуль | Модель | Роль |
|---|---|---|
| `M5` | `meta-llama/llama-4-scout-17b-16e-instruct` | основной grouped structured signal extraction через Groq |
| `M5` | heuristic extractor | детерминированный fallback |
| `M7` | deterministic formatter | сборка explainability-report из сохраненного M6 output |

### ASR

| Модуль | Модель | Роль |
|---|---|---|
| `M13` | env-выбранная Groq Whisper model (`whisper-large-v3-turbo` по умолчанию) | транскрибация интервью и анализ сегментов |

### Embeddings

| Runtime | Модель | Роль |
|---|---|---|
| Primary | `jinaai/jina-embeddings-v5-text-nano` | локальные similarity и consistency checks внутри backend-процесса |
| Fallback | lexical cosine similarity | детерминированный запасной path при недоступности локального embedding backend |

### Scoring

| Слой | Модель / метод | Роль |
|---|---|---|
| Baseline | rule-based scoring | прозрачный базовый score |
| Refinement | `GradientBoostingRegressor` | ML-уточнение score |
| Calibration | `ScoreCalibrator` | опциональный post-processing score |

---

## Модель управления данными

### Layer 1: Secure PII Vault

Хранит зашифрованные PII и административно-чувствительные данные: имена, адреса, контакты, guardians, IDs и supporting documents.

### Layer 2: Operational Metadata

Хранит workflow-метаданные: age eligibility, language-threshold status, selected program, language exam type, completeness, data flags и наличие видео.

### Layer 3: Safe Model Input

Хранит model-facing контент: redacted transcript, essay text, internal test answers, ASR confidence и ASR quality flags.

---

## Диаграмма 2. Privacy-by-Design

```mermaid
flowchart TD
    Raw["Raw Candidate Payload"]
    Privacy["M3 Privacy"]

    subgraph Layer1["Layer 1: Secure PII Vault"]
        PII1["Полное имя"]
        PII2["IIN и данные документа"]
        PII3["Адрес и контакты"]
        PII4["Данные родителей или guardian"]
    end

    subgraph Layer2["Layer 2: Operational Metadata"]
        META1["Age eligibility"]
        META2["Language threshold flag"]
        META3["Selected program и language exam"]
        META4["Completeness и data flags"]
    end

    subgraph Layer3["Layer 3: Safe Model Input"]
        SAFE1["Redacted transcript"]
        SAFE2["Essay text"]
        SAFE3["Internal test answers"]
        SAFE4["ASR confidence"]
        SAFE5["ASR quality flags"]
    end

    AI["AI и ML-модули"]

    Raw --> Privacy
    Privacy --> Layer1
    Privacy --> Layer2
    Privacy --> Layer3
    Layer3 --> AI

    Layer1 -. never sent .-> AI
    Layer2 -. not used for demographic scoring .-> AI
```

---

## Диаграмма 3. Базовая модель данных

```mermaid
erDiagram
    candidates ||--o| candidate_pii : has
    candidates ||--o| candidate_metadata : has
    candidates ||--o| candidate_model_inputs : has
    candidates ||--o| nlp_signals : has
    candidates ||--o| candidate_scores : has
    candidates ||--o| candidate_explanations : has
    candidates ||--o{ reviewer_actions : has
    audit_log }o--|| candidates : references

    candidates {
        uuid id PK
        uuid intake_id
        string dedupe_key
        string selected_program
        string pipeline_status
        timestamp created_at
        timestamp updated_at
    }

    candidate_pii {
        uuid id PK
        uuid candidate_id FK
        bytes encrypted_data
    }

    candidate_metadata {
        uuid id PK
        uuid candidate_id FK
        boolean age_eligible
        boolean language_threshold_met
        string language_exam_type
        boolean has_video
        float data_completeness
        jsonb data_flags
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
    }

    nlp_signals {
        uuid id PK
        uuid candidate_id FK
        jsonb signals
        string model_used
        int processing_time_ms
    }

    candidate_scores {
        uuid id PK
        uuid candidate_id FK
        jsonb sub_scores
        float review_priority_index
        string recommendation_status
        float confidence
        int ranking_position
        jsonb score_payload
    }

    candidate_explanations {
        uuid id PK
        uuid candidate_id FK
        text summary
        jsonb positive_factors
        jsonb caution_flags
        jsonb data_quality_notes
        text reviewer_guidance
        jsonb report_payload
    }

    reviewer_actions {
        uuid id PK
        uuid candidate_id FK
        uuid reviewer_user_id
        string reviewer_name
        string action_type
        string previous_status
        string new_status
        text comment
    }

    audit_log {
        uuid id PK
        string entity_type
        uuid entity_id
        string action
        string actor
        jsonb details
    }
```

---

## Структура репозитория

```text
.agent/
  memory/
backend/
  app/
    core/
    modules/
    schemas/
  tests/
docs/
  eng/
  rus/
frontend/
  src/
  e2e/
scripts/
```

---

Projet Documentation
