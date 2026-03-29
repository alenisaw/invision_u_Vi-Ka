# M2 Intake Module

---

## Document Structure

- [Purpose](#purpose)
- [Responsibilities](#responsibilities)
- [File Responsibilities](#file-responsibilities)

---

## Purpose

`M2` validates the incoming candidate submission and creates the initial candidate record. It computes early completeness and eligibility metadata used by downstream modules.

---

## Responsibilities

- validate intake payloads
- create candidate records
- compute completeness
- compute basic eligibility and data flags
- persist initial intake metadata

---

## File Responsibilities

| File | Responsibility |
|---|---|
| `schemas.py` | intake request and response models |
| `service.py` | validation, completeness, eligibility, persistence |
| `router.py` | intake endpoint |

---

Projet Documentation
