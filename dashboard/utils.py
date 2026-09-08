"""Shared utility functions for the Bitcoin transaction forensics dashboard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Standard color palette for confidence labels
CONFIDENCE_COLORS: dict[str, str] = {
    "high": "#E53E3E",    # Red / High risk
    "medium": "#DD6B20",  # Orange / Medium risk
    "low": "#38A169",     # Green / Low risk
}
DEFAULT_COLOR = "#718096"  # Slate / Unknown


def confidence_color(label: str | None) -> str:
    """Return a hex color string corresponding to a confidence level."""
    if not label:
        return DEFAULT_COLOR
    normalized = str(label).strip().casefold()
    return CONFIDENCE_COLORS.get(normalized, DEFAULT_COLOR)


def load_evidence_packages(path: str = "data/evidence_packages.json") -> list[dict[str, Any]]:
    """Load serializable evidence packages from disk safely."""
    target = Path(path)
    if not target.is_file():
        return []
    try:
        content = target.read_text(encoding="utf-8")
        if not content.strip():
            return []
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []
    except (json.JSONDecodeError, OSError):
        return []


def filter_alerts(
    evidence_list: list[dict[str, Any]],
    min_score: float = 0.0,
    labels: list[str] | None = None,
    patterns: list[str] | None = None,
    search: str = "",
) -> list[dict[str, Any]]:
    """Pure filter function for filtering alert records by score, labels, patterns, and wallet ID."""
    if not evidence_list:
        return []

    normalized_labels = (
        {str(lbl).strip().casefold() for lbl in labels if str(lbl).strip()}
        if labels
        else None
    )
    normalized_patterns = (
        {str(pat).strip().casefold() for pat in patterns if str(pat).strip()}
        if patterns
        else None
    )
    query = search.strip().casefold() if search else ""

    filtered: list[dict[str, Any]] = []
    for item in evidence_list:
        # Check risk score threshold
        score = float(item.get("final_risk_score", 0.0))
        if score < min_score:
            continue

        # Check confidence label
        if normalized_labels:
            label = str(item.get("confidence_label", "")).strip().casefold()
            if label not in normalized_labels:
                continue

        # Check pattern hint
        if normalized_patterns:
            pattern = str(item.get("pattern_hint", "")).strip().casefold()
            if pattern not in normalized_patterns:
                continue

        # Check search query against wallet_id
        if query:
            wallet_id = str(item.get("wallet_id", "")).casefold()
            if query not in wallet_id:
                continue

        filtered.append(item)

    return filtered
