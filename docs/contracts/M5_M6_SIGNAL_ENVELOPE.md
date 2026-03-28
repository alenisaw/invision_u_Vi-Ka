# M5 -> M6 SignalEnvelope v1

## Purpose

This document defines the canonical contract between:
- `M5. NLP Signal Extraction`
- `M6. Scoring & Ranking Engine`

`M6` is already implemented against this contract.
`M5` should emit this exact shape.

## Frozen rules

- `M6` consumes only structured signals
- no raw candidate text is required by `M6`
- no PII is allowed in this payload
- all `value` fields must be in `0.0..1.0`
- all `confidence` fields must be in `0.0..1.0`
- missing optional signals must be omitted, not sent as `null`
- `completeness` and `data_flags` are safe metadata and must be provided

## Canonical envelope

```json
{
  "candidate_id": "8a352307-4af4-4f0a-a8f7-b0dd22cb6fa5",
  "signal_schema_version": "v1",
  "m5_model_version": "qwen-promptset-1",
  "selected_program": "Инновационные цифровые продукты и сервисы",
  "program_id": "digital_products_and_services",
  "completeness": 0.91,
  "data_flags": [],
  "signals": {
    "leadership_indicators": {
      "value": 0.82,
      "confidence": 0.88,
      "source": ["video_transcript", "essay"],
      "evidence": ["candidate led a school team project"],
      "reasoning": "leadership behavior is explicit and concrete"
    }
  }
}
```

## Top-level fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `candidate_id` | `uuid string` | yes | stable anonymized candidate id |
| `signal_schema_version` | `string` | yes | currently `v1` |
| `m5_model_version` | `string` | yes | model or prompt bundle version |
| `selected_program` | `string` | yes | raw safe program label |
| `program_id` | `string` | yes | canonical normalized program id for `M6` policy |
| `completeness` | `float` | yes | safe profile completeness score |
| `data_flags` | `string[]` | yes | data quality flags from upstream |
| `signals` | `object` | yes | map of signal name -> signal payload |

## Signal payload

Each signal must follow this structure:

```json
{
  "value": 0.0,
  "confidence": 0.0,
  "source": ["essay"],
  "evidence": ["short quote or factual snippet"],
  "reasoning": "brief explanation"
}
```

## Signal payload fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `value` | `float` | yes | normalized signal value |
| `confidence` | `float` | yes | signal confidence, same `0.0..1.0` range |
| `source` | `string[]` | yes | source modalities used |
| `evidence` | `string[]` | yes | short evidence snippets |
| `reasoning` | `string` | yes | compact factual explanation |

## Data flags recognized by M6

These can push candidates toward manual review:
- `requires_human_review`
- `low_asr_confidence`
- `unclear_segments_high`
- `no_speech_detected`

## NLP-side implementation notes

- if a signal cannot be estimated reliably, omit it
- do not substitute unknown signals with `0.0`
- keep evidence concise
- keep reasoning short and factual
- keep `signal_schema_version` pinned to `v1` until both sides agree on a new version
