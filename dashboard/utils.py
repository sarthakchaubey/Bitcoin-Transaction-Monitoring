"""Shared utility functions and design system constants for the Bitcoin forensics dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Visual Design Tokens from ANTIGRAVITY_DASHBOARD_BRIEF.md
DESIGN_TOKENS = {
    "bg": "#0B1220",             # App background
    "surface": "#131B2E",        # Card/table background
    "surface_raised": "#1A2438", # Table headers, hover
    "border": "#1F2A44",         # Borders and outlines
    "text": "#E8E6DE",           # Primary text
    "text_muted": "#94A3B8",     # Muted / labels
    "accent": "#C8973B",         # Gold accent for headers/highlights
    "accent_hover": "#DDAE55",
    "risk_low": "#5B7A6B",       # Muted green (<40)
    "risk_medium": "#C8973B",    # Gold (40-69)
    "risk_high": "#B8562E",      # Burnt orange (70-89)
    "risk_critical": "#8B2E2E",  # Dark red (>=90)
}

CONFIDENCE_COLORS: dict[str, str] = {
    "critical": DESIGN_TOKENS["risk_critical"],
    "high": DESIGN_TOKENS["risk_high"],
    "medium": DESIGN_TOKENS["risk_medium"],
    "low": DESIGN_TOKENS["risk_low"],
}
DEFAULT_COLOR = DESIGN_TOKENS["text_muted"]


def risk_band_for_score(score: float) -> str:
    """Return risk severity band name for a 0-100 risk score."""
    s = float(score)
    if s >= 90.0:
        return "Critical"
    if s >= 70.0:
        return "High"
    if s >= 40.0:
        return "Medium"
    return "Low"


def risk_color(score_or_label: float | str | None) -> str:
    """Return hex color corresponding to a risk score or label."""
    if score_or_label is None:
        return DEFAULT_COLOR
    if isinstance(score_or_label, (int, float)):
        band = risk_band_for_score(score_or_label)
        return CONFIDENCE_COLORS.get(band.lower(), DEFAULT_COLOR)
    normalized = str(score_or_label).strip().lower()
    return CONFIDENCE_COLORS.get(normalized, DEFAULT_COLOR)


def confidence_color(label: str | None) -> str:
    """Alias for risk_color to maintain backward compatibility with tests."""
    return risk_color(label)


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

        # Check confidence label / risk band
        if normalized_labels:
            label = str(item.get("confidence_label", "")).strip().casefold()
            band = risk_band_for_score(score).casefold()
            if label not in normalized_labels and band not in normalized_labels:
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


def extract_subgraph_metrics(subgraph_data: dict[str, Any]) -> dict[str, Any]:
    """Calculate node counts, transaction flows, and IP summary for a subgraph."""
    nodes = subgraph_data.get("nodes", []) if isinstance(subgraph_data, dict) else []
    edges = subgraph_data.get("edges", []) if isinstance(subgraph_data, dict) else []

    node_types: dict[str, int] = {}
    ip_list: list[dict[str, Any]] = []
    total_inflow = 0.0
    total_outflow = 0.0
    total_fees = 0.0

    for node in nodes:
        ntype = str(node.get("type", "unknown")).lower()
        node_types[ntype] = node_types.get(ntype, 0) + 1
        if ntype == "ip":
            ip_list.append(
                {
                    "ip": node.get("id"),
                    "country": node.get("country", "Unknown"),
                    "high_risk": bool(node.get("high_risk", False)),
                }
            )
        elif ntype == "transaction":
            fee = float(node.get("fee", 0.0) or 0.0)
            total_fees += fee

    for edge in edges:
        amount = float(edge.get("amount", 0.0) or 0.0)
        etype = str(edge.get("type", "")).upper()
        if "INPUT" in etype:
            total_inflow += amount
        elif "OUTPUT" in etype:
            total_outflow += amount

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": node_types,
        "wallet_count": node_types.get("wallet", 0),
        "tx_count": node_types.get("transaction", 0),
        "ip_count": node_types.get("ip", 0),
        "ips": ip_list,
        "total_inflow_btc": round(total_inflow, 6),
        "total_outflow_btc": round(total_outflow, 6),
        "total_fees_btc": round(total_fees, 6),
    }


def compute_network_summary_stats(evidence_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute network-wide aggregate risk, pattern, and geographic statistics."""
    if not evidence_list:
        return {
            "total_wallets": 0,
            "avg_risk_score": 0.0,
            "max_risk_score": 0.0,
            "min_risk_score": 0.0,
            "total_flagged_volume_btc": 0.0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "pattern_counts": {},
            "confidence_counts": {},
            "country_counts": {},
            "high_risk_geo_count": 0,
        }

    scores = [float(item.get("final_risk_score", 0.0)) for item in evidence_list]
    pattern_counts: dict[str, int] = {}
    confidence_counts: dict[str, int] = {}
    country_counts: dict[str, int] = {}
    high_risk_geo_count = 0
    total_volume_btc = 0.0

    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0

    for item in evidence_list:
        score = float(item.get("final_risk_score", 0.0))
        if score >= 90.0:
            critical_count += 1
        elif score >= 70.0:
            high_count += 1
        elif score >= 40.0:
            medium_count += 1
        else:
            low_count += 1

        pat = str(item.get("pattern_hint", "unknown"))
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1

        conf = str(item.get("confidence_label", "Unknown"))
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

        sub = item.get("subgraph", {})
        sub_metrics = extract_subgraph_metrics(sub)
        total_volume_btc += sub_metrics["total_inflow_btc"]

        for node in sub.get("nodes", []):
            if str(node.get("type", "")).lower() == "ip":
                country = str(node.get("country", "Unknown"))
                country_counts[country] = country_counts.get(country, 0) + 1
                if node.get("high_risk"):
                    high_risk_geo_count += 1

    return {
        "total_wallets": len(evidence_list),
        "avg_risk_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
        "max_risk_score": max(scores) if scores else 0.0,
        "min_risk_score": min(scores) if scores else 0.0,
        "total_flagged_volume_btc": round(total_volume_btc, 4),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "pattern_counts": pattern_counts,
        "confidence_counts": confidence_counts,
        "country_counts": country_counts,
        "high_risk_geo_count": high_risk_geo_count,
    }


