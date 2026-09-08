"""Human-readable explanations for investigator review."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

# Tunable triage thresholds; these labels are operational guidance, not legal findings.
LOW_RISK_MAX = 40.0
MEDIUM_RISK_MAX = 70.0

FEATURE_PHRASES = {
    "fan_in": "distinct counterparties sending value to the wallet",
    "fan_out": "distinct counterparties receiving value from the wallet",
    "shared_ip_with_n_wallets": "wallet clusters sharing the same broadcast IP",
    "distinct_ips": "distinct broadcast IPs",
    "distinct_countries": "geographic hopping across countries",
    "high_risk_geo_ratio": "transactions involving configured high-risk geographies",
    "burst_score": "rapid transaction bursts",
    "peeling_chain_score": "repeated small-output splits consistent with a peeling pattern",
    "amount_entropy": "highly varied transaction amounts",
    "round_number_ratio": "round-number payment amounts",
    "fee_to_amount_ratio": "fees unusually large relative to transferred amounts",
    "tx_count": "transaction activity",
    "avg_amount": "average transaction amount",
    "total_amount": "total transferred amount",
}


def confidence_label(final_risk_score: float) -> str:
    """Map a 0-100 risk score to a simple investigator triage label."""
    score = float(final_risk_score)
    if score < LOW_RISK_MAX:
        return "Low"
    if score < MEDIUM_RISK_MAX:
        return "Medium"
    return "High"


def _format_value(value: Any) -> str:
    """Format raw feature values without exposing technical NaN output."""
    try:
        number = float(value)
        if math.isfinite(number):
            return f"{number:.2f}" if not number.is_integer() else str(int(number))
    except (TypeError, ValueError):
        pass
    return str(value)


def build_reason_sentence(
    shap_explanation: list[dict],
    community_risk_score: float,
    raw_features: pd.Series,
) -> str:
    """Convert top SHAP contributions and community context into plain English."""
    clauses = []
    for item in shap_explanation[:3]:
        feature = item.get("feature", "unknown feature")
        base_feature = feature.split("_", 1)[0] if feature not in FEATURE_PHRASES else feature
        phrase = FEATURE_PHRASES.get(feature, FEATURE_PHRASES.get(base_feature, feature.replace("_", " ")))
        value = item.get("raw_value", raw_features.get(feature, "unknown"))
        direction = item.get("direction")
        qualifier = "elevated" if direction == "increases_risk" else "lower"
        percentile = item.get("percentile")
        context = f", in approximately the top {percentile:.0f}% of wallets" if percentile is not None else ""
        clauses.append(f"{qualifier} {phrase} ({_format_value(value)}{context})")
    if clauses:
        reason = "Flagged primarily due to " + "; ".join(clauses) + "."
    else:
        reason = "Flagged because the combined model signals indicate unusual activity."
    reason += (
        f" The wallet also belongs to a community with elevated network risk "
        f"(community risk: {float(community_risk_score):.0f}/100)."
    )
    return reason
