"""Case Detail view component for deep-dive forensic inspection of a selected wallet entity."""

from __future__ import annotations

import json
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dashboard.utils import (
    DESIGN_TOKENS,
    extract_subgraph_metrics,
    generate_forensic_dossier_markdown,
    risk_band_for_score,
    risk_color,
)

PATTERN_EXPLANATIONS: dict[str, str] = {
    "peeling_chain": "Peeling chain: repeated small-output splits from a single source — a classic layering/structuring signature.",
    "fan_in_fan_out": "Fan-in / Fan-out: many inputs consolidate into one wallet then quickly disperse to multiple destinations — typical mixing behavior.",
    "rapid_cashout": "Rapid cashout: high transaction velocity, burst activity, or high fee ratios consistent with urgent fund extraction.",
    "shared_ip_cluster": "Shared IP cluster: multiple wallets transacting from the same broadcast IP address or rapid geographic hopping.",
    "unknown": "Anomalous pattern: composite behavioral outlier across transaction, temporal, and graph structural metrics.",
}

PATTERN_RECOMMENDATIONS: dict[str, str] = {
    "peeling_chain": "Track downstream peel hops to identify intermediate liquidity consolidation or exchange deposit addresses.",
    "fan_in_fan_out": "Cluster ingress funding wallets to check for common ownership or darknet market payment aggregators.",
    "rapid_cashout": "Check destination addresses against known OTC desks, high-risk VASP deposit endpoints, or bridge protocols.",
    "shared_ip_cluster": "Correlate broadcast timestamp windows with VPN/proxy exit nodes and geographic hop latency.",
    "unknown": "Perform comprehensive multi-hop graph expansion and evaluate counterparty exposure ratios.",
}


def render_case_detail_tab(evidence_list: list[dict[str, Any]]) -> None:
    """Render Tab 3: Case Detail view for inspecting flagged entities."""
    if not evidence_list:
        st.info("No evidence records available.")
        return

    wallet_options = [str(item.get("wallet_id", "")) for item in evidence_list]
    selected_wallet_id = st.selectbox(
        "🔍 Select Wallet Entity for Case Inspection",
        options=wallet_options,
        index=0,
        help="Select a wallet to load its full forensic dossier, SHAP breakdown, and network neighborhood.",
    )

    selected_evidence = next((item for item in evidence_list if item.get("wallet_id") == selected_wallet_id), evidence_list[0])
    render_wallet_detail(selected_evidence)


