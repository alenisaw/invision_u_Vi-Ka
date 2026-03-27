# API Reference — inVision U Candidate Selection System

**Base URL:** `http://localhost:8000`
**Auth:** `X-API-Key: <key>` (в dev режиме не требуется)
**Content-Type:** `application/json`

---

## Response Envelope

Все ответы оборачиваются в единый формат:

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

Ошибка:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Video transcript is required",
    "details": {}
  }
}
```

---

## Health

### `GET /health`
Проверка состояния сервера.

**Response:**
```json
{ "status": "ok", "version": "1.0.0" }
```

---

## Pipeline

### `POST /api/v1/pipeline/score-signals`
Score one candidate directly from the canonical `SignalEnvelope v1` contract.

Use this endpoint while `M5` is still under implementation.
It is the stable integration point between NLP output and `M6`.

**Request Body:**
```json
{
  "candidate_id": "8a352307-4af4-4f0a-a8f7-b0dd22cb6fa5",
  "signal_schema_version": "v1",
  "m5_model_version": "mock-v0",
  "completeness": 0.91,
  "data_flags": [],
  "signals": {
    "leadership_indicators": {
      "value": 0.82,
      "confidence": 0.88,
      "source": ["video_transcript", "essay"],
      "evidence": ["candidate led a school team project"],
      "reasoning": "leadership behavior is explicit and concrete"
    },
    "motivation_clarity": {
      "value": 0.76,
      "confidence": 0.83,
      "source": ["essay"],
      "evidence": ["clear motivation statement"],
      "reasoning": "goals are specific and credible"
    }
  }
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "candidate_id": "8a352307-4af4-4f0a-a8f7-b0dd22cb6fa5",
    "sub_scores": {
      "leadership_potential": 0.82,
      "growth_trajectory": 0.0,
      "motivation_clarity": 0.76,
      "initiative_agency": 0.0,
      "learning_agility": 0.0,
      "communication_clarity": 0.0,
      "ethical_reasoning": 0.0,
      "program_fit": 0.0
    },
    "review_priority_index": 0.278,
    "recommendation_status": "LOW_SIGNAL",
    "confidence": 0.62,
    "uncertainty_flag": false,
    "shortlist_eligible": false,
    "ranking_position": null,
    "caution_flags": [],
    "score_breakdown": {
      "baseline_rpi": 0.278,
      "ml_rpi": 0.278,
      "blended_rpi": 0.278,
      "mean_signal_confidence": 0.855,
      "signal_coverage": 0.125,
      "completeness": 0.91,
      "model_disagreement": 0.0
    },
    "scoring_version": "m6-v1"
  }
}
```

---

### `POST /api/v1/pipeline/score-signals/batch`
Score and rank multiple signal envelopes directly.

**Request Body:** array of `SignalEnvelope v1`

---

### `POST /api/v1/pipeline/score-signals/train-synthetic`
Train the optional `M6` refinement model on synthetic development data.

**Query params:**
- `sample_count` default `300`
- `seed` default `42`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "status": "trained",
    "sample_count": 300,
    "seed": 42
  }
}
```

---

### `POST /api/v1/pipeline/score-signals/evaluate-synthetic`
Run a compact synthetic holdout evaluation for the scoring module.

**Query params:**
- `train_sample_count` default `300`
- `test_sample_count` default `120`
- `seed` default `42`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "train_sample_count": 300,
    "test_sample_count": 120,
    "mae": 0.0341,
    "rmse": 0.0438,
    "r2": 0.9142,
    "macro_precision": 0.8125,
    "macro_recall": 0.8012,
    "macro_f1": 0.8059,
    "spearman_rank_correlation": 0.9214,
    "top_k_overlap": 0.8
  }
}
```

---

### `POST /api/v1/pipeline/submit`
Отправить одного кандидата и запустить полный pipeline (sync).

**Request Body:**
```json
{
  "personal": {
    "last_name": "Doe",
    "first_name": "John",
    "patronymic": "Alex",
    "date_of_birth": "2005-04-15",
    "gender": "M",
    "citizenship": "KZ",
    "iin": "050415300123",
    "document_type": "passport",
    "document_no": "N12345678",
    "document_authority": "MIA RK",
    "document_date": "2020-01-10"
  },
  "contacts": {
    "phone": "+77001234567",
    "instagram": "@johndoe",
    "telegram": "@johndoe",
    "whatsapp": "+77001234567"
  },
  "parents": {
    "father": { "last_name": "Doe", "first_name": "Richard", "phone": "+77009876543" },
    "mother": { "last_name": "Doe", "first_name": "Mary", "phone": "+77009876544" }
  },
  "address": {
    "country": "KZ",
    "region": "Almaty",
    "city": "Almaty",
    "street": "Abay Ave",
    "house": "10",
    "apartment": "5"
  },
  "academic": {
    "selected_program": "Innovative IT Product Design and Development",
    "language_exam_type": "IELTS",
    "language_score": 7.0
  },
  "content": {
    "video_url": "https://example.com/video.mp4",
    "essay_text": "I believe I can contribute...",
    "project_descriptions": ["Built a mobile app for...", "Led a team of 5..."],
    "experience_summary": "Volunteered at youth NGO for 2 years..."
  },
  "social_status": {
    "has_social_benefit": false,
    "benefit_type": null
  },
  "internal_test": {
    "answers": [
      { "question_id": "q1", "answer": "A" },
      { "question_id": "q2", "answer": "C" }
    ]
  }
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "candidate_id": "uuid",
    "pipeline_status": "completed",
    "recommendation_status": "STRONG_RECOMMEND",
    "review_priority_index": 0.81,
    "confidence": 0.87,
    "sub_scores": {
      "leadership_potential": 0.82,
      "growth_trajectory": 0.79,
      "motivation_clarity": 0.85,
      "initiative_agency": 0.78,
      "learning_agility": 0.80,
      "communication_clarity": 0.75,
      "ethical_reasoning": 0.70,
      "program_fit": 0.83
    },
    "explanation_summary": "Strong candidate with 5 notable positive indicators."
  }
}
```

---

### `POST /api/v1/pipeline/batch`
Отправить нескольких кандидатов (async, background).

**Request Body:** массив объектов того же формата что и `/submit`
```json
[ { ...candidate1 }, { ...candidate2 } ]
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "status": "queued",
    "total": 2
  }
}
```

---

### `GET /api/v1/pipeline/status/{job_id}`
Статус batch-задачи.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "total": 2,
    "processed": 2
  }
}
```

