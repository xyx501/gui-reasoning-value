# GUI Agent Reasoning Value Calibration

This repository contains an early-stage research prototype for estimating the value of additional observation and reasoning in GUI agents.

## Research Question

Given a GUI state and an action proposed by an agent, should the system:

- execute the action directly;
- obtain an additional observation;
- perform additional reasoning; or
- wait for the interface state to change?

The project studies whether runtime evidence can predict the incremental benefit of additional observation or reasoning under a resource budget.

## Current Implementation

The repository currently provides:

- a resettable synthetic GUI click environment;
- `direct`, `observe-more`, `reason-more`, and `wait-control` paths;
- structured rollout logging;
- incremental value prediction;
- calibration and cost measurement.

## Repository Structure

```text
experiments/
  gui_value_pilot/       Pilot experiment implementation

refine-logs/
  EXPERIMENT_PLAN.md     Claim-driven experiment plan
  EXPERIMENT_TRACKER.md  Experiment tracker
  EXPERIMENT_RESULTS.md  Initial synthetic results

outputs/
  gui_agent_action_reliability_outline.docx
```

Generated pilot outputs and temporary research files are intentionally excluded from version control.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the Synthetic Pilot

```powershell
python experiments/gui_value_pilot/run_pilot.py `
  --num-states 50 `
  --repeats 3 `
  --seed 42 `
  --outdir refine-logs/pilot_runs/r002
```

## Train the Lightweight Value Predictor

```powershell
python experiments/gui_value_pilot/train_value_predictor.py `
  --run-dir refine-logs/pilot_runs/r002 `
  --outdir refine-logs/pilot_runs/value_predictor `
  --seed 42
```

## Current Status

The existing results are synthetic pipeline sanity checks. They verify the experiment protocol, logging pipeline, and evaluation code, but should not be interpreted as evidence for real GUI-agent performance.

## Next Step

The next stage is to replace the synthetic actor with a real vision-language GUI agent and evaluate it on real GUI screenshots or a resettable GUI environment.

## Security

API credentials must be provided through local environment variables or an ignored `.env` file. Do not commit real credentials, private datasets, or third-party model weights.
