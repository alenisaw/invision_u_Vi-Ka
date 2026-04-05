# Privacy Stage

---

## Purpose

The `Privacy` stage implements the privacy boundary of the system. It separates candidate data into protected identity data, operational metadata, and safe analytical content.

## Responsibilities

- redact sensitive text content
- separate payloads into privacy layers
- persist protected, operational, and safe data
- ensure only safe analytical content is passed downstream

## File Responsibilities

| File | Responsibility |
|---|---|
| `redactor.py` | text-level redaction |
| `separator.py` | layer separation logic |
| `service.py` | persistence of separated layers |

## Public Stage Mapping

Internal package: `privacy`  
Public stage name: `Privacy`
