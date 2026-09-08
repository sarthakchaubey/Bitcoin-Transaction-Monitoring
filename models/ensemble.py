"""Combination and ranking of model risk scores."""

from __future__ import annotations

import pandas as pd


def combine_scores(
    anomaly_scores: pd.Series,
    community_scores: pd.Series,
    weights: tuple[float, float] = (0.5, 0.5),
) -> pd.Series:
    """Return a weighted 0-100 risk score aligned by wallet index."""
    if len(weights) != 2 or any(weight < 0 for weight in weights) or sum(weights) <= 0:
        raise ValueError("weights must contain two non-negative values with a positive sum")
    anomaly, community = anomaly_scores.align(community_scores, join="outer", fill_value=0.0)
    total = sum(weights)
    return ((weights[0] * anomaly + weights[1] * community) / total).clip(0.0, 100.0).rename("final_risk_score")


def rank_alerts(
    wallet_df: pd.DataFrame,
    final_scores: pd.Series,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Return descending alert rows with scores and key review features."""
    result = wallet_df.copy()
    wallet_id_column = "wallet_id" if "wallet_id" in result.columns else "cluster_id"
    result["wallet_id"] = result[wallet_id_column]
    score_by_wallet = final_scores.to_dict()
    mapped_scores = result["wallet_id"].map(score_by_wallet)
    if mapped_scores.isna().all():
        mapped_scores = final_scores.reindex(result.index)
    result["final_risk_score"] = mapped_scores.fillna(0.0).to_numpy()
    if "anomaly_score" not in result:
        result["anomaly_score"] = 0.0
    if "community_risk_score" not in result:
        result["community_risk_score"] = 0.0
    columns = [
        "wallet_id", "final_risk_score", "anomaly_score", "community_risk_score",
        "tx_count", "fan_in", "fan_out", "distinct_ips", "high_risk_geo_ratio",
    ]
    for column in columns:
        if column not in result:
            result[column] = 0.0
    ranked = result[columns].sort_values("final_risk_score", ascending=False).reset_index(drop=True)
    return ranked.head(top_n) if top_n is not None else ranked
