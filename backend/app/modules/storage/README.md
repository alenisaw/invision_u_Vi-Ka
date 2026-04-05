# Storage Stage

---

## Purpose

The `Storage` stage provides the persistence layer for the admissions runtime. It defines the database models and the repository methods used by active stages.

## Responsibilities

- define persistence models
- expose repository methods for candidate lifecycle operations
- support candidate, score, explanation, and committee-event persistence

## File Responsibilities

| File | Responsibility |
|---|---|
| `models.py` | SQLAlchemy database models |
| `repository.py` | repository methods for CRUD and runtime persistence |

## Public Stage Mapping

Internal package: `storage`  
Public stage name: `Storage`
