"""Detail view component for inspecting a selected flagged wallet."""

from __future__ import annotations

import json
from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from dashboard.utils import (
    confidence_color,
    extract_subgraph_metrics,
    generate_forensic_dossier_markdown,
)

# Human-readable explanations for common forensic patterns
PATTERN_EXPLANATIONS: dict[str, str] = {
    "peeling_chain": "Peeling chain: repeated small-output splits from a single source — a classic layering/structuring signature.",
    "fan_in_fan_out": "Fan-in / Fan-out: many inputs consolidate into one wallet then quickly disperse to multiple destinations — typical mixing behavior.",
    "rapid_cashout": "Rapid cashout: high transaction velocity, burst activity, or high fee ratios consistent with urgent fund extraction.",
    "shared_ip_cluster": "Shared IP cluster: multiple wallets transacting from the same broadcast IP address or rapid geographic hopping.",
    "unknown": "Anomalous pattern: composite behavioral outlier across transaction, temporal, and graph structural metrics.",
}

PATTERN_RECOMMENDATIONS: dict[str, str] = {
    "peeling_chain": "Recommend tracking downstream peel hops to identify intermediate liquidity consolidation or exchange deposit addresses.",
    "fan_in_fan_out": "Recommend clustering ingress funding wallets to check for common ownership or darknet market payment aggregators.",
    "rapid_cashout": "Recommend checking destination addresses against known OTC desks, high-risk VASP deposit endpoints, or bridge protocols.",
    "shared_ip_cluster": "Recommend correlating broadcast timestamp windows with VPN/proxy exit nodes and geographic hop latency.",
    "unknown": "Recommend comprehensive multi-hop graph expansion and evaluating counterparty exposure ratios.",
}


