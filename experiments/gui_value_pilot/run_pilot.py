"""Synthetic GUI value pilot.

This script implements the first sanity-stage experiment from refine-logs/EXPERIMENT_PLAN.md.
It is intentionally small and deterministic:

- Generate resettable synthetic GUI CLICK states.
- Run direct / observe / reason / wait paths from the same initial state.
- Save parseable CSV/JSON results for later review.

The synthetic actor is a placeholder. It simulates common GUI-agent failure modes so the
experiment plumbing can be validated before replacing it with a real VLM actor.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont


CANVAS_W = 960
CANVAS_H = 540


@dataclass
class GUIState:
    state_id: str
    difficulty: str
    task: str
    target_label: str
    target_bbox: Tuple[int, int, int, int]
    distractor_count: int
    target_size: int
    visual_ambiguity: float
    semantic_ambiguity: float
    info_missing: float
    loading_dynamic: float
    screenshot_path: str


@dataclass
class Rollout:
    state_id: str
    repeat: int
    path: str
    x: float
    y: float
    success: int
    latency: float
    model_calls: int
    cost: float
    notes: str


DIFFICULTIES = [
    "easy",
    "small_target",
    "ambiguous_label",
    "cluttered",
    "edge_target",
    "loading_sensitive",
]


LABELS = [
    "Search",
    "Submit",
    "Save",
    "Download",
    "Close",
    "Continue",
    "Settings",
    "Open",
    "Confirm",
    "Cancel",
]


def _font(size: int = 18):
    # Use default font for portability.
    try:
        return ImageFont.truetype("arial.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def bbox_center(b: Tuple[int, int, int, int]) -> Tuple[float, float]:
    x1, y1, x2, y2 = b
    return (x1 + x2) / 2, (y1 + y2) / 2


def point_in_bbox(x: float, y: float, b: Tuple[int, int, int, int]) -> bool:
    x1, y1, x2, y2 = b
    return x1 <= x <= x2 and y1 <= y <= y2


def draw_button(draw: ImageDraw.ImageDraw, bbox: Tuple[int, int, int, int], label: str, target: bool = False, disabled: bool = False):
    x1, y1, x2, y2 = bbox
    fill = (225, 238, 255) if target else (245, 245, 245)
    if disabled:
        fill = (220, 220, 220)
    outline = (50, 95, 180) if target else (160, 160, 160)
    draw.rounded_rectangle(bbox, radius=8, fill=fill, outline=outline, width=2 if target else 1)
    draw.text((x1 + 8, y1 + max(5, (y2 - y1 - 14) // 2)), label, fill=(25, 25, 25), font=_font(15))


def generate_state(i: int, outdir: Path, rng: random.Random) -> GUIState:
    difficulty = DIFFICULTIES[i % len(DIFFICULTIES)]
    target_label = rng.choice(LABELS)
    distractor_count = {"easy": 3, "small_target": 5, "ambiguous_label": 6, "cluttered": 12, "edge_target": 7, "loading_sensitive": 5}[difficulty]
    target_size = {"easy": 120, "small_target": 44, "ambiguous_label": 98, "cluttered": 82, "edge_target": 72, "loading_sensitive": 100}[difficulty]
    visual_ambiguity = {"easy": 0.15, "small_target": 0.65, "ambiguous_label": 0.45, "cluttered": 0.8, "edge_target": 0.55, "loading_sensitive": 0.5}[difficulty]
    semantic_ambiguity = {"easy": 0.1, "small_target": 0.25, "ambiguous_label": 0.85, "cluttered": 0.55, "edge_target": 0.35, "loading_sensitive": 0.35}[difficulty]
    info_missing = {"easy": 0.05, "small_target": 0.55, "ambiguous_label": 0.25, "cluttered": 0.4, "edge_target": 0.35, "loading_sensitive": 0.35}[difficulty]
    loading_dynamic = 0.8 if difficulty == "loading_sensitive" else 0.1

    if difficulty == "edge_target":
        x1 = rng.choice([20, CANVAS_W - target_size - 20])
        y1 = rng.randint(50, CANVAS_H - 90)
    else:
        x1 = rng.randint(80, CANVAS_W - target_size - 100)
        y1 = rng.randint(70, CANVAS_H - 110)
    h = max(28, int(target_size * 0.38))
    target_bbox = (x1, y1, x1 + target_size, y1 + h)

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), (252, 252, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, CANVAS_W, 50), fill=(30, 35, 45))
    draw.text((20, 16), "Synthetic GUI Pilot", fill=(255, 255, 255), font=_font(18))
    draw.text((20, CANVAS_H - 30), f"Task: click the {target_label} button", fill=(80, 80, 80), font=_font(14))

    # Draw distractors.
    boxes = [target_bbox]
    for j in range(distractor_count):
        for _ in range(100):
            w = rng.randint(52, 128)
            hh = rng.randint(28, 44)
            dx = rng.randint(45, CANVAS_W - w - 45)
            dy = rng.randint(70, CANVAS_H - hh - 60)
            box = (dx, dy, dx + w, dy + hh)
            if all(not intersects(box, b, margin=10) for b in boxes):
                boxes.append(box)
                if difficulty == "ambiguous_label" and j < 2:
                    lab = target_label  # same text, wrong location
                else:
                    lab = rng.choice([l for l in LABELS if l != target_label])
                draw_button(draw, box, lab, target=False)
                break

    draw_button(draw, target_bbox, target_label, target=True)

    if difficulty == "loading_sensitive":
        # Overlay a subtle loading hint to simulate a UI state where waiting may help.
        draw.rectangle((CANVAS_W - 180, 60, CANVAS_W - 40, 94), fill=(255, 247, 210), outline=(230, 190, 90))
        draw.text((CANVAS_W - 170, 70), "Loading...", fill=(110, 85, 20), font=_font(14))

    img_dir = outdir / "screenshots"
    img_dir.mkdir(parents=True, exist_ok=True)
    path = img_dir / f"{i:04d}_{difficulty}.png"
    img.save(path)
    return GUIState(
        state_id=f"S{i:04d}",
        difficulty=difficulty,
        task=f"Click the {target_label} button.",
        target_label=target_label,
        target_bbox=target_bbox,
        distractor_count=distractor_count,
        target_size=target_size,
        visual_ambiguity=visual_ambiguity,
        semantic_ambiguity=semantic_ambiguity,
        info_missing=info_missing,
        loading_dynamic=loading_dynamic,
        screenshot_path=str(path),
    )


def intersects(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], margin: int = 0) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 + margin < bx1 or bx2 + margin < ax1 or ay2 + margin < by1 or by2 + margin < ay1)


class SyntheticActor:
    """Simulates a GUI actor for the pilot.

    Direct is hurt by visual and semantic ambiguity.
    Observe reduces spatial/visual noise and missing information.
    Reason reduces semantic ambiguity but may not fix visual precision.
    Wait helps only loading-sensitive states.
    """

    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def _base_error_scale(self, state: GUIState, path: str) -> float:
        scale = 16 + 70 * state.visual_ambiguity + 50 * state.info_missing
        if path == "observe":
            scale *= 0.45
        elif path == "reason":
            scale *= 0.8
        elif path == "wait":
            scale *= 0.9 if state.loading_dynamic > 0.5 else 1.0
        return scale

    def _semantic_failure_prob(self, state: GUIState, path: str) -> float:
        p = 0.05 + 0.55 * state.semantic_ambiguity
        if path == "reason":
            p *= 0.45
        elif path == "observe":
            p *= 0.8
        elif path == "wait":
            p *= 0.9 if state.loading_dynamic > 0.5 else 1.0
        return clamp(p, 0.0, 0.9)

    def predict(self, state: GUIState, path: str) -> Tuple[float, float, str]:
        cx, cy = bbox_center(state.target_bbox)
        semantic_fail = self.rng.random() < self._semantic_failure_prob(state, path)
        if semantic_fail:
            # Click a plausible but wrong region.
            x = self.rng.uniform(60, CANVAS_W - 60)
            y = self.rng.uniform(70, CANVAS_H - 70)
            return x, y, "semantic_or_target_confusion"
        scale = self._base_error_scale(state, path)
        if path == "wait" and state.loading_dynamic > 0.5:
            # Waiting can improve loading-sensitive cases.
            scale *= 0.55
        x = self.rng.gauss(cx, scale)
        y = self.rng.gauss(cy, scale * 0.45)
        x = clamp(x, 0, CANVAS_W - 1)
        y = clamp(y, 0, CANVAS_H - 1)
        return x, y, "ok"


PATH_COSTS = {
    "direct": (1.0, 1),
    "observe": (1.65, 2),
    "reason": (2.2, 2),
    "wait": (2.15, 1),
}


def path_latency(path: str, rng: random.Random) -> float:
    base, _ = PATH_COSTS[path]
    return max(0.05, rng.gauss(base, base * 0.08))


def run_rollouts(states: List[GUIState], repeats: int, seed: int) -> List[Rollout]:
    actor = SyntheticActor(seed)
    rng = random.Random(seed + 1000)
    rollouts: List[Rollout] = []
    for state in states:
        for rep in range(repeats):
            for path in ["direct", "observe", "reason", "wait"]:
                x, y, note = actor.predict(state, path)
                success = int(point_in_bbox(x, y, state.target_bbox))
                latency = path_latency(path, rng)
                cost, model_calls = PATH_COSTS[path]
                rollouts.append(
                    Rollout(
                        state_id=state.state_id,
                        repeat=rep,
                        path=path,
                        x=round(x, 2),
                        y=round(y, 2),
                        success=success,
                        latency=round(latency, 4),
                        model_calls=model_calls,
                        cost=round(cost, 4),
                        notes=note,
                    )
                )
    return rollouts


def save_csv(path: Path, rows: Iterable[dict], fieldnames: List[str]):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize(states: List[GUIState], rollouts: List[Rollout]) -> Dict:
    by_path: Dict[str, List[Rollout]] = {p: [] for p in ["direct", "observe", "reason", "wait"]}
    for r in rollouts:
        by_path[r.path].append(r)
    summary = {
        "num_states": len(states),
        "num_rollouts": len(rollouts),
        "paths": {},
        "delta": {},
        "by_difficulty": {},
    }
    for p, rows in by_path.items():
        summary["paths"][p] = {
            "success_rate": mean([r.success for r in rows]),
            "avg_latency": mean([r.latency for r in rows]),
            "avg_cost": mean([r.cost for r in rows]),
            "model_calls": mean([r.model_calls for r in rows]),
        }
    direct_by_key = {(r.state_id, r.repeat): r.success for r in by_path["direct"]}
    for p in ["observe", "reason", "wait"]:
        deltas = [r.success - direct_by_key[(r.state_id, r.repeat)] for r in by_path[p]]
        summary["delta"][p] = {
            "mean_delta_vs_direct": mean(deltas),
            "positive_rate": mean([int(d > 0) for d in deltas]),
            "negative_rate": mean([int(d < 0) for d in deltas]),
        }
    state_map = {s.state_id: s for s in states}
    for diff in sorted(set(s.difficulty for s in states)):
        ids = {s.state_id for s in states if s.difficulty == diff}
        summary["by_difficulty"][diff] = {}
        for p in ["direct", "observe", "reason", "wait"]:
            rows = [r for r in by_path[p] if r.state_id in ids]
            summary["by_difficulty"][diff][p] = mean([r.success for r in rows])
    return summary


def mean(xs: List[float]) -> float:
    return float(sum(xs) / len(xs)) if xs else float("nan")


def write_summary_md(outdir: Path, summary: Dict):
    lines = []
    lines.append("# Pilot Results Summary")
    lines.append("")
    lines.append(f"- States: {summary['num_states']}")
    lines.append(f"- Rollouts: {summary['num_rollouts']}")
    lines.append("")
    lines.append("## Path Results")
    lines.append("")
    lines.append("| Path | Success Rate | Avg Latency | Avg Cost | Model Calls |")
    lines.append("|---|---:|---:|---:|---:|")
    for p, v in summary["paths"].items():
        lines.append(f"| {p} | {v['success_rate']:.3f} | {v['avg_latency']:.3f} | {v['avg_cost']:.3f} | {v['model_calls']:.2f} |")
    lines.append("")
    lines.append("## Delta vs Direct")
    lines.append("")
    lines.append("| Path | Mean Delta | Positive Rate | Negative Rate |")
    lines.append("|---|---:|---:|---:|")
    for p, v in summary["delta"].items():
        lines.append(f"| {p} | {v['mean_delta_vs_direct']:.3f} | {v['positive_rate']:.3f} | {v['negative_rate']:.3f} |")
    lines.append("")
    lines.append("## By Difficulty")
    lines.append("")
    lines.append("| Difficulty | Direct | Observe | Reason | Wait |")
    lines.append("|---|---:|---:|---:|---:|")
    for diff, vals in summary["by_difficulty"].items():
        lines.append(f"| {diff} | {vals['direct']:.3f} | {vals['observe']:.3f} | {vals['reason']:.3f} | {vals['wait']:.3f} |")
    (outdir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-states", type=int, default=50)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    t0 = time.time()
    args.outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    states = [generate_state(i, args.outdir, rng) for i in range(args.num_states)]
    rollouts = run_rollouts(states, args.repeats, args.seed)
    save_csv(args.outdir / "states.csv", [asdict(s) for s in states], list(asdict(states[0]).keys()))
    save_csv(args.outdir / "rollouts.csv", [asdict(r) for r in rollouts], list(asdict(rollouts[0]).keys()))
    summary = summarize(states, rollouts)
    summary["runtime_seconds"] = round(time.time() - t0, 3)
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary_md(args.outdir, summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
