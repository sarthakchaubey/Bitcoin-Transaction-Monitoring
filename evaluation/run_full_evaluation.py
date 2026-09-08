"""Run the complete pipeline and collect performance/timing artifacts.

This script intentionally depends on the real Phase 1 dataset and GeoLite2
installation. It does not synthesize evaluation numbers when those inputs are
missing.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

import main
from models.evaluate import evaluate_against_ground_truth


ROOT = Path(__file__).resolve().parents[1]
TIMING_PATH = ROOT / "data" / "pipeline_timing.json"
ERROR_ANALYSIS_PATH = ROOT / "data" / "error_analysis.json"
GROUND_TRUTH_PATH = ROOT / "data" / "ground_truth" / "ground_truth.csv"


def _timed(timings: dict[str, dict[str, Any]], name: str, function: Callable[[], Any]) -> Any:
    """Run one pipeline phase and record wall-clock duration."""
    started = time.perf_counter()
    try:
        result = function()
        timings[name] = {"seconds": time.perf_counter() - started, "status": "ok"}
        return result
    except Exception as exc:
        timings[name] = {
            "seconds": time.perf_counter() - started,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        raise


def _error_analysis(ranked_alerts: pd.DataFrame, ground_truth_path: Path) -> dict[str, Any]:
    """Save false-negative and false-positive examples with evidence reasons."""
    truth = pd.read_csv(ground_truth_path)
    joined = truth.merge(ranked_alerts, on="wallet_id", how="left")
    high_score = joined["final_risk_score"].fillna(0.0) >= 50.0
    illicit = joined["is_illicit"].astype(bool)
    false_negatives = joined[illicit & ~high_score]
    false_positives = joined[~illicit & high_score]

    def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
        columns = [column for column in ("wallet_id", "pattern_type", "final_risk_score") if column in frame]
        return frame[columns].fillna(0).to_dict(orient="records")

    report = {
        "threshold": 50.0,
        "false_negative_count": len(false_negatives),
        "false_positive_count": len(false_positives),
        "false_negatives": records(false_negatives),
        "false_positives": records(false_positives),
        "note": "Evidence reason sentences can be joined from data/evidence_packages.json by wallet_id.",
    }
    ERROR_ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ERROR_ANALYSIS_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report


def run() -> dict[str, Any]:
    """Execute phases 1–7, write timing/error artifacts, and print evaluation."""
    timings: dict[str, dict[str, Any]] = {}
    try:
        _timed(timings, "phase_1_dataset", main.load_or_generate_dataset)
        transactions = _timed(timings, "phase_2_ingestion", main.ingest_data)
        # GeoIP is created inside the same offline-only phase as the production entry point.
        def enrich() -> pd.DataFrame:
            from geoip.enrich import enrich_dataframe
            from geoip.lookup import GeoIPLookup
            from geoip.risk import flag_high_risk_geo

            lookup = GeoIPLookup()
            try:
                return flag_high_risk_geo(enrich_dataframe(transactions, lookup))
            finally:
                lookup.close()

        enriched = _timed(timings, "phase_3_geoip", enrich)
        graph, wallet_features = _timed(timings, "phase_4_graph", lambda: main.build_graph(enriched))
        feature_matrix, feature_table, feature_pipeline = _timed(
            timings, "phase_5_features", lambda: main.engineer_features(wallet_features, enriched)
        )
        ranked_alerts, evaluation, anomaly_detector = _timed(
            timings, "phase_6_models", lambda: main.run_models(feature_matrix, feature_table, graph)
        )
        packages = _timed(
            timings,
            "phase_7_explainability",
            lambda: main.generate_explanations(
                feature_matrix, feature_table, feature_pipeline, anomaly_detector, ranked_alerts, graph
            ),
        )
        if GROUND_TRUTH_PATH.exists():
            evaluation = evaluate_against_ground_truth(ranked_alerts, str(GROUND_TRUTH_PATH))
            error_analysis = _error_analysis(ranked_alerts, GROUND_TRUTH_PATH)
        else:
            error_analysis = {"status": "not_run", "reason": f"Missing {GROUND_TRUTH_PATH}"}
        result = {"evaluation": evaluation, "error_analysis": error_analysis, "evidence_count": len(packages)}
    except Exception as exc:
        result = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        raise
    finally:
        TIMING_PATH.parent.mkdir(parents=True, exist_ok=True)
        TIMING_PATH.write_text(json.dumps(timings, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    run()
