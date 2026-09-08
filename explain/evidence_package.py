"""Serializable evidence records for dashboard and investigator use."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from graph.visualization_export import export_subgraph_for_wallet

from .reason_builder import build_reason_sentence, confidence_label


def _json_value(value: Any) -> Any:
    """Convert pandas, NumPy, and timestamp values to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    missing = pd.isna(value)
    if isinstance(missing, (bool, np.bool_)) and missing:
        return None
    return str(value)


def _serialize_subgraph(graph: nx.MultiDiGraph) -> dict[str, list[dict[str, Any]]]:
    """Serialize a NetworkX subgraph without retaining a non-JSON graph object."""
    nodes = [
        {"id": _json_value(node), **{key: _json_value(value) for key, value in data.items()}}
        for node, data in graph.nodes(data=True)
    ]
    edges = [
        {
            "source": _json_value(source), "target": _json_value(target), "key": _json_value(key),
            **{name: _json_value(value) for name, value in data.items()},
        }
        for source, target, key, data in graph.edges(keys=True, data=True)
    ]
    return {"nodes": nodes, "edges": edges}


def _pattern_hint(shap_explanation: list[dict]) -> str:
    """Return a best-effort pattern hint from dominant explanation features."""
    names = {str(item.get("feature", "")).casefold() for item in shap_explanation}
    if any("peeling" in name or "amount_entropy" in name for name in names):
        return "peeling_chain"
    if any("fan_in" in name or "fan_out" in name for name in names):
        return "fan_in_fan_out"
    if any("burst" in name or "fee_to_amount" in name for name in names):
        return "rapid_cashout"
    if any("shared_ip" in name or "distinct_ip" in name for name in names):
        return "shared_ip_cluster"
    return "unknown"


def build_evidence_package(
    wallet_id: Any,
    G: nx.MultiDiGraph,
    ranked_alerts_row: pd.Series,
    shap_explanation: list[dict],
    reason_sentence: str,
) -> dict[str, Any]:
    """Build one complete, JSON-safe evidence record for a flagged wallet."""
    subgraph = export_subgraph_for_wallet(G, wallet_id, hops=1)
    final_score = float(ranked_alerts_row.get("final_risk_score", 0.0))
    return {
        "wallet_id": _json_value(wallet_id),
        "final_risk_score": final_score,
        "confidence_label": confidence_label(final_score),
        "reason_sentence": reason_sentence,
        "shap_explanation": shap_explanation,
        "subgraph": _serialize_subgraph(subgraph),
        "pattern_hint": _pattern_hint(shap_explanation),
    }


def build_all_evidence_packages(
    ranked_alerts: pd.DataFrame,
    G: nx.MultiDiGraph,
    shap_explanations: list[list[dict]] | dict[Any, list[dict]],
    top_n: int | None = None,
    output_path: str = "data/evidence_packages.json",
) -> list[dict[str, Any]]:
    """Build and save evidence records for ranked alerts."""
    rows = ranked_alerts.head(top_n) if top_n is not None else ranked_alerts
    packages = []
    for position, (_, row) in enumerate(rows.iterrows()):
        wallet_id = row.get("wallet_id")
        if isinstance(shap_explanations, dict):
            explanation = shap_explanations.get(wallet_id, [])
        else:
            explanation = shap_explanations[position] if position < len(shap_explanations) else []
        reason = build_reason_sentence(
            explanation,
            float(row.get("community_risk_score", 0.0)),
            row,
        )
        packages.append(build_evidence_package(wallet_id, G, row, explanation, reason))
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(packages, indent=2, default=_json_value), encoding="utf-8")
    return packages