def render_wallet_detail(evidence: dict[str, Any]) -> None:
    """Render the forensic detail view for a single flagged wallet."""
    if not evidence:
        st.info("Select a wallet from the alert table to inspect its evidence.")
        return

    wallet_id = str(evidence.get("wallet_id", "Unknown"))
    score = float(evidence.get("final_risk_score", 0.0))
    label = str(evidence.get("confidence_label", "Unknown"))
    reason = str(evidence.get("reason_sentence", "No reason provided."))
    pattern = str(evidence.get("pattern_hint", "unknown"))
    shap_items = evidence.get("shap_explanation", [])

    badge_color = confidence_color(label)
    sub_metrics = extract_subgraph_metrics(evidence.get("subgraph", {}))

    # Header Card with Score & Badge
    st.markdown(
        f"""
        <div style="background-color: #1A202C; border: 1px solid #2D3748; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.85rem; color: #A0AEC0; text-transform: uppercase; letter-spacing: 0.05em;">Target Wallet Entity</span>
                    <h3 style="margin: 2px 0 0 0; color: #F7FAFC; word-break: break-all;">{wallet_id}</h3>
                </div>
                <div style="text-align: right; min-width: 140px;">
                    <span style="font-size: 0.85rem; color: #A0AEC0; text-transform: uppercase; letter-spacing: 0.05em;">Risk Score</span>
                    <div style="font-size: 1.8rem; font-weight: bold; color: {badge_color}; line-height: 1.2;">
                        {score:.1f} <span style="font-size: 1rem; color: #718096;">/ 100</span>
                    </div>
                    <span style="display: inline-block; background-color: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}; border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; font-weight: 600; margin-top: 4px;">
                        {label.upper()} CONFIDENCE
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sub-network Value Summary Metrics
    v_col1, v_col2, v_col3, v_col4 = st.columns(4)
    v_col1.metric("Est. Inflow", f"{sub_metrics['total_inflow_btc']:.2f} BTC")
    v_col2.metric("Est. Outflow", f"{sub_metrics['total_outflow_btc']:.2f} BTC")
    v_col3.metric("Tx Hubs", sub_metrics["tx_count"])
    v_col4.metric("Linked IPs", sub_metrics["ip_count"])

    # Prominent Human-Readable Reason Sentence (Centerpiece)
    st.markdown("#### 📝 Forensic Finding")
    st.markdown(
        f"""
        <div style="background-color: #2D3748; border-left: 4px solid {badge_color}; border-radius: 4px; padding: 14px 16px; margin-bottom: 16px;">
            <p style="margin: 0; color: #EDF2F7; font-size: 1.05rem; line-height: 1.5; font-weight: 500;">
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

    st.markdown("#### 🔎 Behavioral Pattern & Forensic Guidance")
    st.markdown(
        f"""
        <div style="background-color: #1A202C; border: 1px solid #2D3748; border-radius: 6px; padding: 12px 14px; margin-bottom: 16px;">
            <div style="margin-bottom: 6px;">
                <span style="background-color: #4A5568; color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; margin-right: 8px;">
                    {pattern}
                </span>
                <span style="color: #CBD5E0; font-size: 0.95rem;">
                    {pattern_explanation}
                </span>
            </div>
            <div style="color: #90CDF4; font-size: 0.88rem; font-style: italic; border-top: 1px solid #2D3748; padding-top: 6px; margin-top: 6px;">
                💡 <strong>Investigator Next Step:</strong> {pattern_rec}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # SHAP Feature Contribution Chart
    st.markdown("#### 📊 Model Feature Contributions (SHAP)")
    if shap_items:
        _render_shap_chart(shap_items)
    else:
        st.info("No feature explanation breakdown available for this record.")

    st.markdown("---")

    # Investigator Triage Action Bar & Case Dossier Export
    st.markdown("#### 🛠️ Case Triage & Forensic Dossier Export")

    # Session state for analyst notes
    note_key = f"notes_{wallet_id}"
    status_key = f"status_{wallet_id}"

    col_status, col_notes = st.columns([1, 2])
    with col_status:
        triage_status = st.selectbox(
            "Triage Status",
            options=["Under Review", "Confirmed Suspicious", "Cleared / False Positive", "Escalated to Compliance"],
            key=status_key,
        )
    with col_notes:
        analyst_notes = st.text_input(
            "Analyst Case Notes",
            value=st.session_state.get(note_key, ""),
            placeholder="Add case observations or law-enforcement notes...",
            key=note_key,
        )

    # Generate Dossier content
    dossier_md = generate_forensic_dossier_markdown(
        evidence=evidence,
        analyst_notes=analyst_notes,
        triage_status=triage_status,
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button(
            label="📥 Download Audit Dossier (.md)",
            data=dossier_md,
            file_name=f"case_dossier_{wallet_id[:10]}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_btn2:
        st.download_button(
            label="📦 Export Case Evidence (.json)",
            data=json.dumps(evidence, indent=2),
            file_name=f"evidence_{wallet_id[:10]}.json",
            mime="application/json",
            use_container_width=True,
        )


def _render_shap_chart(shap_items: list[dict[str, Any]]) -> None:
    """Render a horizontal bar chart of SHAP values colored by directional impact without label overlap."""
    feature_labels = []
    values = []
    colors = []

    for item in shap_items:
        feat = str(item.get("feature", "unknown"))
        val = float(item.get("shap_value", 0.0))
        direction = str(item.get("direction", ""))
        raw = item.get("raw_value")

        raw_str = f"{raw:.2f}" if isinstance(raw, float) else str(raw) if raw is not None else ""
        label = f"{feat} (raw: {raw_str})" if raw_str else feat

        feature_labels.append(label)
        values.append(val)
        if direction == "increases_risk" or val > 0:
            colors.append("#E53E3E")
        else:
            colors.append("#38A169")

    fig, ax = plt.subplots(figsize=(6.5, max(2.6, len(feature_labels) * 0.75)))
    fig.patch.set_facecolor("#1A202C")
    ax.set_facecolor("#1A202C")

    y_pos = range(len(feature_labels))
    bars = ax.barh(y_pos, values, color=colors, height=0.5, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(feature_labels, color="#E2E8F0", fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("SHAP Impact on Anomaly Score", color="#A0AEC0", fontsize=9)
    ax.tick_params(colors="#A0AEC0", labelsize=8.5)
    ax.grid(axis="x", linestyle="--", alpha=0.25, color="#4A5568")
    ax.axvline(0, color="#718096", linestyle="--", linewidth=0.8, alpha=0.6)

    # Dynamic xlim to guarantee labels never clip or overlap axes
    min_val = min(values) if values else 0.0
    max_val = max(values) if values else 0.0
    span = max(0.08, max_val - min_val)
    ax.set_xlim(min(0.0, min_val) - span * 0.28, max(0.0, max_val) + span * 0.28)

    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        offset = span * 0.03 if x_pos >= 0 else -span * 0.03
        ha = "left" if x_pos >= 0 else "right"
        ax.text(
            x_pos + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.2f}",
            va="center",
            ha=ha,
            color="#CBD5E0",
            fontsize=8.5,
            fontweight="bold",
        )

    red_patch = plt.Line2D([0], [0], color="#E53E3E", lw=4, label="Increases Risk")
    green_patch = plt.Line2D([0], [0], color="#38A169", lw=4, label="Decreases Risk")
    ax.legend(
        handles=[red_patch, green_patch],
        loc="lower right",
        framealpha=0.35,
        facecolor="#2D3748",
        edgecolor="#4A5568",
        labelcolor="#E2E8F0",
        fontsize=8,
    )

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
