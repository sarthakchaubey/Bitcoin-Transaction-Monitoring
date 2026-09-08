"""Pipeline diagnostics, phase execution benchmarks, and system health view."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PHASE_DESCRIPTIONS: dict[str, str] = {
    "phase_1_dataset": "Synthetic Dataset Generation (Transaction traffic generator)",
    "phase_2_ingestion": "Format-Agnostic Ingestion (CSV/JSON/XML parsing & validation)",
    "phase_3_geoip": "GeoIP & Network Enrichment (MaxMind City & ASN lookups)",
    "phase_4_graph": "Graph Construction & Clustering (Entity graph & CIO clusters)",
    "phase_5_features": "Feature Engineering & Preprocessing (Standardization & pipeline)",
    "phase_6_models": "ML Modeling & Community Scoring (Isolation Forest & Louvain)",
    "phase_7_explainability": "Explainability & Packaging (SHAP kernel & evidence json)",
    "phase_8_dashboard": "Forensics Dashboard (Streamlit interactive console)",
}


def render_diagnostics_view(evidence_list: list[dict[str, Any]]) -> None:
    """Render pipeline health metrics, phase timing durations, and system telemetry."""
    st.markdown("### ⏱️ Pipeline Health & Diagnostics")
    st.caption("Execution benchmarks, phase timing breakdown, and offline environment telemetry.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Evidence Packages", len(evidence_list))
    col2.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    col3.metric("System Mode", "Offline Forensics")

    st.markdown("---")

    # Pipeline Phase Timings
    st.markdown("#### 🕒 Pipeline Execution Timings")
    timing_path = Path("data/pipeline_timing.json")
    timing_data: dict[str, Any] = {}

    if timing_path.is_file():
        try:
            timing_data = json.loads(timing_path.read_text(encoding="utf-8"))
        except Exception:
            timing_data = {}

    timing_rows = []
    for phase_key, desc in PHASE_DESCRIPTIONS.items():
        phase_info = timing_data.get(phase_key, {})
        duration_sec = phase_info.get("seconds")
        status = phase_info.get("status", "completed" if evidence_list else "ready")
        err = phase_info.get("error", "")

        status_display = "✅ OK" if status in ("ok", "completed") else "⚠️ " + status.upper()
        duration_str = f"{duration_sec:.4f}s" if duration_sec is not None else "Cached / Ready"

        timing_rows.append(
            {
                "Pipeline Phase": phase_key.replace("_", " ").upper(),
                "Description": desc,
                "Status": status_display,
                "Execution Duration": duration_str,
                "Diagnostic Notes": err if err else "Operational",
            }
        )

    st.dataframe(pd.DataFrame(timing_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Forensics File System Health
    st.markdown("#### 📁 Forensics Data Repository Integrity")
    repo_checks = [
        ("data/evidence_packages.json", "Forensics evidence packages output", Path("data/evidence_packages.json").exists()),
        ("data/pipeline_timing.json", "Pipeline execution benchmark records", Path("data/pipeline_timing.json").exists()),
        ("geoip/GeoLite2-City.mmdb", "Offline MaxMind City Database", Path("geoip/GeoLite2-City.mmdb").exists()),
        ("data/raw/transactions.csv", "Raw transaction ingestion source", Path("data/raw/transactions.csv").exists()),
    ]

    check_cols = st.columns(len(repo_checks))
    for col, (path_str, desc, exists) in zip(check_cols, repo_checks):
        with col:
            icon = "✅" if exists else "ℹ️"
            st.markdown(
                f"""
                <div style="background-color: #1A202C; border: 1px solid #2D3748; border-radius: 6px; padding: 10px; text-align: center;">
                    <div style="font-size: 1.3rem;">{icon}</div>
                    <strong style="color: #E2E8F0; font-size: 0.85rem; word-break: break-all;">{path_str}</strong>
                    <div style="color: #A0AEC0; font-size: 0.75rem; margin-top: 4px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
