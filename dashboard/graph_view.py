"""Interactive graph view component for visualizing transaction/IP subgraphs."""

from __future__ import annotations

from typing import Any

from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components


def render_subgraph(evidence: dict[str, Any]) -> None:
    """Convert evidence subgraph to a pyvis Network and render in Streamlit with visual controls."""
    if not evidence:
        st.info("No subgraph data to display.")
        return

    subgraph_data = evidence.get("subgraph", {})
    nodes = subgraph_data.get("nodes", [])
    edges = subgraph_data.get("edges", [])
    selected_wallet = str(evidence.get("wallet_id", ""))

    st.markdown("#### 🕸️ Transaction & IP Neighborhood Graph")

    if not nodes:
        st.info("No neighborhood graph available for this wallet.")
        return

    # Visual Layout & Physics Controls
    with st.expander("⚙️ Graph Physics & Display Controls", expanded=False):
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
        with ctrl_col1:
            spring_length = st.slider("Spring Distance", min_value=60, max_value=220, value=120, step=10)
        with ctrl_col2:
            gravity = st.slider("Node Repulsion (Gravity)", min_value=-4000, max_value=-1000, value=-2500, step=250)
        with ctrl_col3:
            enable_physics = st.checkbox("Enable Physics Simulation", value=True)

    # Topology Summary Pills
    wallet_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "wallet")
    tx_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "transaction")
    ip_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "ip")

    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <span style="background-color: #2B6CB0; color: #EBF8FF; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 12px;">● {wallet_count} Wallets</span>
            <span style="background-color: #4A5568; color: #F7FAFC; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 12px;">◆ {tx_count} Transactions</span>
            <span style="background-color: #C05621; color: #FFFAF0; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 12px;">▲ {ip_count} Broadcast IPs</span>
            <span style="background-color: #2D3748; color: #CBD5E0; font-size: 0.78rem; font-weight: 600; padding: 2px 8px; border-radius: 12px;">🔗 {len(edges)} Edges</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize Pyvis Network
    net = Network(
        height="480px",
        width="100%",
        bgcolor="#1A202C",
        font_color="#F7FAFC",
        directed=True,
    )

    if enable_physics:
        net.barnes_hut(
            gravity=gravity,
            central_gravity=0.25,
            spring_length=spring_length,
            spring_strength=0.05,
            damping=0.12,
        )
    else:
        net.toggle_physics(False)

    # Add nodes with distinct styling by type
    added_nodes = set()
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id or node_id in added_nodes:
            continue
        added_nodes.add(node_id)

        node_type = str(node.get("type", "wallet")).casefold()
        is_selected = (node_id == selected_wallet)

        display_label = (
            f"{node_id[:10]}..." if len(node_id) > 12 and node_type != "ip" else node_id
        )

        if is_selected:
            net.add_node(
                node_id,
                label=f"★ {display_label}",
                title=f"SELECTED WALLET\nID: {node_id}\nType: {node_type}",
                color={"background": "#E53E3E", "border": "#FFF5F5", "highlight": "#FEB2B2"},
                size=26,
                shape="dot",
                font={"color": "#FFF", "size": 13, "face": "Courier New", "bold": True},
                borderWidth=3,
            )
        elif node_type == "wallet":
            cluster = node.get("cluster_id", "N/A")
            net.add_node(
                node_id,
                label=display_label,
                title=f"Wallet: {node_id}\nCluster: {cluster}",
                color={"background": "#3182CE", "border": "#63B3ED", "highlight": "#90CDF4"},
                size=18,
                shape="dot",
                font={"color": "#E2E8F0", "size": 11},
            )
        elif node_type == "transaction":
            fee = node.get("fee", "N/A")
            net.add_node(
                node_id,
                label=display_label,
                title=f"Transaction: {node_id}\nFee: {fee}",
                color={"background": "#718096", "border": "#CBD5E0", "highlight": "#E2E8F0"},
                size=16,
                shape="diamond",
                font={"color": "#CBD5E0", "size": 10},
            )
        elif node_type == "ip":
            country = node.get("country", "Unknown")
            high_risk = " (HIGH RISK)" if node.get("high_risk") else ""
            ip_color = "#E53E3E" if node.get("high_risk") else "#DD6B20"
            net.add_node(
                node_id,
                label=display_label,
                title=f"IP Address: {node_id}\nCountry: {country}{high_risk}",
                color={"background": ip_color, "border": "#FBD38D", "highlight": "#FEEBC8"},
                size=17,
                shape="triangle",
                font={"color": "#FEEBC8", "size": 10},
            )
        else:
            net.add_node(
                node_id,
                label=display_label,
                title=f"Entity: {node_id}\nType: {node_type}",
                color={"background": "#805AD5", "border": "#D6BCFA"},
                size=15,
                shape="dot",
                font={"color": "#E2E8F0", "size": 10},
            )

    # Add edges
    for edge in edges:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        if source in added_nodes and target in added_nodes:
            edge_type = str(edge.get("type", "transfer"))
            amount = edge.get("amount")
            title_text = f"Type: {edge_type}"
            if amount is not None:
                title_text += f"\nAmount: {amount} BTC"

            net.add_edge(
                source,
                target,
                title=title_text,
                color={"color": "#4A5568", "highlight": "#CBD5E0", "hover": "#A0AEC0"},
                width=1.5,
                arrows="to",
            )

    raw_html = net.generate_html()
    components.html(raw_html, height=500, scrolling=False)

    # Explanatory Caption
    st.markdown(
        """
        <div style="font-size: 0.82rem; color: #A0AEC0; background-color: #1A202C; border: 1px solid #2D3748; border-radius: 4px; padding: 8px 12px; margin-top: 8px;">
            <strong>Legend & Forensic Cues:</strong><br>
            • <span style="color: #E53E3E;">★ Red node</span>: Currently inspected flagged wallet.<br>
            • <span style="color: #63B3ED;">● Blue nodes</span>: Counterparty wallets.<br>
            • <span style="color: #CBD5E0;">◆ Grey diamonds</span>: Transactions (fan-in/fan-out hubs have many wallet links).<br>
            • <span style="color: #F6AD55;">▲ Orange triangles</span>: Broadcast IP nodes (wallets linked to many IPs indicate geo-hopping/mixers).
        </div>
        """,
        unsafe_allow_html=True,
    )
