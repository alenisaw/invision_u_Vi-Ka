# M6 Test Bundle

## Purpose

This folder keeps everything needed to check the `M6` module in one place:
- unit tests
- integration tests
- synthetic evaluation tests
- notebook
- exported run artifacts
- frozen pre-tuning reference for before/after comparison

## Layout

- `unit/` unit tests for scoring logic
- `integration/` API and handoff tests
- `evaluation/` synthetic evaluation tests
- `notebooks/` notebook for result inspection
- `results/` exported csv/json outputs from evaluation runs
  - `results/latest/` fresh tuned run
  - `results/pre_tuning_reference/` frozen baseline for comparison

## Main commands

Run the full M6 test bundle:

```bash
python -m unittest discover -s backend/tests/m6_scoring -p "test_*.py"
```

Run a synthetic evaluation and export the artifacts:

```bash
python backend/tests/m6_scoring/run_evaluation.py
```

The exported bundle includes balanced and stress comparisons for:
- `baseline_only`
- `gbr`

It also writes a `vs_pre_tuning.csv` delta file under `results/latest/`.

Open the notebook:

```bash
jupyter lab backend/tests/m6_scoring/notebooks
```
