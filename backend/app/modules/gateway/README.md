# Gateway Stage

---

## Purpose

The `Gateway` stage is the public backend entrypoint for synchronous pipeline execution, batch submission, and related committee-facing APIs.

## Responsibilities

- expose public pipeline routes
- orchestrate the runtime stage order
- normalize API success and error envelopes
- coordinate direct calls into downstream analytical stages where needed

## File Responsibilities

| File | Responsibility |
|---|---|
| `router.py` | public HTTP routes |
| `orchestrator.py` | synchronous pipeline orchestration |

## Public Stage Mapping

Internal package: `gateway`  
Public stage name: `Gateway`
