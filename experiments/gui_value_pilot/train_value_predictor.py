"""Train a lightweight value predictor on pilot CSV outputs.

This script is intentionally dependency-light: numpy + pandas only.
It trains logistic regression with gradient descent to predict whether a path
(`observe` or `reason`) has positive mean delta over `direct` for a state.

This is a sanity-stage predictor, not a final paper model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


FEATURES = [
    "distractor_count",
    "target_size",
    "visual_ambiguity",
    "semantic_ambiguity",
    "info_missing",
    "loading_dynamic",
]


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -40, 40)))


def train_logreg(X, y, lr=0.08, epochs=2000, l2=1e-3):
    n, d = X.shape
    w = np.zeros(d)
    b = 0.0
    for _ in range(epochs):
        p = sigmoid(X @ w + b)
        grad_w = (X.T @ (p - y)) / n + l2 * w
        grad_b = float(np.mean(p - y))
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def auroc(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    pos = p[y == 1]
    neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    # Mann-Whitney U interpretation.
    wins = 0.0
    for pp in pos:
        wins += np.sum(pp > neg) + 0.5 * np.sum(pp == neg)
    return float(wins / (len(pos) * len(neg)))


def brier(y, p):
    return float(np.mean((p - y) ** 2))


def ece(y, p, bins=10):
    y = np.asarray(y)
    p = np.asarray(p)
    total = len(y)
    val = 0.0
    for i in range(bins):
        lo, hi = i / bins, (i + 1) / bins
        mask = (p >= lo) & (p < hi if i < bins - 1 else p <= hi)
        if np.any(mask):
            conf = float(np.mean(p[mask]))
            acc = float(np.mean(y[mask]))
            val += (np.sum(mask) / total) * abs(conf - acc)
    return float(val)


def f1_at_half(y, p):
    pred = (p >= 0.5).astype(int)
    tp = np.sum((pred == 1) & (y == 1))
    fp = np.sum((pred == 1) & (y == 0))
    fn = np.sum((pred == 0) & (y == 1))
    if tp + fp == 0 or tp + fn == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0


def standardize(train_X, X):
    mu = train_X.mean(axis=0)
    sigma = train_X.std(axis=0)
    sigma[sigma < 1e-8] = 1.0
    return (X - mu) / sigma, mu, sigma


def build_dataset(run_dir: Path, path_name: str):
    states = pd.read_csv(run_dir / "states.csv")
    rolls = pd.read_csv(run_dir / "rollouts.csv")
    direct = rolls[rolls["path"] == "direct"].groupby("state_id")["success"].mean()
    target = rolls[rolls["path"] == path_name].groupby("state_id")["success"].mean()
    df = states.copy()
    df["direct_success_mean"] = df["state_id"].map(direct)
    df[f"{path_name}_success_mean"] = df["state_id"].map(target)
    df["delta"] = df[f"{path_name}_success_mean"] - df["direct_success_mean"]
    df["positive_gain"] = (df["delta"] > 0).astype(int)
    return df


def split_by_state(df: pd.DataFrame, seed: int):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(df))
    rng.shuffle(idx)
    n = len(idx)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)
    return idx[:train_end], idx[train_end:val_end], idx[val_end:]


def evaluate(y, p):
    return {
        "auroc": auroc(y, p),
        "brier": brier(y, p),
        "ece": ece(y, p),
        "f1_at_0.5": f1_at_half(y, p),
        "positive_rate": float(np.mean(y)),
        "mean_prediction": float(np.mean(p)),
    }


def run_for_path(run_dir: Path, path_name: str, seed: int):
    df = build_dataset(run_dir, path_name)
    train_idx, val_idx, test_idx = split_by_state(df, seed)
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["positive_gain"].to_numpy(dtype=float)
    X_train_raw = X[train_idx]
    X_train, mu, sigma = standardize(X_train_raw, X_train_raw)
    X_val = (X[val_idx] - mu) / sigma
    X_test = (X[test_idx] - mu) / sigma
    w, b = train_logreg(X_train, y[train_idx])
    results = {}
    for split_name, idxs, Xs in [("train", train_idx, X_train), ("val", val_idx, X_val), ("test", test_idx, X_test)]:
        p = sigmoid(Xs @ w + b)
        results[split_name] = evaluate(y[idxs], p)
    results["weights"] = {feat: float(weight) for feat, weight in zip(FEATURES, w)}
    results["bias"] = float(b)
    results["num_states"] = int(len(df))
    results["num_positive"] = int(df["positive_gain"].sum())
    return results


def write_md(out_path: Path, all_results: Dict):
    lines = ["# Value Predictor Results", ""]
    for path_name, result in all_results.items():
        lines.append(f"## {path_name}")
        lines.append("")
        lines.append("| Split | AUROC | Brier | ECE | F1@0.5 | Positive Rate | Mean Prediction |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for split in ["train", "val", "test"]:
            r = result[split]
            lines.append(
                f"| {split} | {r['auroc']:.3f} | {r['brier']:.3f} | {r['ece']:.3f} | {r['f1_at_0.5']:.3f} | {r['positive_rate']:.3f} | {r['mean_prediction']:.3f} |"
            )
        lines.append("")
        lines.append("Feature weights:")
        for feat, weight in result["weights"].items():
            lines.append(f"- {feat}: {weight:.3f}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    all_results = {}
    for path_name in ["observe", "reason"]:
        all_results[path_name] = run_for_path(args.run_dir, path_name, args.seed)
    (args.outdir / "value_predictor_results.json").write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_md(args.outdir / "value_predictor_results.md", all_results)
    print(json.dumps(all_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
