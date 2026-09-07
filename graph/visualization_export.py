"""Graph exports and summary statistics for later visualization phases."""

from __future__ import annotations

from collections import Counter
from typing import Any

import networkx as nx


def export_subgraph_for_wallet(
    graph: nx.MultiDiGraph,
    wallet_or_cluster_id: str | int,
    hops: int = 1,
) -> nx.MultiDiGraph:
    """Return the local undirected neighborhood for a wallet or cluster ID."""
    selected = {
        node
        for node, data in graph.nodes(data=True)
        if data.get("type") == "wallet"
        and (node == wallet_or_cluster_id or data.get("cluster_id") == wallet_or_cluster_id)
    }
    if not selected:
        return nx.MultiDiGraph()
    undirected = graph.to_undirected()
    neighborhood: set[Any] = set()
    for node in selected:
        neighborhood.update(nx.single_source_shortest_path_length(undirected, node, cutoff=max(0, hops)))
    return graph.subgraph(neighborhood).copy()


def graph_summary_stats(graph: nx.MultiDiGraph) -> dict[str, Any]:
    """Return node, edge, cluster, and average cluster-size summary statistics."""
    node_types = Counter(data.get("type") for _, data in graph.nodes(data=True))
    edge_types = Counter(data.get("type") for _, _, data in graph.edges(data=True))
    cluster_sizes = Counter(
        data.get("cluster_id")
        for _, data in graph.nodes(data=True)
        if data.get("type") == "wallet" and data.get("cluster_id") is not None
    )
    return {
        "nodes_by_type": dict(node_types),
        "edges_by_type": dict(edge_types),
        "total_nodes": graph.number_of_nodes(),
        "total_edges": graph.number_of_edges(),
        "distinct_wallet_clusters": len(cluster_sizes),
        "average_cluster_size": (
            sum(cluster_sizes.values()) / len(cluster_sizes) if cluster_sizes else 0.0
        ),
    }
