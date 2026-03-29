# M9 Storage Module

---

## Document Structure

- [Purpose](#purpose)
- [Responsibilities](#responsibilities)
- [File Responsibilities](#file-responsibilities)

---

## Purpose

`M9` provides the persistence layer of the backend pipeline. It defines the core database models and the repository methods used by active modules.

---

## Responsibilities

- define persistence models
- expose repository methods for candidate lifecycle operations
- support score, explanation, metadata, and audit persistence

---

## File Responsibilities

| File | Responsibility |
|---|---|
| `models.py` | SQLAlchemy database models |
| `repository.py` | repository methods for CRUD and pipeline persistence |

---

Projet Documentation
