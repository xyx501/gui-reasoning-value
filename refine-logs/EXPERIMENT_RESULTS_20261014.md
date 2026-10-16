# Initial Experiment Results

**Date**: 2026-10-14
**Plan**: `refine-logs/EXPERIMENT_PLAN.md`
**Status**: Synthetic sanity and pilot only. These results validate the pipeline, not a real VLM GUI Agent.

## Implementation Summary

Implemented:

- `experiments/gui_value_pilot/run_pilot.py`
  - Generates resettable synthetic GUI CLICK states.
  - Runs `direct`, `observe`, `reason`, and `wait` paths from the same state.
  - Saves `states.csv`, `rollouts.csv`, `summary.json`, and `summary.md`.
- `experiments/gui_value_pilot/train_value_predictor.py`
  - Trains lightweight logistic predictors for positive incremental gain.
  - Predicts whether `observe` or `reason` improves over `direct`.
  - Saves calibration and ranking metrics.

## Environment

- GPU detected: NVIDIA GeForce RTX 5050 Laptop GPU
- VRAM: 8151 MiB
- Current run did not use GPU; it is a pipeline sanity test.

## Results by Milestone

### M0: Sanity — PASSED

Run: `R001`

- States: 10
- Rollouts: 40
- Output: `refine-logs/pilot_runs/r001_sanity_synthetic_click`

Path summary:

| Path | Success | Avg Latency | Avg Cost |
|---|---:|---:|---:|
| direct | 0.300 | 1.019 | 1.000 |
| observe | 0.500 | 1.676 | 1.650 |
| reason | 0.600 | 2.239 | 2.200 |
| wait | 0.100 | 2.088 | 2.150 |

Interpretation: The four-path pipeline runs end to end and produces parseable metrics.

### M1 and M2: Synthetic CLICK Pilot and Fixed Baselines — PASSED

Run: `R002`

- States: 50
- Repeats: 3
- Rollouts: 600
- Output: `refine-logs/pilot_runs/r002_synthetic_click_50x3`

Path summary:

| Path | Success | Avg Latency | Avg Cost | Model Calls |
|---|---:|---:|---:|---:|
| direct | 0.193 | 1.005 | 1.000 | 1.00 |
| observe | 0.580 | 1.648 | 1.650 | 2.00 |
| reason | 0.347 | 2.190 | 2.200 | 2.00 |
| wait | 0.347 | 2.130 | 2.150 | 1.00 |

Delta vs direct:

| Path | Mean Delta | Positive Rate | Negative Rate |
|---|---:|---:|---:|
| observe | 0.387 | 0.407 | 0.020 |
| reason | 0.153 | 0.193 | 0.040 |
| wait | 0.153 | 0.173 | 0.020 |

Interpretation:

- In the synthetic pilot, `observe` yields the strongest average gain.
- `reason` and `wait` have similar mean delta, showing why wait-control is necessary.
- This is only a synthetic sanity signal; a real GUI/VLM actor is needed before making research claims.

### M3: Lightweight Value Prediction — PASSED ON SYNTHETIC DATA

Run: `R007` and `R008`

Output: `refine-logs/pilot_runs/r007_r008_value_predictor`

Observe gain prediction:

| Split | AUROC | Brier | ECE | F1@0.5 | Positive Rate |
|---|---:|---:|---:|---:|---:|
| train | 0.824 | 0.151 | 0.037 | 0.833 | 0.686 |
| val | 0.750 | 0.186 | 0.173 | 0.750 | 0.571 |
| test | 1.000 | 0.080 | 0.218 | 0.909 | 0.750 |

Reason gain prediction:

| Split | AUROC | Brier | ECE | F1@0.5 | Positive Rate |
|---|---:|---:|---:|---:|---:|
| train | 0.788 | 0.175 | 0.046 | 0.500 | 0.429 |
| val | 0.542 | 0.260 | 0.214 | 0.000 | 0.429 |
| test | 0.969 | 0.093 | 0.073 | 0.857 | 0.500 |

Interpretation:

- The lightweight predictor can recover the synthetic rules used by the simulated actor.
- Validation variance is high because the dataset is small.
- The result is useful as a pipeline check, not as evidence that the real research claim holds.

## Summary

- Must-run sanity/pilot completed: R001-R008.
- Main result status: **pipeline positive, scientific result not yet established**.
- Ready for next step: connect a real GUI dataset and a real actor, then repeat R001-R008.

## Next Step

Recommended next run:

1. Replace `SyntheticActor` with a real local VLM or API actor.
2. Use 20 real GUI screenshots for a mini pilot.
3. Keep the exact same output schema so the predictor and analysis scripts remain reusable.
