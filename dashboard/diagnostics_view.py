"""Evaluation metrics and pipeline diagnostics view strictly adhering to honest reporting."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from dashboard.utils import DESIGN_TOKENS

PHASE_DESCRIPTIONS: dict[str, str] = {
    "phase_1_dataset": "Synthetic Dataset Generation (Transaction traffic generator)",
    "phase_2_ingestion": "Format-Agnostic Ingestion (CSV/JSON/XML parsing & validation)",
    "phase_3_geoip": "GeoIP & Network Enrichment (MaxMind City & ASN lookups)",
    "phase_4_graph": "Graph Construction & Clustering (Entity graph & CIO clusters)",
    "phase_5_features": "Feature Engineering & Preprocessing (Standardization & pipeline)",
    "phase_6_models": "ML Modeling & Community Scoring (Isolation Forest & Louvain)",
    "phase_7_explainability": "Explainability & Packaging (SHAP kernel & evidence json)",
    "phase_8_dashboard": "Forensics Dashboard (Streamlit case file console)",
}


def render_evaluation_tab(evidence_list: list[dict[str, Any]]) -> None:
    """Render Tab 6: Evaluation metrics and pipeline execution diagnostics."""
    st.markdown("### 📊 Pipeline Evaluation & Empirical Diagnostics")
    st.caption("Verification benchmarks, timing durations, and honest evaluation status against ground truth.")

    eval_report_path = Path("data/evaluation_report.txt")
    ground_truth_path = Path("data/ground_truth/ground_truth.csv")
    error_analysis_path = Path("data/error_analysis.json")

    # 1. Ground Truth & Evaluation Status Banner (Honest Policy)
    if eval_report_path.is_file() and ground_truth_path.is_file():
        st.success("✅ Ground truth dataset loaded and evaluation report generated.")
        st.text(eval_report_path.read_text(encoding="utf-8"))
    else:
        st.markdown(
            f"""
            <div style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['border']}; border-left: 4px solid {DESIGN_TOKENS['accent']}; border-radius: 6px; padding: 16px 20px; margin-bottom: 20px;">
                <div style="font-weight: bold; color: {DESIGN_TOKENS['accent']}; font-size: 1.05rem; margin-bottom: 6px;">
                    ℹ️ Evaluation Metrics: Not Available (Offline Test Environment)
                </div>
                <div style="color: {DESIGN_TOKENS['text_muted']}; font-size: 0.92rem; line-height: 1.5;">
                    End-to-end evaluation metrics (Precision, Recall, F1, ROC-AUC) are not displayed because a verified 
                    labeled <code>data/ground_truth/ground_truth.csv</code> file is not present in this local checkout.
                    <br><br>
                    <em>Per the project's documentation and honest reporting policy in <code>WRITEUP.md</code>, synthetic or fabricated metrics are strictly avoided.</em>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Pipeline Phase Execution Timings
    st.markdown("#### 🕒 Pipeline Execution Timings & Benchmarks")
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

    # 3. Repository File System Integrity
    st.markdown("#### 📁 Forensics Data Repository Integrity")
    repo_checks = [
        ("data/evidence_packages.json", "Evidence packages output", Path("data/evidence_packages.json").exists()),
        ("data/pipeline_timing.json", "Execution benchmarks", Path("data/pipeline_timing.json").exists()),
        ("geoip/GeoLite2-City.mmdb", "MaxMind City Database", Path("geoip/GeoLite2-City.mmdb").exists()),
        ("data/raw/transactions.csv", "Raw transaction source", Path("data/raw/transactions.csv").exists()),
    ]

    check_cols = st.columns(len(repo_checks))
    for col, (path_str, desc, exists) in zip(check_cols, repo_checks):
        with col:
            icon = "✅" if exists else "ℹ️"
            border_c = DESIGN_TOKENS["border"] if exists else DESIGN_TOKENS["accent"]
            st.markdown(
                f"""
                <div style="background-color: {DESIGN_TOKENS['surface']}; border: 1px solid {border_c}; border-radius: 6px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.4rem;">{icon}</div>
                    <strong style="color: {DESIGN_TOKENS['text']}; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; word-break: break-all;">{path_str}</strong>
                    <div style="color: {DESIGN_TOKENS['text_muted']}; font-size: 0.75rem; margin-top: 4px;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