def generate_forensic_dossier_markdown(
    evidence: dict[str, Any],
    analyst_notes: str = "",
    triage_status: str = "Under Review",
) -> str:
    """Generate a formal forensic audit case dossier in Markdown format."""
    wallet_id = evidence.get("wallet_id", "Unknown")
    score = float(evidence.get("final_risk_score", 0.0))
    label = evidence.get("confidence_label", "Unknown")
    band = risk_band_for_score(score)
    reason = evidence.get("reason_sentence", "")
    pattern = evidence.get("pattern_hint", "unknown")
    shap_items = evidence.get("shap_explanation", [])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sub_metrics = extract_subgraph_metrics(evidence.get("subgraph", {}))

    md = [
        f"# 🛡️ BITCOIN FORENSICS CASE FILE",
        f"**Target Entity (Wallet ID):** `{wallet_id}`  ",
        f"**Generated:** {now}  ",
        f"**Case Status:** `{triage_status.upper()}`  ",
        f"**Risk Severity Band:** **{band.upper()} ({score:.1f} / 100)** — {label} Confidence",
        "",
        "---",
        "",
        "## 1. Executive Forensic Finding",
        f"> {reason}",
        "",
        "## 2. Behavioral Topology & Pattern Classification",
        f"- **Classified Pattern:** `{pattern}`",
        f"- **Associated Transaction Hubs:** {sub_metrics['tx_count']}",
        f"- **Associated Counterparty Wallets:** {sub_metrics['wallet_count']}",
        f"- **Broadcast IP Endpoints:** {sub_metrics['ip_count']}",
        f"- **Estimated Subgraph Volume:** {sub_metrics['total_inflow_btc']} BTC Inflow | {sub_metrics['total_outflow_btc']} BTC Outflow",
        "",
        "## 3. Explainable AI Feature Contributions (SHAP)",
        "| Feature Name | SHAP Impact | Direction | Raw Observed Value |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for item in shap_items:
        feat = item.get("feature", "unknown")
        val = item.get("shap_value", 0.0)
        direction = item.get("direction", "")
        raw = item.get("raw_value", "")
        md.append(f"| `{feat}` | {val:+.4f} | {direction} | `{raw}` |")

    md.extend(
        [
            "",
            "## 4. Associated IP Endpoints & Geolocation",
        ]
    )

    if sub_metrics["ips"]:
        md.append("| IP Address | Country | High Risk Jurisdiction |")
        md.append("| :--- | :--- | :--- |")
        for ip_data in sub_metrics["ips"]:
            hr = "🚨 YES" if ip_data["high_risk"] else "No"
            md.append(f"| `{ip_data['ip']}` | {ip_data['country']} | {hr} |")
    else:
        md.append("_No broadcast IP records associated in local neighborhood._")

    md.extend(
        [
            "",
            "## 5. Investigator Notes & Audit Trail",
            analyst_notes if analyst_notes.strip() else "_No investigator notes logged for this entity._",
            "",
            "---",
            "**Notice:** _This document is generated by the AI-Powered Bitcoin Transaction Monitoring & Forensics Pipeline for investigative and compliance evaluation purposes._",
        ]
    )

    return "\n".join(md)
