"""Cluster-level graph feature computation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx
import pandas as pd

from .builder import INPUT_TO, OUTPUT_TO

FEATURE_COLUMNS = [
    "cluster_id", "tx_count", "fan_in", "fan_out", "avg_amount", "std_amount",
    "total_amount", "avg_fee", "time_between_tx_mean", "time_between_tx_std",
    "distinct_ips", "distinct_countries", "shared_ip_with_n_wallets", "high_risk_geo_ratio",
]


def _as_list(value: Any) -> list[Any]:
    """Convert a transaction list field to a safe Python list."""
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    return []


def compute_wallet_features(graph: nx.MultiDiGraph, df: pd.DataFrame) -> pd.DataFrame:
    """Compute one ML-ready feature row per wallet cluster."""
    wallet_clusters = {
        node: data.get("cluster_id")
        for node, data in graph.nodes(data=True)
        if data.get("type") == "wallet" and data.get("cluster_id") is not None
    }
    cluster_ids = sorted(set(wallet_clusters.values()), key=str)
    tx_records: list[dict[str, Any]] = []
    fan_in = defaultdict(set)
    fan_out = defaultdict(set)
    ip_clusters = defaultdict(set)

    for _, row in df.iterrows():
        txid = str(row.get("txid"))
        tx_node = f"tx:{txid}"
        if tx_node not in graph:
            continue
        input_wallets = {
            wallet_clusters[source]
            for source, _, _, data in graph.in_edges(tx_node, keys=True, data=True)
            if source in wallet_clusters and data.get("type") == INPUT_TO
        }
        output_wallets = {
            wallet_clusters[target]
            for _, target, _, data in graph.out_edges(tx_node, keys=True, data=True)
            if target in wallet_clusters and data.get("type") == OUTPUT_TO
        }
        involved = input_wallets | output_wallets
        if not involved:
            continue
        for source_cluster in input_wallets:
            fan_out[source_cluster].update(output_wallets - {source_cluster})
        for destination_cluster in output_wallets:
            fan_in[destination_cluster].update(input_wallets - {destination_cluster})

        ip = row.get("src_ip")
        country = row.get("src_country")
        high_risk = any(
            bool(value) for value in (row.get("src_high_risk_geo", False), row.get("dst_high_risk_geo", False))
            if value is not None and not pd.isna(value)
        )
        amounts = []
        for value in _as_list(row.get("input_amounts")) + _as_list(row.get("output_amounts")):
            try:
                numeric_value = float(value)
                if pd.notna(numeric_value):
                    amounts.append(numeric_value)
            except (TypeError, ValueError):
                continue
        for cluster in involved:
            tx_records.append({
                "cluster_id": cluster,
                "txid": txid,
                "timestamp": pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True),
                "amounts": amounts,
                "fee": pd.to_numeric(row.get("fee"), errors="coerce"),
                "ip": ip,
                "country": country,
                "high_risk": high_risk,
            })
            if ip is not None and not pd.isna(ip):
                ip_clusters[str(ip)].add(cluster)

    records = pd.DataFrame(tx_records)
    output: list[dict[str, Any]] = []
    for cluster in cluster_ids:
        subset = records[records["cluster_id"] == cluster] if not records.empty else records
        amounts = [amount for values in subset.get("amounts", []) for amount in values]
        timestamps = pd.to_datetime(subset.get("timestamp", pd.Series(dtype="datetime64[ns, UTC]")), errors="coerce").dropna().sort_values()
        deltas = timestamps.diff().dt.total_seconds().dropna()
        unique_ips = set(subset.get("ip", pd.Series(dtype=object)).dropna().astype(str))
        countries = set(subset.get("country", pd.Series(dtype=object)).dropna().astype(str))
        shared = set().union(*(ip_clusters[ip] for ip in unique_ips)) - {cluster} if unique_ips else set()
        risk_values = subset.get("high_risk", pd.Series(dtype=bool))
        output.append({
            "cluster_id": cluster,
            "tx_count": subset["txid"].nunique() if not subset.empty else 0,
            "fan_in": len(fan_in[cluster]),
            "fan_out": len(fan_out[cluster]),
            "avg_amount": float(pd.Series(amounts).mean()) if amounts else 0.0,
            "std_amount": float(pd.Series(amounts).std(ddof=0)) if amounts else 0.0,
            "total_amount": float(sum(amounts)),
            "avg_fee": float(subset["fee"].mean()) if not subset.empty else 0.0,
            "time_between_tx_mean": float(deltas.mean()) if not deltas.empty else 0.0,
            "time_between_tx_std": float(deltas.std(ddof=0)) if len(deltas) > 1 else 0.0,
            "distinct_ips": len(unique_ips),
            "distinct_countries": len(countries),
            "shared_ip_with_n_wallets": len(shared),
            "high_risk_geo_ratio": float(risk_values.mean()) if not risk_values.empty else 0.0,
        })
    return pd.DataFrame(output, columns=FEATURE_COLUMNS)
