"""Tests for Phase 7 explainability and evidence packaging."""

from __future__ import annotations

import json

import networkx as nx
import pandas as pd

from explain.evidence_package import build_all_evidence_packages, build_evidence_package
from explain.reason_builder import build_reason_sentence, confidence_label


def explanation_fixture():
    """Return a small explanation and ranked-alert row fixture."""
    explanation = [
        {
            "feature": "fan_in",
            "shap_value": 2.5,
            "direction": "increases_risk",
            "raw_value": 47,
        },
        {
            "feature": "shared_ip_with_n_wallets",
            "shap_value": 1.2,
            "direction": "increases_risk",
            "raw_value": 6,
        },
    ]
    row = pd.Series(
        {
            "wallet_id": "A",
            "final_risk_score": 82.0,
            "community_risk_score": 72.0,
            "tx_count": 12,
            "fan_in": 47,
            "fan_out": 3,
            "distinct_ips": 2,
            "high_risk_geo_ratio": 0.4,
        }
    )
    return explanation, row


def evidence_graph():
    """Return a minimal graph containing wallet A and a transaction."""
    graph = nx.MultiDiGraph()
    graph.add_node("A", type="wallet", cluster_id=0)
    graph.add_node("tx:t1", type="transaction", txid="t1")
    graph.add_edge("A", "tx:t1", type="INPUT_TO", amount=1.0)
    return graph


def test_build_reason_sentence_is_readable_and_formatted():
    explanation, row = explanation_fixture()

    sentence = build_reason_sentence(explanation, 72.0, row)

    assert sentence.startswith("Flagged primarily due to")
    assert "distinct counterparties" in sentence
    assert "community risk: 72/100" in sentence
    assert sentence.endswith(".")


def test_confidence_label_boundaries():
    assert confidence_label(0) == "Low"
    assert confidence_label(39) == "Low"
    assert confidence_label(40) == "Medium"
    assert confidence_label(70) == "High"
    assert confidence_label(100) == "High"


def test_build_evidence_package_contains_required_fields():
    explanation, row = explanation_fixture()
    sentence = build_reason_sentence(explanation, row["community_risk_score"], row)

    package = build_evidence_package("A", evidence_graph(), row, explanation, sentence)

    assert {
        "wallet_id", "final_risk_score", "confidence_label", "reason_sentence",
        "shap_explanation", "subgraph", "pattern_hint",
    }.issubset(package)
    assert package["confidence_label"] == "High"
    assert package["subgraph"]["nodes"]
    assert package["pattern_hint"] == "fan_in_fan_out"


def test_build_all_evidence_packages_is_json_serializable(tmp_path):
    explanation, row = explanation_fixture()
    ranked = pd.DataFrame([row])

    packages = build_all_evidence_packages(
        ranked,
        evidence_graph(),
        [explanation],
        output_path=str(tmp_path / "evidence_packages.json"),
    )

    json.dumps(packages)
    assert len(packages) == 1
    assert (tmp_path / "evidence_packages.json").exists()
