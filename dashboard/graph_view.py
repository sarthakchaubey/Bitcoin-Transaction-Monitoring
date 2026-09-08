"""Interactive graph view component for visualizing transaction/IP network neighborhoods."""

from __future__ import annotations

from typing import Any

from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components

from dashboard.utils import DESIGN_TOKENS, risk_color


def render_network_tab(evidence_list: list[dict[str, Any]]) -> None:
    """Render Tab 4: Network forensics graph with single-neighborhood and multi-wallet views."""
    if not evidence_list:
        st.info("No evidence subgraphs available.")
        return

    st.markdown("### 🕸️ Interactive Forensics Network Graph")
    st.caption("Inspect local counterparty transaction flows, multi-hop peeling paths, and broadcast IP clustering.")

    wallet_options = [str(item.get("wallet_id", "")) for item in evidence_list]

    top_col1, top_col2 = st.columns([2, 1])
    with top_col1:
        selected_wallet_id = st.selectbox(
            "Select Focus Wallet Entity",
            options=wallet_options,
            index=0,
            key="network_focus_wallet",
        )
    with top_col2:
        graph_mode = st.radio(
            "Graph View Scope",
            options=["Single Wallet Neighborhood", "Top High-Risk Multi-Wallet Network"],
            index=0,
            horizontal=True,
        )

    if graph_mode == "Single Wallet Neighborhood":
        selected_evidence = next((item for item in evidence_list if item.get("wallet_id") == selected_wallet_id), evidence_list[0])
        render_subgraph(selected_evidence)
    else:
        # Render combined graph of top high-risk packages
        top_packages = [e for e in evidence_list if float(e.get("final_risk_score", 0.0)) >= 50.0]
        if not top_packages:
            top_packages = evidence_list[:3]
        _render_combined_network(top_packages)


