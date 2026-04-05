# Profile Stage

---

## Purpose

The `Profile` stage assembles the unified `CandidateProfile` consumed by downstream analytical stages. It combines safe analytical content and operational metadata into one normalized profile object.

## Responsibilities

- load sanitized candidate layers
- build a unified candidate profile
- propagate completeness and data flags
- expose model-facing fields to extraction and scoring

## File Responsibilities

| File | Responsibility |
|---|---|
| `schemas.py` | profile models |
| `assembler.py` | profile assembly logic |
| `service.py` | build flow and storage integration |

## Public Stage Mapping

Internal package: `profile`  
Public stage name: `Profile`
