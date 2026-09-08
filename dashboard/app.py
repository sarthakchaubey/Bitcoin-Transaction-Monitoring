"""Main entry point for the Bitcoin Transaction Forensics Case-File Dashboard.

Follows the exact visual design system and structure in ANTIGRAVITY_DASHBOARD_BRIEF.md.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.analytics_view import render_model_insights_tab, render_overview_tab
from dashboard.detail_view import render_case_detail_tab
from dashboard.diagnostics_view import render_evaluation_tab
from dashboard.graph_view import render_network_tab
from dashboard.utils import (
    DESIGN_TOKENS,
    filter_alerts,
    load_evidence_packages,
    risk_band_for_score,
    risk_color,
)

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="Bitcoin Forensics Case Console",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Case-File Dark Design System Styling
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,600;0,8..60,700;1,8..60,600&display=swap');

    :root {{
        --bg: {DESIGN_TOKENS['bg']};
        --surface: {DESIGN_TOKENS['surface']};
        --surface-raised: {DESIGN_TOKENS['surface_raised']};
        --border: {DESIGN_TOKENS['border']};
        --text: {DESIGN_TOKENS['text']};
        --text-muted: {DESIGN_TOKENS['text_muted']};
        --accent: {DESIGN_TOKENS['accent']};
        --accent-hover: {DESIGN_TOKENS['accent_hover']};
        --risk-low: {DESIGN_TOKENS['risk_low']};
        --risk-medium: {DESIGN_TOKENS['risk_medium']};
        --risk-high: {DESIGN_TOKENS['risk_high']};
        --risk-critical: {DESIGN_TOKENS['risk_critical']};
    }}

    .stApp {{
        background-color: var(--bg);
        color: var(--text);
        font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    h1, h2, h3, h4 {{
        font-family: 'Source Serif 4', Georgia, serif;
        color: var(--text);
        font-weight: 700;
        letter-spacing: -0.01em;
    }}

    /* Monospace for metrics and data elements */
    code, pre, .mono-data {{
        font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
    }}

    /* Custom tab navigation bar */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        border-bottom: 2px solid var(--border);
        padding-bottom: 2px;
        background-color: transparent;
    }}

    .stTabs [data-baseweb="tab"] {{
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
        font-weight: 600;
        font-size: 0.92rem;
        color: var(--text-muted);
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-bottom: none;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: var(--surface-raised) !important;
        color: var(--accent) !important;
        border-top: 2px solid var(--accent) !important;
    }}

    /* Sidebar container */
    section[data-testid="stSidebar"] {{
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }}

    /* Custom dataframe/table styling */
    .queue-table-container {{
        background-color: var(--surface);
        border: 1px solid var(--border);
        border-radius: 6px;
        overflow: hidden;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_evidence_data(path: str = "data/evidence_packages.json") -> list[dict]:
    """Load and cache the evidence packages from Phase 7."""
    return load_evidence_packages(path)


def main() -> None:
    # 3. Header & Case Console Identity
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid {DESIGN_TOKENS['border']}; padding-bottom: 14px; margin-bottom: 18px;">
            <div>
                <h1 style="margin: 0; font-size: 1.85rem; color: {DESIGN_TOKENS['text']};">
                    🛡️ Bitcoin Forensics Case Console
                </h1>
                <p style="margin: 3px 0 0 0; color: {DESIGN_TOKENS['text_muted']}; font-size: 0.9rem;">
                    Offline Transaction Monitoring, Community Risk Scoring & Explainable AI Case Investigation
                </p>
            </div>
            <div style="text-align: right;">
                <span style="background-color: {DESIGN_TOKENS['surface_raised']}; color: {DESIGN_TOKENS['accent']}; border: 1px solid {DESIGN_TOKENS['accent']}; padding: 4px 10px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600;">
                    OFFLINE FORENSICS MODE
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Load Data
    all_evidence = get_evidence_data()

    if not all_evidence:
        st.warning(
            "⚠️ No evidence packages found at `data/evidence_packages.json`. "
            "Please run the pipeline via `python main.py` first to generate forensic evidence records."
        )
        return

    # 5. Sidebar Triage Filters
    available_patterns = sorted(
        {str(item.get("pattern_hint", "unknown")) for item in all_evidence if item.get("pattern_hint")}
    )
    confidence_options = ["Critical", "High", "Medium", "Low"]

    st.sidebar.markdown(
        f"<h3 style='color: {DESIGN_TOKENS['accent']}; font-family: Source Serif 4, Georgia, serif;'>🎛️ Queue Filters</h3>",
        unsafe_allow_html=True,
    )

    min_score = st.sidebar.slider(
        "Minimum Risk Score Threshold",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
        help="Filter wallets with final_risk_score at or above this threshold.",
    )

    selected_labels = st.sidebar.multiselect(
        "Risk Severity / Confidence",
        options=confidence_options,
        default=confidence_options,
        help="Filter by assigned risk severity band.",
    )

    selected_patterns = st.sidebar.multiselect(
        "Behavioral Pattern Hint",
        options=available_patterns,
        default=available_patterns,
        help="Filter by detected behavioral topology signature.",
    )

    search_query = st.sidebar.text_input(
        "Search Target Wallet ID",
        value="",
        placeholder="e.g. 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    )

    if st.sidebar.button("🔄 Reload Evidence Records", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Filtered dataset
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

    # 6. Six Required Tabs from ANTIGRAVITY_DASHBOARD_BRIEF.md
    tab_overview, tab_queue, tab_case, tab_network, tab_models, tab_eval = st.tabs(
        [
            "📋 Overview",
            "🚨 Alert Queue",
            "📁 Case Detail",
            "🕸️ Network",
            "🧠 Model Insights",
            "📊 Evaluation",
        ]
    )

    # --- TAB 1: OVERVIEW ---
    with tab_overview:
        render_overview_tab(all_evidence)

    # --- TAB 2: ALERT QUEUE ---
    with tab_queue:
        _render_alert_queue_tab(filtered_evidence, len(all_evidence))

    # --- TAB 3: CASE DETAIL ---
    with tab_case:
        render_case_detail_tab(filtered_evidence if filtered_evidence else all_evidence)

    # --- TAB 4: NETWORK ---
    with tab_network:
        render_network_tab(filtered_evidence if filtered_evidence else all_evidence)

    # --- TAB 5: MODEL INSIGHTS ---
    with tab_models:
        render_model_insights_tab(all_evidence)

    # --- TAB 6: EVALUATION ---
    with tab_eval:
        render_evaluation_tab(all_evidence)


def _render_alert_queue_tab(filtered_evidence: list[dict], total_count: int) -> None:
    """Render Tab 2: Alert Queue sortable table with CSV export."""
    st.markdown("### 🚨 Ranked Forensic Alert Queue")
    st.caption(f"Showing {len(filtered_evidence)} of {total_count} ranked wallet entities matching active filter criteria.")

    if not filtered_evidence:
        st.info("No alert records match the active sidebar filters. Try adjusting threshold sliders or search keywords.")
        return

    # Build queue table data
    table_records = []
    csv_records = []

    for item in filtered_evidence:
        wallet_id = item.get("wallet_id", "unknown")
        score = float(item.get("final_risk_score", 0.0))
        band = risk_band_for_score(score)
        conf = item.get("confidence_label", "Unknown")
        pat = item.get("pattern_hint", "unknown")
        reason = str(item.get("reason_sentence", ""))

        preview = reason[:85] + "..." if len(reason) > 88 else reason

        table_records.append(
            {
                "Wallet ID (Target Entity)": wallet_id,
                "Risk Score": f"{score:.1f}",
                "Severity Band": band,
                "Confidence": conf,
                "Pattern Hint": pat,
                "Forensic Reason Finding": preview,
            }
        )

        csv_records.append(
            {
                "wallet_id": wallet_id,
                "final_risk_score": score,
                "severity_band": band,
                "confidence_label": conf,
                "pattern_hint": pat,
                "reason_sentence": reason,
            }
        )

    df_queue = pd.DataFrame(table_records)

    # Render formatted table
    st.dataframe(
        df_queue,
        use_container_width=True,
        hide_index=True,
    )

    # CSV Export Button
    df_csv = pd.DataFrame(csv_records)
    csv_bytes = df_csv.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Export Alert Queue (.csv)",
        data=csv_bytes,
        file_name="forensic_alert_queue.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
