"""Tests for Phase 6 anomaly, community, ensemble, and evaluation code."""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

from models.anomaly_detector import AnomalyDetector
from models.ensemble import combine_scores
from models.evaluate import evaluate_against_ground_truth
from models.graph_detector import detect_communities


def test_anomaly_detector_ranks_obvious_outlier_higher():
    X = np.array([[0.0, 0.1], [0.1, 0.0], [-0.1, 0.0], [0.0, -0.1], [10.0, 10.0]])

    detector = AnomalyDetector(contamination=0.2).fit(X)
    scores = detector.score(X)

    assert scores.shape == (5,)
    assert scores[-1] > scores[:-1].mean()
    assert scores.min() >= 0.0
    assert scores.max() <= 100.0


def test_detect_communities_separates_disconnected_wallet_groups():
    graph = nx.MultiDiGraph()
    for wallet in ("A", "B", "C", "D"):
        graph.add_node(wallet, type="wallet")
    for txid, inputs, outputs in (("t1", ["A"], ["B"]), ("t2", ["C"], ["D"])):
        tx = f"tx:{txid}"
        graph.add_node(tx, type="transaction")
        for wallet in inputs:
            graph.add_edge(wallet, tx, type="INPUT_TO")
        for wallet in outputs:
            graph.add_edge(tx, wallet, type="OUTPUT_TO")

    communities = detect_communities(graph)

    assert communities["A"] == communities["B"]
    assert communities["C"] == communities["D"]
    assert communities["A"] != communities["C"]


def test_combine_scores_returns_weighted_average():
    anomaly = pd.Series([0.0, 100.0], index=["a", "b"])
    community = pd.Series([100.0, 0.0], index=["a", "b"])

    combined = combine_scores(anomaly, community, weights=(0.25, 0.75))

    assert combined["a"] == 75.0
    assert combined["b"] == 25.0


def test_evaluation_computes_known_precision_recall(tmp_path, monkeypatch):
    ranked = pd.DataFrame(
        {
            "wallet_id": ["w1", "w2", "w3", "w4"],
            "final_risk_score": [90.0, 80.0, 70.0, 20.0],
        }
    )
    truth_path = tmp_path / "ground_truth.csv"
    pd.DataFrame(
        {
            "wallet_id": ["w1", "w2", "w3", "w4"],
            "is_illicit": [True, False, True, True],
            "pattern_type": ["peeling_chain", "benign", "fan_in_fan_out", "peeling_chain"],
        }
    ).to_csv(truth_path, index=False)
    monkeypatch.chdir(tmp_path)

    result = evaluate_against_ground_truth(ranked, str(truth_path))

    assert result["metrics"]["precision@10"] == 3 / 4
    assert result["metrics"]["recall@10"] == 1.0
    assert result["metrics"]["overall_precision_at_50"] == 2 / 3
    assert result["metrics"]["overall_recall_at_50"] == 2 / 3
    assert result["metrics"]["recall_pattern_peeling_chain"] == 0.5
