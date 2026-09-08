"""Unit tests for dashboard utility and data filtering functions."""

from __future__ import annotations

import json
import re

import pytest

from dashboard.utils import (
    CONFIDENCE_COLORS,
    DEFAULT_COLOR,
    compute_network_summary_stats,
    confidence_color,
    extract_subgraph_metrics,
    filter_alerts,
    generate_forensic_dossier_markdown,
    load_evidence_packages,
)

HEX_COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


@pytest.fixture
def sample_evidence_list() -> list[dict]:
    """Return a representative list of evidence packages for testing."""
    return [
        {
            "wallet_id": "wallet_alpha_001",
            "final_risk_score": 88.5,
            "confidence_label": "High",
            "pattern_hint": "peeling_chain",
            "reason_sentence": "Flagged due to elevated peeling chain score.",
            "shap_explanation": [
                {"feature": "peeling_chain_score", "shap_value": 0.45, "direction": "increases_risk", "raw_value": 0.95},
                {"feature": "tx_count", "shap_value": 0.12, "direction": "increases_risk", "raw_value": 15},
            ],
            "subgraph": {
                "nodes": [
                    {"id": "wallet_alpha_001", "type": "wallet"},
                    {"id": "tx_01", "type": "transaction", "fee": 0.0005},
                    {"id": "1.1.1.1", "type": "ip", "country": "Australia", "high_risk": False},
                ],
                "edges": [
                    {"source": "wallet_alpha_001", "target": "tx_01", "type": "INPUT_TO", "amount": 5.0},
                ],
            },
        },
        {
            "wallet_id": "wallet_beta_002",
            "final_risk_score": 62.0,
            "confidence_label": "Medium",
            "pattern_hint": "fan_in_fan_out",
            "reason_sentence": "Flagged due to fan-in and fan-out counterparty counts.",
            "shap_explanation": [
                {"feature": "fan_in", "shap_value": 0.30, "direction": "increases_risk", "raw_value": 8},
                {"feature": "fan_out", "shap_value": 0.25, "direction": "increases_risk", "raw_value": 12},
            ],
            "subgraph": {
                "nodes": [
                    {"id": "wallet_beta_002", "type": "wallet"},
                    {"id": "8.8.8.8", "type": "ip", "country": "United States", "high_risk": True},
                ],
                "edges": [],
            },
        },
        {
            "wallet_id": "wallet_gamma_003",
            "final_risk_score": 35.0,
            "confidence_label": "Low",
            "pattern_hint": "shared_ip_cluster",
            "reason_sentence": "Low risk with slight shared IP flag.",
            "shap_explanation": [
                {"feature": "shared_ip_with_n_wallets", "shap_value": 0.05, "direction": "increases_risk", "raw_value": 1},
            ],
            "subgraph": {"nodes": [{"id": "wallet_gamma_003", "type": "wallet"}], "edges": []},
        },
        {
            "wallet_id": "wallet_delta_004",
            "final_risk_score": 15.0,
            "confidence_label": "Low",
            "pattern_hint": "unknown",
            "reason_sentence": "Normal baseline activity.",
            "shap_explanation": [],
            "subgraph": {"nodes": [{"id": "wallet_delta_004", "type": "wallet"}], "edges": []},
        },
    ]


def test_confidence_color_returns_valid_hex_codes():
    """Verify confidence_color produces valid hex codes for standard labels."""
    for label in ["High", "Medium", "Low", "high", "MEDIUM", "low"]:
        color = confidence_color(label)
        assert HEX_COLOR_REGEX.match(color) is not None

    assert confidence_color("High") == CONFIDENCE_COLORS["high"]
    assert confidence_color("Medium") == CONFIDENCE_COLORS["medium"]
    assert confidence_color("Low") == CONFIDENCE_COLORS["low"]


def test_confidence_color_fallback_for_unknown_or_none():
    """Verify confidence_color returns default fallback color for None/empty/unknown."""
    assert confidence_color(None) == DEFAULT_COLOR
    assert confidence_color("") == DEFAULT_COLOR
    assert confidence_color("Unrecognized") == DEFAULT_COLOR


def test_filter_alerts_by_min_score(sample_evidence_list):
    """Verify filtering by minimum final_risk_score threshold."""
    all_results = filter_alerts(sample_evidence_list, min_score=0.0)
    assert len(all_results) == 4

    high_med = filter_alerts(sample_evidence_list, min_score=50.0)
    assert len(high_med) == 2
    assert {r["wallet_id"] for r in high_med} == {"wallet_alpha_001", "wallet_beta_002"}

    top_only = filter_alerts(sample_evidence_list, min_score=80.0)
    assert len(top_only) == 1
    assert top_only[0]["wallet_id"] == "wallet_alpha_001"

    none_match = filter_alerts(sample_evidence_list, min_score=95.0)
    assert len(none_match) == 0


