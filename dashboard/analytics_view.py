"""Network-wide forensic analytics and risk distribution view."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dashboard.utils import compute_network_summary_stats


def render_analytics_view(evidence_list: list[dict[str, Any]]) -> None:
    """Render aggregate network forensics, risk distributions, and geo patterns."""
    if not evidence_list:
        st.info("No data available for network analytics.")
        return

    stats = compute_network_summary_stats(evidence_list)

    st.markdown("### 📊 Network Risk Analytics & Topological Distribution")
    st.caption("Aggregate behavioral patterns, risk distributions, and geographic exposure across monitored wallets.")

    # High-level summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monitored Wallets", stats["total_wallets"])
    col2.metric("Mean Network Risk", f"{stats['avg_risk_score']:.1f} / 100")
    col3.metric("Peak Entity Risk", f"{stats['max_risk_score']:.1f} / 100")
    col4.metric("High-Risk Geo Hits", stats["high_risk_geo_count"], delta_color="inverse")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # 1. Risk Score Distribution Chart
    with col_left:
        st.markdown("#### 🎯 Risk Score Distribution")
        scores = [float(item.get("final_risk_score", 0.0)) for item in evidence_list]

        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#1A202C")
        ax.set_facecolor("#1A202C")

        n, bins, patches = ax.hist(
            scores, bins=10, range=(0, 100), color="#3182CE", edgecolor="#2D3748", alpha=0.85
        )

        # Color-code bins by risk band
        for i, patch in enumerate(patches):
            center = (bins[i] + bins[i + 1]) / 2
            if center >= 70:
                patch.set_facecolor("#E53E3E")
            elif center >= 40:
                patch.set_facecolor("#DD6B20")
            else:
                patch.set_facecolor("#38A169")

        ax.set_xlabel("Final Risk Score (0–100)", color="#A0AEC0", fontsize=9)
        ax.set_ylabel("Wallet Count", color="#A0AEC0", fontsize=9)
        ax.tick_params(colors="#A0AEC0", labelsize=8.5)
        ax.grid(axis="y", linestyle="--", alpha=0.25, color="#4A5568")

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # 2. Behavioral Pattern Breakdown
    with col_right:
        st.markdown("#### 🔄 Behavioral Pattern Classification")
        pattern_data = stats["pattern_counts"]
        if pattern_data:
            pat_df = (
                pd.DataFrame(list(pattern_data.items()), columns=["Pattern", "Count"])
                .sort_values(by="Count", ascending=True)
            )

            fig, ax = plt.subplots(figsize=(6, 3.8))
            fig.patch.set_facecolor("#1A202C")
            ax.set_facecolor("#1A202C")

            colors = ["#805AD5", "#3182CE", "#DD6B20", "#E53E3E", "#718096"]
            bar_colors = [colors[i % len(colors)] for i in range(len(pat_df))]

            bars = ax.barh(pat_df["Pattern"], pat_df["Count"], color=bar_colors, height=0.55)
            ax.set_xlabel("Number of Wallets", color="#A0AEC0", fontsize=9)
            ax.tick_params(colors="#A0AEC0", labelsize=8.5)
            ax.grid(axis="x", linestyle="--", alpha=0.25, color="#4A5568")

            for bar in bars:
                w = bar.get_width()
                ax.text(
                    w + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    f"{int(w)}",
                    va="center",
                    color="#CBD5E0",
                    fontsize=8.5,
                )

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    st.markdown("---")

    col_geo, col_features = st.columns(2)

    # 3. Geographic IP Exposure
    with col_geo:
        st.markdown("#### 🌍 Broadcast IP Geolocation Breakdown")
        country_data = stats["country_counts"]
        if country_data:
            c_df = (
                pd.DataFrame(list(country_data.items()), columns=["Country", "IP Count"])
                .sort_values(by="IP Count", ascending=False)
                .head(8)
            )

            fig, ax = plt.subplots(figsize=(6, 3.5))
            fig.patch.set_facecolor("#1A202C")
            ax.set_facecolor("#1A202C")

            ax.bar(c_df["Country"], c_df["IP Count"], color="#DD6B20", edgecolor="#2D3748", width=0.5)
            ax.set_ylabel("Distinct Broadcast IPs", color="#A0AEC0", fontsize=9)
            ax.tick_params(colors="#A0AEC0", labelsize=8.5, rotation=25)
            ax.grid(axis="y", linestyle="--", alpha=0.25, color="#4A5568")

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("No IP geolocation records present in evidence subgraphs.")

    # 4. Top Dominant SHAP Features Across Network
    with col_features:
        st.markdown("#### ⚡ Most Prevalent Anomaly Drivers (SHAP)")
        feature_impact: dict[str, float] = {}
        for item in evidence_list:
            for feat in item.get("shap_explanation", []):
                fname = feat.get("feature", "unknown")
                sval = abs(float(feat.get("shap_value", 0.0)))
                feature_impact[fname] = feature_impact.get(fname, 0.0) + sval

        if feature_impact:
            f_df = (
                pd.DataFrame(list(feature_impact.items()), columns=["Feature", "Aggregate Impact"])
                .sort_values(by="Aggregate Impact", ascending=True)
                .tail(7)
            )

            fig, ax = plt.subplots(figsize=(6, 3.5))
            fig.patch.set_facecolor("#1A202C")
            ax.set_facecolor("#1A202C")

            ax.barh(f_df["Feature"], f_df["Aggregate Impact"], color="#E53E3E", height=0.5)
            ax.set_xlabel("Cumulative Absolute SHAP Value", color="#A0AEC0", fontsize=9)
            ax.tick_params(colors="#A0AEC0", labelsize=8.5)
            ax.grid(axis="x", linestyle="--", alpha=0.25, color="#4A5568")

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
