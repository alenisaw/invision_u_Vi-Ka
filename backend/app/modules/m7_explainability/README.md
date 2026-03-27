# M7 Explainability Module

## Current status

`M7` is not implemented yet.
The integration contract is prepared in advance so this module can be built without changing `M6`.

## What M7 will receive

Input from `M6`:
- final score
- sub-scores
- confidence
- uncertainty flag
- positive score contributors
- caution flags
- signal context with evidence and reasoning

See:
- `docs/contracts/M6_M7_EXPLAINABILITY_HANDOFF.md`
- `docs/contracts/m6_m7_explainability_input_v1.example.json`
- `backend/app/modules/m7_explainability/schemas.py`

## What M7 should do

1. Build a short summary for the candidate.
2. Turn `positive_factors` into reviewer-facing explanation blocks.
3. Turn `caution_flags` into caution blocks with severity and suggested action.
4. Reuse `signal_context.evidence` for evidence snippets.
5. Generate a short `reviewer_guidance` string.

## What M7 should not do

- do not recompute or override `M6` scores
- do not invent evidence
- do not use raw PII

## Suggested future files

- `schemas.py`
- `evidence.py`
- `factors.py`
- `service.py`

## NLP adaptation note

NLP should continue emitting `SignalEnvelope v1`.
`M6` will carry signal context into the `M6 -> M7` handoff automatically.
