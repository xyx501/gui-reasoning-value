# Experiment Code Review

**Date**: 2026-10-14

Review mode: local-only. No secondary Codex reviewer was delegated in this run.

## Scope

Reviewed:

- `experiments/gui_value_pilot/run_pilot.py`
- `experiments/gui_value_pilot/README.md`

Against:

- `refine-logs/EXPERIMENT_PLAN.md`
- `refine-logs/EXPERIMENT_TRACKER.md`

## Findings

### Blocking issues

None for the sanity/pilot purpose.

### Non-blocking issues

1. The actor is synthetic and should not be interpreted as evidence for real VLM behavior.
2. The environment is synthetic and only validates the experiment protocol and logging pipeline.
3. The code currently implements R001/R002-style synthetic CLICK sanity, not the full value predictor training stage.

## Checks

- Hyperparameters exposed via argparse: yes (`num-states`, `repeats`, `seed`, `outdir`).
- Random seed fixed and controllable: yes.
- Results saved to parseable JSON/CSV: yes.
- Evaluation compares predictions against environment ground truth target boxes: yes.
- Sanity-stage experiments run before full deployment: yes.