def render_wallet_detail(evidence: dict[str, Any]) -> None:
    """Render the forensic detail view for a single flagged wallet entity."""
    if not evidence:
        st.info("No evidence data provided.")
        return

    wallet_id = str(evidence.get("wallet_id", "Unknown"))
    score = float(evidence.get("final_risk_score", 0.0))
    label = str(evidence.get("confidence_label", "Unknown"))
    band = risk_band_for_score(score)
    reason = str(evidence.get("reason_sentence", "No reason provided."))
    pattern = str(evidence.get("pattern_hint", "unknown"))
    shap_items = evidence.get("shap_explanation", [])

    badge_color = risk_color(score)
    sub_metrics = extract_subgraph_metrics(evidence.get("subgraph", {}))

    # Header Case File Card
    stamp_html = ""
    if score >= 90.0:
        stamp_html = f"""
        <div style="display: inline-block; border: 2px solid {DESIGN_TOKENS['risk_critical']}; color: {DESIGN_TOKENS['risk_critical']}; padding: 3px 10px; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; border-radius: 4px; transform: rotate(-3deg); margin-top: 6px;">
            ★ CRITICAL SEVERITY
        </div>
        """

    st.markdown(
        f"""
        <div style="background-color: {DESIGN_TOKENS['surface']}; border: 1px solid {DESIGN_TOKENS['border']}; border-left: 5px solid {badge_color}; border-radius: 8px; padding: 18px 20px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; color: {DESIGN_TOKENS['text_muted']};">Target Entity Case File</span>
                    <h2 style="margin: 4px 0 6px 0; color: {DESIGN_TOKENS['text']}; font-family: 'Source Serif 4', Georgia, serif; font-size: 1.4rem; word-break: break-all;">{wallet_id}</h2>
                    <span style="display: inline-block; background-color: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}; border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600;">
                        {band.upper()} RISK ({label} CONFIDENCE)
                    </span>
                </div>
                <div style="text-align: right; min-width: 150px;">
                    <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: {DESIGN_TOKENS['text_muted']};">Composite Risk Score</div>
                    <div style="font-size: 2.2rem; font-weight: 800; font-family: 'IBM Plex Mono', Courier, monospace; color: {badge_color}; line-height: 1.1;">
                        {score:.1f} <span style="font-size: 1rem; color: {DESIGN_TOKENS['text_muted']};">/ 100</span>
                    </div>
                    {stamp_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sub-network Volume Summary Metrics
    v1, v2, v3, v4 = st.columns(4)
    with v1:
        _render_sub_metric("Est. Inflow", f"{sub_metrics['total_inflow_btc']:.4f} BTC")
    with v2:
        _render_sub_metric("Est. Outflow", f"{sub_metrics['total_outflow_btc']:.4f} BTC")
    with v3:
        _render_sub_metric("Tx Hubs", str(sub_metrics["tx_count"]))
    with v4:
        _render_sub_metric("Linked IPs", str(sub_metrics["ip_count"]))

    st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

    # Prominent Human-Readable Reason Sentence (Centerpiece)
    st.markdown("#### 📝 Forensic Investigation Finding")
    st.markdown(
        f"""
        <div style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['border']}; border-left: 4px solid {badge_color}; border-radius: 6px; padding: 16px 18px; margin-bottom: 16px;">
            <p style="margin: 0; color: {DESIGN_TOKENS['text']}; font-size: 1.02rem; line-height: 1.55; font-weight: 500;">
                {reason}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Pattern Hint Analysis & Actionable Recommendation
    pattern_explanation = PATTERN_EXPLANATIONS.get(
        pattern.casefold(),
        f"Pattern signature: {pattern.replace('_', ' ').capitalize()}"
    )
    pattern_rec = PATTERN_RECOMMENDATIONS.get(
        pattern.casefold(),
        "Evaluate multi-hop counterparty transaction flows."
    )

    st.markdown("#### 🔎 Behavioral Topology & Recommended Action")
    st.markdown(
        f"""
        <div style="background-color: {DESIGN_TOKENS['surface']}; border: 1px solid {DESIGN_TOKENS['border']}; border-radius: 6px; padding: 14px 16px; margin-bottom: 18px;">
            <div style="margin-bottom: 8px;">
                <span style="background-color: {DESIGN_TOKENS['surface_raised']}; color: {DESIGN_TOKENS['accent']}; border: 1px solid {DESIGN_TOKENS['accent']}; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; margin-right: 8px;">
                    {pattern}
                </span>
                <span style="color: {DESIGN_TOKENS['text']}; font-size: 0.95rem;">
                    {pattern_explanation}
                </span>
            </div>
            <div style="color: {DESIGN_TOKENS['accent_hover']}; font-size: 0.88rem; border-top: 1px solid {DESIGN_TOKENS['border']}; padding-top: 8px; margin-top: 8px;">
                💡 <strong>Investigator Next Step:</strong> {pattern_rec}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SHAP Feature Contribution Chart & Structured Table
    st.markdown("#### 📊 Model Feature Attributions (SHAP)")
    if shap_items:
        _render_shap_chart(shap_items)
        _render_shap_table(shap_items)
    else:
        st.info("No feature explanation breakdown available for this record.")

    st.markdown("---")

    # Investigator Triage Action Bar & Case Dossier Export
    st.markdown("#### 🛠️ Case Triage Actions & Export")

    note_key = f"notes_{wallet_id}"
    status_key = f"status_{wallet_id}"

    col_status, col_notes = st.columns([1, 2])
    with col_status:
        triage_status = st.selectbox(
            "Case Triage Status",
            options=["Under Review", "Confirmed Suspicious", "Cleared / False Positive", "Escalated to Compliance"],
            key=status_key,
        )
    with col_notes:
        analyst_notes = st.text_input(
            "Analyst Investigation Notes",
            value=st.session_state.get(note_key, ""),
            placeholder="Log observations, subpoena notes, or compliance tags...",
            key=note_key,
        )

    dossier_md = generate_forensic_dossier_markdown(
        evidence=evidence,
        analyst_notes=analyst_notes,
        triage_status=triage_status,
    )

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.download_button(
            label="📥 Export Forensic Dossier (.md)",
            data=dossier_md,
            file_name=f"case_dossier_{wallet_id[:10]}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with btn_col2:
        st.download_button(
            label="📦 Export Case Evidence (.json)",
            data=json.dumps(evidence, indent=2),
            file_name=f"evidence_{wallet_id[:10]}.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_sub_metric(label: str, value: str) -> None:
    """Render a small sub-network metric card."""
    st.markdown(
        f"""
        <div style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['border']}; border-radius: 4px; padding: 8px 12px;">
            <div style="font-size: 0.72rem; color: {DESIGN_TOKENS['text_muted']}; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
            <div style="font-size: 1.15rem; font-weight: bold; font-family: 'IBM Plex Mono', Courier, monospace; color: {DESIGN_TOKENS['text']};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_shap_chart(shap_items: list[dict[str, Any]]) -> None:
    """Render a horizontal bar chart of SHAP values colored by directional impact without label overlap."""
    feature_names = []
    values = []
    colors = []

    for item in shap_items:
        feat = str(item.get("feature", "unknown"))
        val = float(item.get("shap_value", 0.0))
        direction = str(item.get("direction", ""))

        feature_names.append(feat)
        values.append(val)
        if direction == "increases_risk" or val > 0:
            colors.append(DESIGN_TOKENS["risk_high"])
        else:
            colors.append(DESIGN_TOKENS["risk_low"])

    fig, ax = plt.subplots(figsize=(6.8, max(2.6, len(feature_names) * 0.75)))
    fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
    ax.set_facecolor(DESIGN_TOKENS["surface"])

    y_pos = range(len(feature_names))
    bars = ax.barh(y_pos, values, color=colors, height=0.52, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(feature_names, color=DESIGN_TOKENS["text"], fontsize=9.5, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlabel("SHAP Impact on Anomaly Score", color=DESIGN_TOKENS["text_muted"], fontsize=9)
    ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5)
    ax.grid(axis="x", linestyle="--", alpha=0.25, color=DESIGN_TOKENS["border"])
    ax.axvline(0, color=DESIGN_TOKENS["text_muted"], linestyle="--", linewidth=0.8, alpha=0.6)
    for spine in ax.spines.values():
        spine.set_color(DESIGN_TOKENS["border"])

    min_val = min(0.0, min(values)) if values else 0.0
    max_val = max(0.0, max(values)) if values else 0.0
    span = max(0.08, max_val - min_val)
    ax.set_xlim(min_val - span * 0.22, max_val + span * 0.22)

    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        if abs(val) >= 0.12:
            ax.text(
                x_pos / 2,
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}",
                va="center",
                ha="center",
                color="#FFFFFF",
                fontsize=8.5,
                fontweight="bold",
                fontfamily="monospace",
            )
        else:
            ha = "left" if val >= 0 else "right"
            offset = span * 0.025 if val >= 0 else -span * 0.025
            ax.text(
                x_pos + offset,
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.2f}",
                va="center",
                ha=ha,
                color=DESIGN_TOKENS["text"],
                fontsize=8.5,
                fontweight="bold",
                fontfamily="monospace",
            )

    red_patch = plt.Line2D([0], [0], color=DESIGN_TOKENS["risk_high"], lw=4, label="Increases Risk")
    green_patch = plt.Line2D([0], [0], color=DESIGN_TOKENS["risk_low"], lw=4, label="Decreases Risk")
    ax.legend(
        handles=[red_patch, green_patch],
        loc="lower right",
        framealpha=0.4,
        facecolor=DESIGN_TOKENS["surface_raised"],
        edgecolor=DESIGN_TOKENS["border"],
        labelcolor=DESIGN_TOKENS["text"],
        fontsize=8,
    )

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _render_shap_table(shap_items: list[dict[str, Any]]) -> None:
    """Render a structured feature contribution breakdown table."""
    rows = []
    for item in shap_items:
        feat = str(item.get("feature", "unknown"))
        val = float(item.get("shap_value", 0.0))
        direction = str(item.get("direction", ""))
        raw = item.get("raw_value")

        raw_str = f"{raw:.2f}" if isinstance(raw, float) else str(raw) if raw is not None else "N/A"
        dir_display = "🚨 Increases Risk" if direction == "increases_risk" or val > 0 else "🟢 Decreases Risk"

        rows.append(
            {
                "Feature Name": feat,
                "Observed Raw Value": raw_str,
                "Risk Contribution": dir_display,
                "SHAP Impact": f"{val:+.4f}",
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
