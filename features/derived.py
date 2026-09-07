"""Derived wallet signals used by downstream anomaly models.

The heuristics in this module are intentionally transparent baselines. They are
features for investigation and model input, not conclusions about activity.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from graph.clustering import (
    common_input_ownership_clusters,
    merge_change_addresses_into_clusters,
)

DERIVED_COLUMNS = [
    "amount_entropy",
    "round_number_ratio",
    "burst_score",
    "peeling_chain_score",
    "fee_to_amount_ratio",
]


def _as_list(value: Any) -> list[Any]:
    """Convert a list-like transaction field into a safe Python list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    return []


def _numeric_values(value: Any) -> list[float]:
    """Return finite numeric values from an amount field."""
    numbers: list[float] = []
    for item in _as_list(value):
        try:
            number = float(item)
        except (TypeError, ValueError):
            continue
        if np.isfinite(number) and number >= 0:
            numbers.append(number)
    return numbers


def _transaction_clusters(row: pd.Series, address_clusters: dict[str, int]) -> set[int]:
    """Find clusters represented by one raw transaction row."""
    if "cluster_id" in row and pd.notna(row.get("cluster_id")):
        return {int(row["cluster_id"])}
    addresses = _as_list(row.get("input_addresses")) + _as_list(row.get("output_addresses"))
    return {address_clusters[str(address)] for address in addresses if str(address) in address_clusters}


def _is_round_number(amount: float) -> bool:
    """Identify amounts divisible by common payment denominations."""
    return any(np.isclose(amount / denomination, round(amount / denomination), atol=1e-8)
               for denomination in (1.0, 0.1, 0.01))


def _entropy(values: list[float]) -> float:
    """Compute Shannon entropy over repeated amount values."""
    if not values:
        return 0.0
    _, counts = np.unique(np.asarray(values), return_counts=True)
    probabilities = counts / counts.sum()
    return float(-(probabilities * np.log2(probabilities)).sum())


def _cluster_records(raw_tx_df: pd.DataFrame) -> dict[int, list[dict[str, Any]]]:
    """Build compact transaction records keyed by wallet cluster."""
    if "cluster_id" in raw_tx_df.columns:
        address_clusters: dict[str, int] = {}
    else:
        address_clusters = common_input_ownership_clusters(raw_tx_df)
        address_clusters = merge_change_addresses_into_clusters(raw_tx_df, address_clusters)
    records: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for _, row in raw_tx_df.iterrows():
        clusters = _transaction_clusters(row, address_clusters)
        if not clusters:
            continue
        outputs = _numeric_values(row.get("output_amounts"))
        amounts = _numeric_values(row.get("input_amounts")) + outputs
        timestamp = pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True)
        for cluster in clusters:
            records[cluster].append({
                "timestamp": timestamp,
                "outputs": outputs,
                "amounts": amounts,
                "src_ip": row.get("src_ip"),
            })
    return records


def add_derived_features(wallet_df: pd.DataFrame, raw_tx_df: pd.DataFrame) -> pd.DataFrame:
    """Add entropy, roundness, burst, peeling, and fee-ratio wallet signals.

    ``amount_entropy`` measures diversity in output amounts: repeated identical
    amounts have entropy zero, while fragmented varied amounts have higher
    entropy. ``round_number_ratio`` records the share of amounts divisible by
    1, 0.1, or 0.01 BTC. Round values are often ordinary payments; a low ratio
    is more informative when combined with fragmentation and other signals.

    ``burst_score`` is the maximum count in any trailing ten-minute window.
    ``peeling_chain_score`` is the fraction of transactions with two outputs
    whose smaller output is at most 25% of the larger. This is a transparent
    peeling-chain baseline; a full detector using address reuse and graph hops
    is intentionally left as a future stretch goal.
    """
    result = wallet_df.copy()
    records = _cluster_records(raw_tx_df)
    derived_rows: list[dict[str, Any]] = []
    for cluster_id in result.get("cluster_id", pd.Series(dtype=object)):
        cluster_records = records.get(cluster_id, [])
        amounts = [amount for record in cluster_records for amount in record["amounts"]]
        output_amount_sets = [record["outputs"] for record in cluster_records]
        round_ratio = (
            sum(_is_round_number(amount) for amount in amounts) / len(amounts)
            if amounts else 0.0
        )
        timestamps = pd.DatetimeIndex(
            [record["timestamp"] for record in cluster_records if pd.notna(record["timestamp"])]
        ).sort_values()
        if len(timestamps):
            rolling_counts = pd.Series(1, index=timestamps).rolling("10min").sum()
            burst_score = float(rolling_counts.max())
        else:
            burst_score = 0.0
        peeling_like = [
            len(outputs) >= 2 and max(outputs) > 0 and min(outputs) / max(outputs) <= 0.25
            for outputs in output_amount_sets
        ]
        derived_rows.append({
            "cluster_id": cluster_id,
            "amount_entropy": _entropy(amounts),
            "round_number_ratio": round_ratio,
            "burst_score": burst_score,
            "peeling_chain_score": float(np.mean(peeling_like)) if peeling_like else 0.0,
        })

    derived = pd.DataFrame(derived_rows)
    if not derived.empty:
        result = result.merge(derived, on="cluster_id", how="left")
    for column in ("amount_entropy", "round_number_ratio", "burst_score", "peeling_chain_score"):
        if column not in result:
            result[column] = 0.0
    avg_amount = pd.to_numeric(result.get("avg_amount", 0), errors="coerce")
    avg_fee = pd.to_numeric(result.get("avg_fee", 0), errors="coerce")
    result["fee_to_amount_ratio"] = (avg_fee / avg_amount.replace(0, np.nan)).replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0.0)
    return result
