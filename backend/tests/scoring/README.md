# Scoring Test Bundle

---

## Document Structure

- [Purpose](#purpose)
- [Folder Layout](#folder-layout)
- [Main Commands](#main-commands)
- [Main Outputs](#main-outputs)

---

## Purpose

This folder keeps everything needed to validate the scoring stage in one place:

- unit tests
- integration tests
- synthetic evaluation tests
- exported evaluation artifacts

---

## Folder Layout

- `unit/`: scoring logic tests
- `integration/`: API and handoff tests
- `evaluation/`: evaluation-layer tests
- `results/`: exported CSV and JSON outputs

---

## Main Commands

Run the full scoring test bundle:

```bash
cd backend && python -m pytest tests/scoring -q
```

Run a synthetic evaluation and export artifacts:

```bash
python backend/tests/scoring/run_evaluation.py
```

---

## Main Outputs

Useful outputs to inspect first:

- `results/current/summary.json`
- `results/current/balanced_status_distribution.csv`
- `results/current/stress_status_distribution.csv`
- `results/current/balanced_profile_type_summary.csv`
- `results/current/stress_profile_type_summary.csv`