def test_filter_alerts_by_confidence_label(sample_evidence_list):
    """Verify filtering by confidence labels."""
    high_only = filter_alerts(sample_evidence_list, labels=["High"])
    assert len(high_only) == 1
    assert high_only[0]["wallet_id"] == "wallet_alpha_001"

    high_and_med = filter_alerts(sample_evidence_list, labels=["high", "medium"])
    assert len(high_and_med) == 2
    assert {r["wallet_id"] for r in high_and_med} == {"wallet_alpha_001", "wallet_beta_002"}

    low_only = filter_alerts(sample_evidence_list, labels=["Low"])
    assert len(low_only) == 2
    assert {r["wallet_id"] for r in low_only} == {"wallet_gamma_003", "wallet_delta_004"}


def test_filter_alerts_by_pattern_hint(sample_evidence_list):
    """Verify filtering by pattern_hint."""
    peeling = filter_alerts(sample_evidence_list, patterns=["peeling_chain"])
    assert len(peeling) == 1
    assert peeling[0]["wallet_id"] == "wallet_alpha_001"

    multi_pattern = filter_alerts(sample_evidence_list, patterns=["peeling_chain", "shared_ip_cluster"])
    assert len(multi_pattern) == 2
    assert {r["wallet_id"] for r in multi_pattern} == {"wallet_alpha_001", "wallet_gamma_003"}


def test_filter_alerts_by_search_query(sample_evidence_list):
    """Verify substring searching on wallet_id."""
    search_beta = filter_alerts(sample_evidence_list, search="BETA")
    assert len(search_beta) == 1
    assert search_beta[0]["wallet_id"] == "wallet_beta_002"

    search_wallet = filter_alerts(sample_evidence_list, search="wallet_")
    assert len(search_wallet) == 4

    search_nonexistent = filter_alerts(sample_evidence_list, search="non_existent_wallet")
    assert len(search_nonexistent) == 0


def test_filter_alerts_combined_criteria(sample_evidence_list):
    """Verify combining score, label, pattern, and search filters."""
    combined = filter_alerts(
        sample_evidence_list,
        min_score=50.0,
        labels=["High", "Medium"],
        patterns=["peeling_chain", "fan_in_fan_out"],
        search="alpha",
    )
    assert len(combined) == 1
    assert combined[0]["wallet_id"] == "wallet_alpha_001"

    empty_combined = filter_alerts(
        sample_evidence_list,
        min_score=50.0,
        labels=["Low"],
    )
    assert len(empty_combined) == 0


def test_filter_alerts_handles_empty_input():
    """Verify filter_alerts returns empty list when given empty input."""
    assert filter_alerts([]) == []


def test_load_evidence_packages_from_file(tmp_path, sample_evidence_list):
    """Verify load_evidence_packages correctly parses JSON file."""
    file_path = tmp_path / "evidence_packages.json"
    file_path.write_text(json.dumps(sample_evidence_list), encoding="utf-8")

    loaded = load_evidence_packages(str(file_path))
    assert len(loaded) == 4
    assert loaded[0]["wallet_id"] == "wallet_alpha_001"


def test_load_evidence_packages_handles_missing_and_corrupt(tmp_path):
    """Verify load_evidence_packages gracefully handles missing or invalid files."""
    assert load_evidence_packages(str(tmp_path / "does_not_exist.json")) == []

    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("NOT_JSON_DATA", encoding="utf-8")
    assert load_evidence_packages(str(corrupt_file)) == []

    empty_file = tmp_path / "empty.json"
    empty_file.write_text("", encoding="utf-8")
    assert load_evidence_packages(str(empty_file)) == []


def test_extract_subgraph_metrics(sample_evidence_list):
    """Verify extract_subgraph_metrics computes node counts, flows, and fees."""
    subgraph = sample_evidence_list[0]["subgraph"]
    metrics = extract_subgraph_metrics(subgraph)

    assert metrics["total_nodes"] == 3
    assert metrics["total_edges"] == 1
    assert metrics["wallet_count"] == 1
    assert metrics["tx_count"] == 1
    assert metrics["ip_count"] == 1
    assert metrics["total_inflow_btc"] == 5.0
    assert metrics["total_fees_btc"] == 0.0005
    assert len(metrics["ips"]) == 1
    assert metrics["ips"][0]["country"] == "Australia"


def test_compute_network_summary_stats(sample_evidence_list):
    """Verify compute_network_summary_stats aggregates network-wide metrics."""
    stats = compute_network_summary_stats(sample_evidence_list)

    assert stats["total_wallets"] == 4
    assert stats["max_risk_score"] == 88.5
    assert stats["min_risk_score"] == 15.0
    assert stats["pattern_counts"]["peeling_chain"] == 1
    assert stats["confidence_counts"]["High"] == 1
    assert stats["high_risk_geo_count"] == 1


def test_generate_forensic_dossier_markdown(sample_evidence_list):
    """Verify generate_forensic_dossier_markdown produces formatted case report."""
    evidence = sample_evidence_list[0]
    md = generate_forensic_dossier_markdown(
        evidence=evidence,
        analyst_notes="Suspicious peel hop to Australia IP",
        triage_status="Confirmed Suspicious",
    )

    assert "# 🛡️ BITCOIN FORENSICS AUDIT CASE DOSSIER" in md
    assert "wallet_alpha_001" in md
    assert "CONFIRMED SUSPICIOUS" in md
    assert "88.5 / 100" in md
    assert "Suspicious peel hop to Australia IP" in md
    assert "peeling_chain_score" in md
