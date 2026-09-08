"""Generate write-up charts from evaluation artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLOTS = ROOT / "data" / "plots"
TRUTH = ROOT / "data" / "ground_truth" / "ground_truth.csv"
EVIDENCE = ROOT / "data" / "evidence_packages.json"
TIMING = ROOT / "data" / "pipeline_timing.json"
ALERT_THRESHOLD = 50.0


def _load_scores() -> pd.DataFrame:
    """Load evidence scores and join the evaluation labels."""
    if not EVIDENCE.exists() or not TRUTH.exists():
        raise FileNotFoundError("Run the full evaluation after creating ground_truth.csv and evidence_packages.json")
    evidence = pd.DataFrame(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    truth = pd.read_csv(TRUTH)
    evidence["is_illicit"] = evidence["wallet_id"].map(
        truth.set_index("wallet_id")["is_illicit"].astype(bool)
    ).fillna(False)
    return evidence


def generate_plots() -> list[Path]:
    """Create precision-recall, score, pattern, and timing charts."""
    PLOTS.mkdir(parents=True, exist_ok=True)
    scores = _load_scores()
    paths: list[Path] = []
    thresholds = list(range(101))
    positives = int(scores["is_illicit"].sum())
    precision, recall = [], []
    for threshold in thresholds:
        predicted = scores["final_risk_score"] >= threshold
        true_positive = int((predicted & scores["is_illicit"]).sum())
        precision.append(true_positive / int(predicted.sum()) if predicted.sum() else 0.0)
        recall.append(true_positive / positives if positives else 0.0)
    plt.figure()
    plt.plot(recall, precision)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall Curve")
    paths.append(PLOTS / "precision_recall_curve.png")
    plt.savefig(paths[-1], dpi=160, bbox_inches="tight")
    plt.close()

    plt.figure()
    plt.hist(scores["final_risk_score"], bins=20, edgecolor="black")
    plt.axvline(ALERT_THRESHOLD, color="red", linestyle="--", label=f"Alert threshold ({ALERT_THRESHOLD:.0f})")
    plt.xlabel("Final risk score")
    plt.ylabel("Wallet count")
    plt.title("Wallet Risk Score Distribution")
    plt.legend()
    paths.append(PLOTS / "score_distribution.png")
    plt.savefig(paths[-1], dpi=160, bbox_inches="tight")
    plt.close()

    if "pattern_type" in scores:
        pattern_rates = scores[scores["is_illicit"]].groupby("pattern_type")["final_risk_score"].apply(
            lambda values: float((values >= ALERT_THRESHOLD).mean())
        )
        plt.figure()
        pattern_rates.plot(kind="bar")
        plt.ylabel("Detection rate")
        plt.xlabel("Pattern type")
        plt.title("Detection Rate by Ground-Truth Pattern")
        plt.xticks(rotation=30, ha="right")
        paths.append(PLOTS / "pattern_detection_rates.png")
        plt.savefig(paths[-1], dpi=160, bbox_inches="tight")
        plt.close()

    if TIMING.exists():
        timing = json.loads(TIMING.read_text(encoding="utf-8"))
        timing_frame = pd.Series({name: value["seconds"] for name, value in timing.items()})
        plt.figure()
        timing_frame.plot(kind="bar")
        plt.ylabel("Seconds")
        plt.xlabel("Pipeline stage")
        plt.title("Pipeline Stage Timing")
        plt.xticks(rotation=30, ha="right")
        paths.append(PLOTS / "pipeline_timing.png")
        plt.savefig(paths[-1], dpi=160, bbox_inches="tight")
        plt.close()
    return paths


if __name__ == "__main__":
    print("Generated plots:", generate_plots())
