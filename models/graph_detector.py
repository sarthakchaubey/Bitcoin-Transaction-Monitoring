"""Louvain community detection and community-level risk scoring."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from graph.builder import INPUT_TO, OUTPUT_TO


def _wallet_projection(graph: nx.MultiDiGraph) -> nx.Graph:
    """Project transaction-mediated wallet relationships to a weighted graph."""
    projection = nx.Graph()
    wallets = [node for node, data in graph.nodes(data=True) if data.get("type") == "wallet"]
    projection.add_nodes_from(wallets)
    for transaction, data in graph.nodes(data=True):
        if data.get("type") != "transaction":
            continue
        related = set()
        for source, _, edge_data in graph.in_edges(transaction, data=True):
            if graph.nodes[source].get("type") == "wallet" and edge_data.get("type") == INPUT_TO:
                related.add(source)
        for _, target, edge_data in graph.out_edges(transaction, data=True):
            if graph.nodes[target].get("type") == "wallet" and edge_data.get("type") == OUTPUT_TO:
                related.add(target)
        for left, right in combinations(sorted(related), 2):
            if projection.has_edge(left, right):
                projection[left][right]["weight"] += 1.0
            else:
                projection.add_edge(left, right, weight=1.0)
    return projection


def detect_communities(graph: nx.MultiDiGraph) -> dict[Any, int]:
    """Detect wallet communities with Louvain on a weighted undirected projection."""
    projection = _wallet_projection(graph)
    if not projection:
        return {}
    try:
        import community as community_louvain
        partition = community_louvain.best_partition(projection, weight="weight", random_state=42)
        return {node: int(community_id) for node, community_id in partition.items()}
    except ImportError:
        if hasattr(nx.community, "louvain_communities"):
            groups = nx.community.louvain_communities(projection, weight="weight", seed=42)
        else:
            groups = list(nx.connected_components(projection))
        return {
            node: community_id
            for community_id, group in enumerate(groups)
            for node in group
        }


def score_communities(
    graph: nx.MultiDiGraph,
    communities: dict[Any, int],
    wallet_features: pd.DataFrame,
) -> pd.DataFrame:
    """Score each wallet cluster using aggregate community risk indicators.

    Formula: ``100 * (0.40 * geo + 0.25 * shared_ip + 0.20 * density
    + 0.15 * velocity)``. Geo is the mean high-risk geography ratio, shared_ip
    is capped at five shared wallets, density is internal transaction count
    divided by possible wallet pairs, and velocity is transaction count per
    community member capped at five transactions. This is an interpretable
    ranking heuristic applied to community behavior; it is not a classifier.
    """
    wallet_id_column = "wallet_id" if "wallet_id" in wallet_features.columns else "cluster_id"
    feature_by_id = wallet_features.set_index(wallet_id_column)
    cluster_communities: dict[Any, set[int]] = defaultdict(set)
    for node, community_id in communities.items():
        cluster_id = graph.nodes[node].get("cluster_id") if node in graph else node
        if cluster_id is not None:
            cluster_communities[cluster_id].add(community_id)

    community_members = defaultdict(set)
    for node, community_id in communities.items():
        community_members[community_id].add(node)
    transaction_counts = defaultdict(int)
    for transaction, data in graph.nodes(data=True):
        if data.get("type") != "transaction":
            continue
        members = {
            communities[node]
            for node in graph.predecessors(transaction)
            if node in communities
        } | {
            communities[node]
            for node in graph.successors(transaction)
            if node in communities
        }
        for community_id in members:
            transaction_counts[community_id] += 1

    community_scores: dict[int, float] = {}
    for community_id, members in community_members.items():
        cluster_ids = [
            graph.nodes[node].get("cluster_id")
            for node in members
            if graph.nodes[node].get("cluster_id") in feature_by_id.index
        ]
        rows = feature_by_id.loc[cluster_ids] if cluster_ids else feature_by_id.iloc[0:0]
        geo_values = rows["high_risk_geo_ratio"] if "high_risk_geo_ratio" in rows else pd.Series(dtype=float)
        shared_values = rows["shared_ip_with_n_wallets"] if "shared_ip_with_n_wallets" in rows else pd.Series(dtype=float)
        geo = float(pd.to_numeric(geo_values, errors="coerce").mean()) if not geo_values.empty else 0.0
        shared = float(pd.to_numeric(shared_values, errors="coerce").mean()) if not shared_values.empty else 0.0
        geo = 0.0 if np.isnan(geo) else geo
        shared = 0.0 if np.isnan(shared) else shared
        shared_signal = min(shared / 5.0, 1.0)
        possible_pairs = max(len(members) * (len(members) - 1) / 2, 1)
        internal_density = min(transaction_counts[community_id] / possible_pairs, 1.0)
        velocity = min(transaction_counts[community_id] / max(len(members), 1) / 5.0, 1.0)
        community_scores[community_id] = 100.0 * (
            0.40 * min(max(geo, 0.0), 1.0)
            + 0.25 * shared_signal
            + 0.20 * internal_density
            + 0.15 * velocity
        )

    rows = []
    for wallet_id in feature_by_id.index:
        scores = [community_scores[community] for community in cluster_communities.get(wallet_id, set())]
        wallet_communities = cluster_communities.get(wallet_id, set())
        rows.append({
            "wallet_id": wallet_id,
            "community_id": min(wallet_communities) if wallet_communities else None,
            "community_risk_score": max(scores, default=0.0),
        })

    # STRETCH GOAL (not implemented): replace this interpretable projection
    # with a GraphSAGE model from torch_geometric, using ground-truth labels
    # only as weak supervision and evaluating on held-out wallet clusters.
    return pd.DataFrame(rows, columns=["wallet_id", "community_id", "community_risk_score"])
