"""Bitcoin wallet clustering heuristics."""

from __future__ import annotations

import logging
from typing import Any

import networkx as nx
import pandas as pd

LOGGER = logging.getLogger(__name__)


def _as_list(value: Any) -> list[Any]:
    """Convert a transaction list field to a safe Python list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    return []


class _UnionFind:
    """Small disjoint-set implementation used for deterministic clustering."""

    def __init__(self, values: set[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        """Return the representative root for a value."""
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        """Merge two sets."""
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def common_input_ownership_clusters(df: pd.DataFrame) -> dict[str, int]:
    """Cluster addresses that co-occur as inputs using the common-input heuristic."""
    addresses: set[str] = set()
    for column in ("input_addresses", "output_addresses"):
        for values in df.get(column, pd.Series(dtype=object)):
            addresses.update(
                str(address) for address in _as_list(values) if address is not None
            )
    union_find = _UnionFind(addresses)
    for values in df.get("input_addresses", pd.Series(dtype=object)):
        inputs = [str(address) for address in _as_list(values) if address is not None]
        for address in inputs[1:]:
            union_find.union(inputs[0], address)

    roots = sorted({union_find.find(address) for address in addresses})
    root_ids = {root: cluster_id for cluster_id, root in enumerate(roots)}
    return {address: root_ids[union_find.find(address)] for address in sorted(addresses)}


def likely_change_address(row: pd.Series) -> str | None:
    """Guess a change output using simple amount-shape heuristics.

    This deliberately conservative heuristic treats a sole non-round output as
    change, or chooses the much smaller output in a two-output transaction.
    Real forensic systems use address reuse, script, timing, and many other
    signals; this is only a transparent baseline for the project.
    """
    addresses = _as_list(row.get("output_addresses"))
    amounts = _as_list(row.get("output_amounts"))
    if len(addresses) != len(amounts) or not addresses:
        return None
    try:
        numeric = [float(amount) for amount in amounts]
    except (TypeError, ValueError):
        return None

    non_round = [index for index, amount in enumerate(numeric) if abs(amount - round(amount)) > 1e-8]
    if len(addresses) >= 2 and len(non_round) == 1:
        return str(addresses[non_round[0]])
    if len(addresses) == 2 and min(numeric) >= 0 and max(numeric) > 0:
        if min(numeric) / max(numeric) <= 0.25:
            return str(addresses[numeric.index(min(numeric))])
    return None


def merge_change_addresses_into_clusters(
    df: pd.DataFrame,
    clusters: dict[str, int],
) -> dict[str, int]:
    """Assign likely change outputs to the input cluster for each transaction."""
    result = dict(clusters)
    for _, row in df.iterrows():
        change = likely_change_address(row)
        inputs = [str(address) for address in _as_list(row.get("input_addresses")) if address is not None]
        if change is None or not inputs:
            continue
        input_clusters = [result[address] for address in inputs if address in result]
        if not input_clusters:
            continue
        result[change] = input_clusters[0]
    return result


def annotate_graph_with_clusters(
    graph: nx.MultiDiGraph,
    clusters: dict[str, int],
) -> nx.MultiDiGraph:
    """Add cluster IDs to wallet nodes in-place and return the graph."""
    for node, data in graph.nodes(data=True):
        if data.get("type") == "wallet":
            data["cluster_id"] = clusters.get(data.get("address", node))
    return graph