---

## Candidates

### `POST /api/v1/candidates/intake`
Только создать запись кандидата без запуска pipeline (для отложенной обработки).

**Request Body:** тот же формат что и `/pipeline/submit`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "candidate_id": "uuid",
    "pipeline_status": "pending",
    "message": "Candidate received. Submit to pipeline to start analysis."
  }
}
```

---

## Dashboard

### `GET /api/v1/dashboard/ranking`
Список всех кандидатов, отсортированный по `review_priority_index` DESC.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "candidate_id": "uuid",
      "selected_program": "Innovative IT Product Design and Development",
      "pipeline_status": "completed",
      "recommendation_status": "STRONG_RECOMMEND",
      "review_priority_index": 0.81,
      "confidence": 0.87,
      "shortlist_eligible": true,
      "ranking_position": 1
    }
  ]
}
```

**Статусы `recommendation_status`:**
| Значение | Смысл |
|----------|-------|
| `STRONG_RECOMMEND` | RPI ≥ 0.75 — приоритетный кандидат |
| `RECOMMEND` | 0.60 ≤ RPI < 0.75 — хороший кандидат |
| `REVIEW_NEEDED` | 0.45 ≤ RPI < 0.60 — требует проверки |
| `LOW_SIGNAL` | RPI < 0.45 — мало данных |
| `MANUAL_REVIEW` | флаг неопределённости — ручная проверка |

---

### `GET /api/v1/dashboard/shortlist`
Только кандидаты с `shortlist_eligible: true`.

**Response:** тот же формат что и `/ranking`

---

### `GET /api/v1/dashboard/stats`
Сводная статистика.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "total_candidates": 42,
    "by_status": {
      "STRONG_RECOMMEND": 8,
      "RECOMMEND": 14,
      "REVIEW_NEEDED": 12,
      "LOW_SIGNAL": 5,
      "MANUAL_REVIEW": 3
    },
    "shortlist_count": 15,
    "avg_rpi": 0.63
  }
}
```

---

### `GET /api/v1/dashboard/candidates/{candidate_id}`
Полная карточка кандидата.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "candidate_id": "uuid",
    "selected_program": "Innovative IT Product Design and Development",
    "pipeline_status": "completed",
    "recommendation_status": "STRONG_RECOMMEND",
    "review_priority_index": 0.81,
    "confidence": 0.87,
    "sub_scores": {
      "leadership_potential": 0.82,
      "growth_trajectory": 0.79,
      "motivation_clarity": 0.85,
      "initiative_agency": 0.78,
      "learning_agility": 0.80,
      "communication_clarity": 0.75,
      "ethical_reasoning": 0.70,
      "program_fit": 0.83
    },
    "explanation": { ... },
    "data_flags": ["missing_essay"]
  }
}
```

---

### `GET /api/v1/dashboard/candidates/{candidate_id}/explanation`
Блок объяснения оценки кандидата.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "summary": "Strong candidate with 5 notable positive indicators.",
    "positive_factors": [
      {
        "factor": "Leadership indicators",
        "score": 0.82,
        "score_contribution": "+0.164"
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
    "reviewer_guidance": "Pay attention to: Essay-transcript consistency gap."
  }
}
```

---

### `POST /api/v1/dashboard/candidates/{candidate_id}/override`
Reviewer override — изменить статус кандидата вручную.

**Request Body:**
```json
{
  "reviewer_id": "reviewer_001",
  "new_status": "RECOMMEND",
  "comment": "Personally interviewed — strong candidate despite low essay score"
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "message": "Override applied",
    "new_status": "RECOMMEND"
  }
}
```

---

## Audit

### `GET /api/v1/audit/log`
Полный журнал действий системы.

**Response `200`:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "entity_type": "candidate",
      "entity_id": "uuid",
      "action": "pipeline_completed",
      "actor": "system",
      "details": { "status": "STRONG_RECOMMEND" },
      "created_at": "2026-03-27T15:00:00"
    }
  ]
}
```

---

## Error Codes

| Code | HTTP | Описание |
|------|------|----------|
| `VALIDATION_ERROR` | 422 | Неверный формат запроса |
| `NOT_FOUND` | 404 | Кандидат или ресурс не найден |
| `PIPELINE_ERROR` | 500 | Ошибка в pipeline обработки |
| `UNAUTHORIZED` | 403 | Неверный API ключ |
