# M6 Scoring Module

## Purpose

`M6` converts structured NLP signals into:
- sub-scores
- final review priority index
- recommendation status
- confidence and uncertainty markers
- ranked shortlist eligibility

## Public contract

- Input model: `SignalEnvelope`
- Output model: `CandidateScore`
- Main entry point: `ScoringService`

## Main files

- `schemas.py` input and output contracts
- `rules.py` deterministic baseline scoring
- `confidence.py` confidence and uncertainty logic
- `ml_model.py` `GradientBoostingRegressor` refinement layer
- `synthetic_data.py` fixtures and synthetic labeled samples
- `evaluation.py` reproducible synthetic evaluation helpers
- `ranker.py` batch ranking
- `service.py` main orchestration

## Bundle structure

- module code stays in `backend/app/modules/m6_scoring/`
- test and notebook bundle now lives in `backend/tests/m6_scoring/`
- exported outputs should be inspected under `backend/tests/m6_scoring/results/`

## Integration rule

`M5` must emit `SignalEnvelope v1`.

Share these files with NLP for integration:
- `docs/contracts/M5_M6_SIGNAL_ENVELOPE.md`
- `docs/contracts/M5_M6_SIGNAL_MAPPING.md`
- `docs/contracts/m5_signal_envelope_v1.example.json`

## Local setup

Install the standalone bundle:

```bash
pip install -r backend/app/modules/m6_scoring/requirements-m6.txt
```

Run synthetic evaluation:

```bash
python -m backend.app.modules.m6_scoring.evaluation --train-samples 300 --test-samples 120 --out-dir backend/tests/m6_scoring/results/manual
```

The evaluation bundle now exports:
- `balanced_model_comparison.csv`
- `stress_model_comparison.csv`
- `baseline_predictions.csv`
- `gbr_predictions.csv`
- `fixture_report.csv`
- `summary.json`

Run the local M6 bundle tests:

```bash
python -m unittest discover -s backend/tests/m6_scoring -p "test_*.py"
```

Export the latest tuned results and compare them with the frozen pre-tuning reference:

```bash
python backend/tests/m6_scoring/run_evaluation.py
```

Open the notebook:

```bash
jupyter lab backend/tests/m6_scoring/notebooks
```

## Docker

Build:

```bash
docker build -f backend/app/modules/m6_scoring/Dockerfile.m6 -t invision-m6 .
```

Run evaluation:

```bash
docker run --rm -v ${PWD}:/workspace invision-m6
```

Run with compose:

```bash
docker compose -f docker-compose.m6.yml up m6_eval
docker compose -f docker-compose.m6.yml up m6_notebook
```
