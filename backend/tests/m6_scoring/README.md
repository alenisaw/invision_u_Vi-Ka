# M6 Test Bundle

---

## Document Structure

- [Purpose](#purpose)
- [Folder Layout](#folder-layout)
- [Main Commands](#main-commands)
- [Main Outputs](#main-outputs)

---

## Purpose

This folder keeps everything needed to validate the `M6` module in one place:

- unit tests
- integration tests
- synthetic evaluation tests
- notebook review
- exported run artifacts
- pre-tuning reference outputs for comparison

---

## Folder Layout

- `unit/`: scoring logic tests
- `integration/`: API and handoff tests
- `evaluation/`: evaluation-layer tests
- `notebooks/`: notebook for result inspection
- `results/`: exported CSV and JSON outputs

---

## Main Commands

Run the full M6 test bundle:

```bash
python -m unittest discover -s backend/tests/m6_scoring -p "test_*.py"
```

Run a synthetic evaluation and export artifacts:

```bash
python backend/tests/m6_scoring/run_evaluation.py
```

Open the notebook:

```bash
jupyter lab backend/tests/m6_scoring/notebooks
```

---

## Main Outputs

Useful outputs to inspect first:

- `results/latest/summary.json`
- `results/latest/balanced_status_distribution.csv`
- `results/latest/stress_status_distribution.csv`
- `results/latest/balanced_profile_type_summary.csv`
- `results/latest/stress_profile_type_summary.csv`

---

Projet Documentation
