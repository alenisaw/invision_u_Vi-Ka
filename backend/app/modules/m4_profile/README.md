# M4 Profile Module

---

## Document Structure

- [Purpose](#purpose)
- [Responsibilities](#responsibilities)
- [File Responsibilities](#file-responsibilities)

---

## Purpose

`M4` assembles the unified `CandidateProfile` consumed by downstream pipeline stages. It combines safe model input and operational metadata into one normalized profile object.

---

## Responsibilities

- load sanitized candidate layers
- build a unified candidate profile
- propagate profile completeness and data flags
- expose model-facing fields to NLP and scoring

---

## File Responsibilities

| File | Responsibility |
|---|---|
| `schemas.py` | profile models |
| `assembler.py` | profile assembly logic |
| `service.py` | build flow and storage integration |

---

Projet Documentation