def render_subgraph(evidence: dict[str, Any]) -> None:
    """Convert evidence subgraph to a pyvis Network and render in Streamlit with visual controls."""
    if not evidence:
        st.info("No subgraph data to display.")
        return

    subgraph_data = evidence.get("subgraph", {})
    nodes = subgraph_data.get("nodes", [])
    edges = subgraph_data.get("edges", [])
    selected_wallet = str(evidence.get("wallet_id", ""))

    if not nodes:
        st.info("No neighborhood graph available for this wallet.")
        return

    # Physics & Display Controls
    with st.expander("⚙️ Graph Physics & Layout Controls", expanded=False):
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
        with ctrl_col1:
            spring_length = st.slider("Spring Distance", min_value=60, max_value=240, value=130, step=10, key="sub_spring")
        with ctrl_col2:
            gravity = st.slider("Node Repulsion (Gravity)", min_value=-4000, max_value=-1000, value=-2500, step=250, key="sub_grav")
        with ctrl_col3:
            enable_physics = st.checkbox("Enable Physics Simulation", value=True, key="sub_phys")

    # Topology Summary Pills
    wallet_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "wallet")
    tx_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "transaction")
    ip_count = sum(1 for n in nodes if str(n.get("type", "")).lower() == "ip")

    st.markdown(
        f"""
        <div style="display: flex; gap: 8px; margin-bottom: 10px;">
            <span style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid #3182CE; color: #EBF8FF; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; padding: 3px 10px; border-radius: 4px;">● {wallet_count} Wallets</span>
            <span style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['text_muted']}; color: #F7FAFC; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; padding: 3px 10px; border-radius: 4px;">◆ {tx_count} Transactions</span>
            <span style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['risk_high']}; color: #FFFAF0; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; padding: 3px 10px; border-radius: 4px;">▲ {ip_count} Broadcast IPs</span>
            <span style="background-color: {DESIGN_TOKENS['surface_raised']}; border: 1px solid {DESIGN_TOKENS['border']}; color: {DESIGN_TOKENS['text_muted']}; font-size: 0.78rem; font-family: 'IBM Plex Mono', monospace; font-weight: 600; padding: 3px 10px; border-radius: 4px;">🔗 {len(edges)} Edges</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize Pyvis Network with design system dark background
    net = Network(
        height="500px",
        width="100%",
        bgcolor=DESIGN_TOKENS["bg"],
        font_color=DESIGN_TOKENS["text"],
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
                title=f"TARGET ENTITY\nID: {node_id}\nType: {node_type}",
                color={"background": DESIGN_TOKENS["risk_critical"], "border": DESIGN_TOKENS["accent"], "highlight": DESIGN_TOKENS["accent_hover"]},
                size=28,
                shape="dot",
                font={"color": "#FFFFFF", "size": 13, "face": "Courier New", "bold": True},
                borderWidth=3,
            )
        elif node_type == "wallet":
            cluster = node.get("cluster_id", "N/A")
            net.add_node(
                node_id,
                label=display_label,
                title=f"Counterparty Wallet: {node_id}\nCluster: {cluster}",
                color={"background": "#3182CE", "border": "#63B3ED", "highlight": "#90CDF4"},
                size=18,
                shape="dot",
                font={"color": DESIGN_TOKENS["text"], "size": 11, "face": "Courier New"},
            )
        elif node_type == "transaction":
            fee = node.get("fee", "N/A")
            net.add_node(
                node_id,
                label=display_label,
                title=f"Transaction Hub: {node_id}\nFee: {fee}",
                color={"background": DESIGN_TOKENS["surface_raised"], "border": DESIGN_TOKENS["text_muted"], "highlight": DESIGN_TOKENS["text"]},
                size=16,
                shape="diamond",
                font={"color": DESIGN_TOKENS["text_muted"], "size": 10, "face": "Courier New"},
            )
        elif node_type == "ip":
            country = node.get("country", "Unknown")
            high_risk = " (HIGH RISK)" if node.get("high_risk") else ""
            ip_color = DESIGN_TOKENS["risk_critical"] if node.get("high_risk") else DESIGN_TOKENS["risk_high"]
            net.add_node(
                node_id,
                label=display_label,
                title=f"Broadcast IP: {node_id}\nCountry: {country}{high_risk}",
                color={"background": ip_color, "border": DESIGN_TOKENS["accent"], "highlight": DESIGN_TOKENS["accent_hover"]},
                size=17,
                shape="triangle",
                font={"color": DESIGN_TOKENS["text"], "size": 10, "face": "Courier New"},
            )
        else:
            net.add_node(
                node_id,
                label=display_label,
                title=f"Entity: {node_id}\nType: {node_type}",
                color={"background": "#805AD5", "border": "#D6BCFA"},
                size=15,
                shape="dot",
                font={"color": DESIGN_TOKENS["text"], "size": 10},
            )

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
                color={"color": DESIGN_TOKENS["border"], "highlight": DESIGN_TOKENS["accent"], "hover": DESIGN_TOKENS["accent_hover"]},
                width=1.5,
                arrows="to",
            )

    raw_html = net.generate_html()
    components.html(raw_html, height=520, scrolling=False)

    _render_legend()


def _render_combined_network(evidence_list: list[dict[str, Any]]) -> None:
    """Render multi-wallet combined high-risk network topology."""
    st.markdown(f"#### 🌐 Combined Topology ({len(evidence_list)} High-Risk Entities)")

    net = Network(
        height="500px",
        width="100%",
        bgcolor=DESIGN_TOKENS["bg"],
        font_color=DESIGN_TOKENS["text"],
        directed=True,
    )
    net.barnes_hut(gravity=-3000, central_gravity=0.2, spring_length=150, spring_strength=0.04)

    target_wallets = {str(e.get("wallet_id", "")) for e in evidence_list}
    added_nodes = set()

    for evidence in evidence_list:
        sub = evidence.get("subgraph", {})
        for node in sub.get("nodes", []):
            node_id = str(node.get("id", ""))
            if not node_id or node_id in added_nodes:
                continue
            added_nodes.add(node_id)

            node_type = str(node.get("type", "wallet")).casefold()
            is_target = node_id in target_wallets

            if is_target:
                score = float(evidence.get("final_risk_score", 0.0))
                b_color = risk_color(score)
                net.add_node(
                    node_id,
                    label=f"★ {node_id[:8]}...",
                    title=f"Flagged Wallet: {node_id}\nRisk: {score:.1f}",
                    color={"background": b_color, "border": DESIGN_TOKENS["accent"]},
                    size=24,
                    shape="dot",
                    font={"color": "#FFFFFF", "size": 11, "bold": True},
                )
            elif node_type == "ip":
                country = node.get("country", "Unknown")
                net.add_node(
                    node_id,
                    label=node_id,
                    title=f"IP: {node_id} ({country})",
                    color={"background": DESIGN_TOKENS["risk_high"], "border": DESIGN_TOKENS["accent"]},
                    size=16,
                    shape="triangle",
                    font={"color": DESIGN_TOKENS["text"], "size": 10},
                )
            else:
                net.add_node(
                    node_id,
                    label=f"{node_id[:8]}...",
                    title=f"Node: {node_id}",
                    color={"background": "#3182CE", "border": DESIGN_TOKENS["border"]},
                    size=14,
                    shape="dot",
                    font={"color": DESIGN_TOKENS["text_muted"], "size": 9},
                )

        for edge in sub.get("edges", []):
            src = str(edge.get("source", ""))
            dst = str(edge.get("target", ""))
            if src in added_nodes and dst in added_nodes:
                net.add_edge(src, dst, color={"color": DESIGN_TOKENS["border"]}, width=1.2, arrows="to")

    components.html(net.generate_html(), height=520, scrolling=False)
    _render_legend()


def _render_legend() -> None:
    """Render standard forensic cues legend."""
    st.markdown(
        f"""
        <div style="font-size: 0.82rem; color: {DESIGN_TOKENS['text_muted']}; background-color: {DESIGN_TOKENS['surface']}; border: 1px solid {DESIGN_TOKENS['border']}; border-radius: 4px; padding: 10px 14px; margin-top: 8px;">
            <strong style="color: {DESIGN_TOKENS['accent']};">Forensics Visual Cues:</strong><br>
            • <span style="color: {DESIGN_TOKENS['risk_critical']}; font-weight: bold;">★ Target Node</span>: Primary inspected wallet entity.<br>
            • <span style="color: #63B3ED;">● Blue Nodes</span>: Counterparty wallets & cluster members.<br>
            • <span style="color: {DESIGN_TOKENS['text_muted']};">◆ Slate Diamonds</span>: Transaction hubs (mixing nodes have multiple in/out branches).<br>
            • <span style="color: {DESIGN_TOKENS['risk_high']};">▲ Orange Triangles</span>: Broadcast IPs (multiple wallets linked to one IP indicate shared infrastructure).
        </div>
        """,
        unsafe_allow_html=True,
    )
