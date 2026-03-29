# M3 Privacy Module

---

## Document Structure

- [Purpose](#purpose)
- [Responsibilities](#responsibilities)
- [File Responsibilities](#file-responsibilities)

---

## Purpose

`M3` implements the privacy boundary of the system. It separates candidate data into encrypted PII, operational metadata, and safe model input.

---

## Responsibilities

- redact sensitive text content
- separate payloads into three layers
- persist Layer 1, Layer 2, and Layer 3 data
- ensure only safe model input is passed downstream

---

## File Responsibilities

| File | Responsibility |
|---|---|
| `redactor.py` | text-level PII redaction |
| `separator.py` | three-layer separation logic |
| `service.py` | persistence of separated layers |

---

Projet Documentation
