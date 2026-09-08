"""Evaluation against hidden ground-truth labels."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _as_bool(value) -> bool:
    """Normalize common CSV representations of an illicit label."""
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "illicit"}
    return bool(value)


def evaluate_against_ground_truth(
    ranked_alerts: pd.DataFrame,
    ground_truth_path: str,
) -> dict:
    """Join ranked alerts to labels and write precision/recall evaluation output."""
    truth = pd.read_csv(ground_truth_path)
    required = {"wallet_id", "is_illicit"}
    missing = required - set(truth.columns)
    if missing:
        raise ValueError(f"Ground truth is missing columns: {sorted(missing)}")
    # Ground truth is evaluation-only and must never be included in model features.
    evaluation = ranked_alerts.merge(truth, on="wallet_id", how="left", suffixes=("", "_truth"))
    evaluation["is_illicit"] = evaluation["is_illicit"].fillna(False).map(_as_bool)
    total_true = int(truth["is_illicit"].map(_as_bool).sum())
    rows: list[dict] = []
    for k in [10, 50, 100, total_true]:
        if k <= 0 or evaluation.empty:
            continue
        actual_k = min(k, len(evaluation))
        selected = evaluation.head(actual_k)
        true_positive = int(selected["is_illicit"].sum())
        rows.append({
            "metric": f"precision@{k}",
            "value": true_positive / actual_k if actual_k else 0.0,
        })
        rows.append({
            "metric": f"recall@{k}",
            "value": true_positive / total_true if total_true else 0.0,
        })

    predicted = evaluation["final_risk_score"] >= 50.0
    true_positive = int((predicted & evaluation["is_illicit"]).sum())
    false_positive = int((predicted & ~evaluation["is_illicit"]).sum())
    false_negative = int((~predicted & evaluation["is_illicit"]).sum())
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    rows.extend([
        {"metric": "overall_precision_at_50", "value": precision},
        {"metric": "overall_recall_at_50", "value": recall},
        {"metric": "overall_f1_at_50", "value": f1},
    ])

    if "pattern_type" in evaluation.columns:
        for pattern, group in evaluation[evaluation["is_illicit"]].groupby("pattern_type"):
            detected = int((group["final_risk_score"] >= 50.0).sum())
            rows.append({
                "metric": f"recall_pattern_{pattern}",
                "value": detected / len(group) if len(group) else 0.0,
            })
    report = pd.DataFrame(rows)
    report_path = Path("data/evaluation_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report.to_string(index=False) + "\n", encoding="utf-8")
    print("\nModel evaluation summary")
    print(report.to_string(index=False))
    return {
        "metrics": dict(zip(report["metric"], report["value"])),
        "evaluation": evaluation,
        "report": report,
    }
