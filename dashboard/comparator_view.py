"""Side-by-side comparative analysis view for multiple wallet entities."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dashboard.utils import confidence_color, extract_subgraph_metrics


def render_comparator_view(evidence_list: list[dict[str, Any]]) -> None:
    """Render side-by-side comparison between two selected wallet entities."""
    if len(evidence_list) < 2:
        st.info("At least two wallet entities are required for comparative analysis.")
        return

    st.markdown("### ⚖️ Multi-Entity Comparative Forensics")
    st.caption("Perform direct side-by-side behavioral, feature-level, and network overlap comparisons between two entities.")

    wallet_options = [str(item.get("wallet_id", "")) for item in evidence_list]

    col_select_a, col_select_b = st.columns(2)
    with col_select_a:
        wallet_a_id = st.selectbox("Select Primary Entity (Entity A)", wallet_options, index=0)
    with col_select_b:
        wallet_b_id = st.selectbox(
            "Select Comparison Entity (Entity B)",
            wallet_options,
            index=1 if len(wallet_options) > 1 else 0,
        )

    entity_a = next((item for item in evidence_list if item.get("wallet_id") == wallet_a_id), None)
    entity_b = next((item for item in evidence_list if item.get("wallet_id") == wallet_b_id), None)

    if not entity_a or not entity_b:
        st.warning("Could not resolve selected entity records.")
        return

    st.markdown("---")

    # Side-by-side Entity Headers
    col_card_a, col_card_b = st.columns(2)

    with col_card_a:
        _render_entity_summary_card(entity_a, "Entity A")

    with col_card_b:
        _render_entity_summary_card(entity_b, "Entity B")

    st.markdown("---")

    # Metrics & Sub-network Topology Comparison Table
    st.markdown("#### 📐 Network Topology & Volume Comparison")
    metrics_a = extract_subgraph_metrics(entity_a.get("subgraph", {}))
    metrics_b = extract_subgraph_metrics(entity_b.get("subgraph", {}))

    comparison_data = {
        "Metric Dimension": [
            "Assigned Risk Score",
            "Confidence Level",
            "Behavioral Pattern Hint",
            "Local Graph Nodes",
            "Transaction Hubs",
            "Counterparty Wallets",
            "Broadcast IPs",
            "Estimated Inflow (BTC)",
            "Estimated Outflow (BTC)",
        ],
        f"Entity A ({wallet_a_id[:12]}...)": [
            f"{entity_a.get('final_risk_score', 0):.1f} / 100",
            str(entity_a.get("confidence_label", "Unknown")),
            str(entity_a.get("pattern_hint", "unknown")),
            str(metrics_a["total_nodes"]),
            str(metrics_a["tx_count"]),
            str(metrics_a["wallet_count"]),
            str(metrics_a["ip_count"]),
            f"{metrics_a['total_inflow_btc']:.4f} BTC",
            f"{metrics_a['total_outflow_btc']:.4f} BTC",
        ],
        f"Entity B ({wallet_b_id[:12]}...)": [
            f"{entity_b.get('final_risk_score', 0):.1f} / 100",
            str(entity_b.get("confidence_label", "Unknown")),
            str(entity_b.get("pattern_hint", "unknown")),
            str(metrics_b["total_nodes"]),
            str(metrics_b["tx_count"]),
            str(metrics_b["wallet_count"]),
            str(metrics_b["ip_count"]),
            f"{metrics_b['total_inflow_btc']:.4f} BTC",
            f"{metrics_b['total_outflow_btc']:.4f} BTC",
        ],
    }

    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Overlap Analysis (Shared IPs / Shared Counterparties)
    st.markdown("#### 🔗 Entity Overlap & Co-Occurrence Analysis")
    ips_a = {ip["ip"] for ip in metrics_a["ips"] if ip.get("ip")}
    ips_b = {ip["ip"] for ip in metrics_b["ips"] if ip.get("ip")}
    shared_ips = ips_a.intersection(ips_b)

    nodes_a = {n["id"] for n in entity_a.get("subgraph", {}).get("nodes", [])}
    nodes_b = {n["id"] for n in entity_b.get("subgraph", {}).get("nodes", [])}
    shared_nodes = nodes_a.intersection(nodes_b) - {wallet_a_id, wallet_b_id}

    col_ov1, col_ov2 = st.columns(2)
    with col_ov1:
        if shared_ips:
            st.error(f"🚨 **Shared Broadcast IPs Detected ({len(shared_ips)}):** {', '.join(shared_ips)}")
        else:
            st.success("✅ No shared broadcast IPs detected in local neighborhood.")

    with col_ov2:
        if shared_nodes:
            st.warning(f"⚠️ **Shared Counterparties/Transactions ({len(shared_nodes)}):** {', '.join(list(shared_nodes)[:4])}")
        else:
            st.info("ℹ️ No directly overlapping transaction nodes found.")


def _render_entity_summary_card(entity: dict[str, Any], tag: str) -> None:
    """Render concise entity card for comparison."""
    wallet_id = str(entity.get("wallet_id", "Unknown"))
    score = float(entity.get("final_risk_score", 0.0))
    label = str(entity.get("confidence_label", "Unknown"))
    reason = str(entity.get("reason_sentence", ""))
    color = confidence_color(label)

    st.markdown(
        f"""
        <div style="background-color: #1A202C; border: 1px solid #2D3748; border-top: 4px solid {color}; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span style="background-color: #2D3748; color: #CBD5E0; padding: 2px 6px; border-radius: 3px; font-size: 0.75rem; font-weight: bold;">{tag}</span>
                    <h4 style="margin: 6px 0 0 0; color: #F7FAFC; word-break: break-all; font-size: 1rem;">{wallet_id}</h4>
                </div>
                <div style="text-align: right; min-width: 90px;">
                    <span style="font-size: 1.4rem; font-weight: bold; color: {color};">{score:.1f}</span>
                    <span style="font-size: 0.8rem; color: #718096;">/100</span>
                </div>
            </div>
            <p style="margin: 10px 0 0 0; color: #E2E8F0; font-size: 0.9rem; line-height: 1.4;">{reason}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
