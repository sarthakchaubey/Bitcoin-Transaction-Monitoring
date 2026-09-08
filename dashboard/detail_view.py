"""Detail view component for inspecting a selected flagged wallet."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from dashboard.utils import confidence_color

# Human-readable explanations for common forensic patterns
PATTERN_EXPLANATIONS: dict[str, str] = {
    "peeling_chain": "Peeling chain: repeated small-output splits from a single source — a classic layering/structuring signature.",
    "fan_in_fan_out": "Fan-in / Fan-out: many inputs consolidate into one wallet then quickly disperse to multiple destinations — typical mixing behavior.",
    "rapid_cashout": "Rapid cashout: high transaction velocity, burst activity, or high fee ratios consistent with urgent fund extraction.",
    "shared_ip_cluster": "Shared IP cluster: multiple wallets transacting from the same broadcast IP address or rapid geographic hopping.",
    "unknown": "Anomalous pattern: composite behavioral outlier across transaction, temporal, and graph structural metrics.",
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

    # Header Card with Score & Badge
    st.markdown(
        f"""
        <div style="background-color: #1A202C; border: 1px solid #2D3748; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.85rem; color: #A0AEC0; text-transform: uppercase; letter-spacing: 0.05em;">Wallet ID</span>
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

    # Pattern Hint Analysis
    pattern_explanation = PATTERN_EXPLANATIONS.get(
        pattern.casefold(),
        f"Pattern signature: {pattern.replace('_', ' ').capitalize()}"
    )
    st.markdown("#### 🔎 Behavioral Pattern")
    st.markdown(
        f"""
        <div style="background-color: #1A202C; border: 1px solid #2D3748; border-radius: 6px; padding: 10px 14px; margin-bottom: 16px;">
            <span style="background-color: #4A5568; color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; margin-right: 8px;">
                {pattern}
            </span>
            <span style="color: #CBD5E0; font-size: 0.95rem;">
                {pattern_explanation}
            </span>
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


def _render_shap_chart(shap_items: list[dict[str, Any]]) -> None:
    """Render a horizontal bar chart of SHAP values colored by directional impact."""
    # Sort items by absolute shap value or by order
    features = []
    values = []
    colors = []
    raw_labels = []

    for item in shap_items:
        feat = str(item.get("feature", "unknown"))
        val = float(item.get("shap_value", 0.0))
        direction = str(item.get("direction", ""))
        raw = item.get("raw_value")

        features.append(feat)
        values.append(val)
        # Red increases risk, Green decreases risk
        if direction == "increases_risk" or val > 0:
            colors.append("#E53E3E")
        else:
            colors.append("#38A169")

        raw_str = f"{raw:.2f}" if isinstance(raw, float) else str(raw) if raw is not None else ""
        raw_labels.append(f"raw: {raw_str}" if raw_str else "")

    # Create matplotlib horizontal bar chart
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(features) * 0.7)))
    fig.patch.set_facecolor("#1A202C")
    ax.set_facecolor("#1A202C")

    y_pos = range(len(features))
    bars = ax.barh(y_pos, values, color=colors, height=0.55, edgecolor="none")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(features, color="#E2E8F0", fontsize=10)
    ax.invert_yaxis()  # Highest ranked at the top
    ax.set_xlabel("SHAP Impact on Anomaly Score", color="#A0AEC0", fontsize=9)
    ax.tick_params(colors="#A0AEC0", labelsize=9)
    ax.grid(axis="x", linestyle="--", alpha=0.3, color="#4A5568")

    # Annotate bars with raw value labels
    for bar, raw_text, val in zip(bars, raw_labels, values):
        x_pos = bar.get_width()
        offset = 0.01 if x_pos >= 0 else -0.01
        ha = "left" if x_pos >= 0 else "right"
        if raw_text:
            ax.text(
                x_pos + offset,
                bar.get_y() + bar.get_height() / 2,
                f" {raw_text}",
                va="center",
                ha=ha,
                color="#CBD5E0",
                fontsize=8.5,
            )

    # Custom legend
    red_patch = plt.Line2D([0], [0], color="#E53E3E", lw=4, label="Increases Risk")
    green_patch = plt.Line2D([0], [0], color="#38A169", lw=4, label="Decreases Risk")
    ax.legend(
        handles=[red_patch, green_patch],
        loc="lower right",
        framealpha=0.3,
        facecolor="#2D3748",
        edgecolor="#4A5568",
        labelcolor="#E2E8F0",
        fontsize=8,
    )

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
