"""Tests for entity/transaction graph construction and features."""

from __future__ import annotations

import pandas as pd

from graph.builder import INPUT_TO, OUTPUT_TO, build_graph
from graph.clustering import (
    annotate_graph_with_clusters,
    common_input_ownership_clusters,
)
from graph.features import compute_wallet_features
from graph.visualization_export import export_subgraph_for_wallet


def graph_frame() -> pd.DataFrame:
    """Return a small manually verifiable transaction fixture."""
    return pd.DataFrame(
        [
            {
                "timestamp": pd.Timestamp("2024-01-01T00:00:00Z"),
                "src_ip": "8.8.8.8", "dst_ip": "1.1.1.1",
                "src_port": 1000, "dst_port": 8333, "txid": "t1",
                "input_addresses": ["A", "B"], "output_addresses": ["C"],
                "input_amounts": [2.0, 3.0], "output_amounts": [4.9],
                "fee": 0.1, "script_type": "p2pkh",
                "src_country": "US", "src_high_risk_geo": False, "dst_high_risk_geo": False,
            },
            {
                "timestamp": pd.Timestamp("2024-01-02T00:00:00Z"),
                "src_ip": "8.8.8.8", "dst_ip": "9.9.9.9",
                "src_port": 1001, "dst_port": 8333, "txid": "t2",
                "input_addresses": ["C"], "output_addresses": ["D"],
                "input_amounts": [4.0], "output_amounts": [3.9],
                "fee": 0.1, "script_type": "p2wpkh",
                "src_country": "US", "src_high_risk_geo": True, "dst_high_risk_geo": False,
            },
        ]
    )


def clustered_graph():
    """Build and annotate the fixture graph for feature tests."""
    frame = graph_frame()
    graph = build_graph(frame)
    clusters = common_input_ownership_clusters(frame)
    annotate_graph_with_clusters(graph, clusters)
    return frame, graph, clusters


def test_build_graph_has_expected_nodes_edges_and_types():
    graph = build_graph(graph_frame())

    assert graph.number_of_nodes() == 9  # 4 wallets, 2 transactions, 3 unique IPs
    assert graph.number_of_edges() == 9  # 3 input, 2 output, 4 broadcast
    assert sum(data["type"] == "wallet" for _, data in graph.nodes(data=True)) == 4
    assert sum(data["type"] == "transaction" for _, data in graph.nodes(data=True)) == 2
    assert sum(data["type"] == "ip" for _, data in graph.nodes(data=True)) == 3
    assert sum(data["type"] == INPUT_TO for _, _, data in graph.edges(data=True)) == 3
    assert sum(data["type"] == OUTPUT_TO for _, _, data in graph.edges(data=True)) == 2
    assert graph.nodes["tx:t1"]["fee"] == 0.1


def test_common_input_clusters_merge_only_coappearing_addresses():
    frame = graph_frame()

    clusters = common_input_ownership_clusters(frame)

    assert clusters["A"] == clusters["B"]
    assert clusters["A"] != clusters["C"]
    assert clusters["C"] != clusters["D"]


def test_wallet_features_have_expected_transaction_and_counterparty_counts():
    frame, graph, clusters = clustered_graph()

    features = compute_wallet_features(graph, frame).set_index("cluster_id")
    cluster_ab = clusters["A"]
    cluster_c = clusters["C"]
    cluster_d = clusters["D"]

    assert features.loc[cluster_ab, "tx_count"] == 1
    assert features.loc[cluster_ab, "fan_out"] == 1
    assert features.loc[cluster_ab, "fan_in"] == 0
    assert features.loc[cluster_c, "tx_count"] == 2
    assert features.loc[cluster_c, "fan_in"] == 1
    assert features.loc[cluster_c, "fan_out"] == 1
    assert features.loc[cluster_d, "tx_count"] == 1
    assert features.loc[cluster_d, "fan_in"] == 1


def test_export_subgraph_respects_hop_distance():
    _, graph, _ = clustered_graph()

    subgraph = export_subgraph_for_wallet(graph, "A", hops=1)

    assert set(subgraph.nodes) == {"A", "tx:t1"}
    assert "tx:t2" not in subgraph
    assert "C" not in subgraph
