"""Main entry point for the Bitcoin Transaction Forensics Dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.analytics_view import render_analytics_view
from dashboard.comparator_view import render_comparator_view
from dashboard.detail_view import render_wallet_detail
from dashboard.diagnostics_view import render_diagnostics_view
from dashboard.graph_view import render_subgraph
from dashboard.utils import (
    filter_alerts,
    load_evidence_packages,
)

# 1. Page Configuration
st.set_page_config(
    page_title="Bitcoin Forensics Console",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS styling for dark forensics console theme
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #1A202C;
        border: 1px solid #2D3748;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #2D3748;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 18px;
        border-radius: 6px 6px 0 0;
        font-weight: 600;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_evidence_data(path: str = "data/evidence_packages.json") -> list[dict]:
    """Load and cache the evidence packages from Phase 7."""
    return load_evidence_packages(path)


def main() -> None:
    # Title & Header
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #2D3748; padding-bottom: 12px; margin-bottom: 16px;">
            <div>
                <h1 style="margin: 0; font-size: 1.85rem; color: #F7FAFC;">
                    🔍 Bitcoin Transaction Forensics Console
                </h1>
                <p style="margin: 4px 0 0 0; color: #A0AEC0; font-size: 0.92rem;">
                    AI-powered transaction monitoring, anomaly scoring, SHAP explainability, and interactive graph forensics
                </p>
            </div>
            <div style="text-align: right;">
                <span style="background-color: #2D3748; color: #68D391; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: bold; border: 1px solid #38A169;">
                    ● SYSTEM ONLINE
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Load Data
    all_evidence = get_evidence_data()

    if not all_evidence:
        st.warning(
            "⚠️ No evidence packages found at `data/evidence_packages.json`. "
            "Please run the pipeline via `python main.py` first to generate forensic evidence records."
        )
        return

    # Extract distinct pattern hints for filters
    available_patterns = sorted(
        {str(item.get("pattern_hint", "unknown")) for item in all_evidence if item.get("pattern_hint")}
    )
    confidence_options = ["High", "Medium", "Low"]

    # 3. Sidebar Filters
    st.sidebar.markdown("### 🎛️ Forensics Triage Filters")

    min_score = st.sidebar.slider(
        "Minimum Risk Score Threshold",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        help="Filter wallets with final_risk_score at or above this threshold.",
    )

    selected_labels = st.sidebar.multiselect(
        "Confidence Triage Label",
        options=confidence_options,
        default=confidence_options,
        help="Filter by assigned confidence severity (High, Medium, Low).",
    )

    selected_patterns = st.sidebar.multiselect(
        "Behavioral Pattern Hint",
        options=available_patterns,
        default=available_patterns,
        help="Filter by detected behavioral topology signature.",
    )

    search_query = st.sidebar.text_input(
        "Search Wallet ID",
        value="",
        placeholder="e.g. 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    )

    if st.sidebar.button("🔄 Clear Cache & Reload", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # 4. Filter Alerts
    filtered_evidence = filter_alerts(
        all_evidence,
        min_score=min_score,
        labels=selected_labels,
        patterns=selected_patterns,
        search=search_query,
    )

    filtered_evidence.sort(
        key=lambda x: float(x.get("final_risk_score", 0.0)),
        reverse=True,
    )

    # 5. Top Summary Metrics Row
    total_analyzed = len(all_evidence)
    total_flagged = len(filtered_evidence)
    high_count = sum(1 for item in filtered_evidence if str(item.get("confidence_label", "")).casefold() == "high")
    med_count = sum(1 for item in filtered_evidence if str(item.get("confidence_label", "")).casefold() == "medium")
    low_count = sum(1 for item in filtered_evidence if str(item.get("confidence_label", "")).casefold() == "low")

    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("Wallets Analyzed", total_analyzed)
    m_col2.metric("Matching Alerts", total_flagged, delta=f"{total_flagged}/{total_analyzed}")
    m_col3.metric("High Risk (🚨)", high_count)
    m_col4.metric("Medium Risk (⚠️)", med_count)
    m_col5.metric("Low Risk (ℹ️)", low_count)

    st.markdown("---")

    # 6. Tabbed Navigation Console
    tab_triage, tab_analytics, tab_compare, tab_diagnostics = st.tabs(
        [
            "🚨 Triage & Investigation",
            "📊 Network Risk Analytics",
            "⚖️ Multi-Entity Comparator",
            "⏱️ Pipeline Diagnostics",
        ]
    )

    # --- TAB 1: TRIAGE & DRILLDOWN ---
    with tab_triage:
        if not filtered_evidence:
            st.info("No alert records match the selected sidebar filters. Try lowering the threshold or clearing filters.")
        else:
            st.markdown("### 📋 Ranked Alert Triage List")

            table_rows = []
            for item in filtered_evidence:
                reason_preview = str(item.get("reason_sentence", ""))
                if len(reason_preview) > 90:
                    reason_preview = reason_preview[:87] + "..."

                table_rows.append(
                    {
                        "Wallet ID": item.get("wallet_id", "unknown"),
                        "Risk Score": f"{float(item.get('final_risk_score', 0.0)):.1f}",
                        "Confidence": item.get("confidence_label", "Unknown"),
                        "Pattern Hint": item.get("pattern_hint", "unknown"),
                        "Forensic Reason Preview": reason_preview,
                    }
                )

            df_alerts = pd.DataFrame(table_rows)

            selection_event = st.dataframe(
                df_alerts,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="alerts_dataframe",
            )

            selected_idx = 0
            selected_rows = []
            if selection_event and hasattr(selection_event, "selection"):
                selected_rows = getattr(selection_event.selection, "rows", [])
            elif isinstance(selection_event, dict):
                selected_rows = selection_event.get("selection", {}).get("rows", [])

            if selected_rows and len(selected_rows) > 0:
                selected_idx = selected_rows[0]
                if selected_idx >= len(filtered_evidence):
                    selected_idx = 0

            selected_wallet_record = filtered_evidence[selected_idx]

            st.markdown("---")

            st.markdown(
                f"### 🔎 Evidence Inspection: `{selected_wallet_record.get('wallet_id', '')}`"
            )

            col_detail, col_graph = st.columns([1, 1], gap="medium")

            with col_detail:
                render_wallet_detail(selected_wallet_record)

            with col_graph:
                render_subgraph(selected_wallet_record)

    # --- TAB 2: NETWORK RISK ANALYTICS ---
    with tab_analytics:
        render_analytics_view(all_evidence)

    # --- TAB 3: MULTI-ENTITY COMPARATOR ---
    with tab_compare:
        render_comparator_view(all_evidence)

    # --- TAB 4: PIPELINE DIAGNOSTICS ---
    with tab_diagnostics:
        render_diagnostics_view(all_evidence)


if __name__ == "__main__":
    main()
