# GUI Value Pilot

Minimal runnable pilot for the first-stage experiment plan.

This code implements a resettable synthetic GUI environment for `CLICK` tasks and runs four paths:

- `direct`
- `observe`
- `reason`
- `wait`

It is a sanity/pilot implementation, not the final paper environment. Its purpose is to verify the experiment pipeline, logging, metrics, and path definitions before connecting a real GUI environment and a GPU/VLM actor.

## Run

```powershell
$py='C:\Users\13803\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py experiments\gui_value_pilot\run_pilot.py --num-states 50 --repeats 3 --seed 42 --outdir refine-logs\pilot_runs\r002_synthetic_click
```

## Outputs

- `states.csv`: generated task states.
- `rollouts.csv`: per-state, per-path, per-repeat outcomes.
- `summary.json`: aggregate metrics.
- `summary.md`: human-readable summary.
- `screenshots/`: synthetic GUI screenshots.

## Next integration point

Replace `SyntheticActor` with a real VLM actor that consumes screenshots and emits normalized coordinates.
