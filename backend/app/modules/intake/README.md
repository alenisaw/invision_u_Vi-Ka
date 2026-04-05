# Input Intake Stage

---

## Purpose

The `Input Intake` stage validates incoming candidate payloads and creates the initial candidate record used by the rest of the runtime pipeline.

## Responsibilities

- validate input payloads
- create candidate records
- compute completeness
- compute initial eligibility and data flags
- persist input-stage metadata

## File Responsibilities

| File | Responsibility |
|---|---|
| `schemas.py` | input request and response models |
| `service.py` | validation, completeness, eligibility, persistence |
| `router.py` | input endpoint |

## Public Stage Mapping

Internal package: `intake`  
Public stage name: `Input Intake`
