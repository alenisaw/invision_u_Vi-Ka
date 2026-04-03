# M1 Gateway Module

---

## Document Structure

- [Purpose](#purpose)
- [Responsibilities](#responsibilities)
- [File Responsibilities](#file-responsibilities)

---

## Purpose

`M1` is the public backend entry point. It exposes API endpoints and orchestrates the candidate-processing flow across the active modules.

---

## Responsibilities

- expose intake and pipeline endpoints
- orchestrate the implemented module sequence
- expose direct M6 scoring endpoints
- return pipeline and scoring responses in a consistent API envelope

---

## File Responsibilities

| File | Responsibility |
|---|---|
| `router.py` | public HTTP endpoints |
| `orchestrator.py` | module orchestration and pipeline flow |

---

Projet Documentation
