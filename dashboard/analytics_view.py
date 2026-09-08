"""Overview metrics, network distribution charts, and model insights view."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dashboard.utils import DESIGN_TOKENS, compute_network_summary_stats, risk_band_for_score


def render_overview_tab(evidence_list: list[dict[str, Any]]) -> None:
    """Render Tab 1: Overview with headline metrics and distribution charts."""
    if not evidence_list:
        st.info("No evidence packages loaded.")
        return

    stats = compute_network_summary_stats(evidence_list)

    # Headline Metric Cards Row
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        _render_metric_card("Wallets Analyzed", str(stats["total_wallets"]), DESIGN_TOKENS["accent"])
    with m2:
        _render_metric_card("Flagged Alerts", str(stats["total_wallets"]), DESIGN_TOKENS["accent"])
    with m3:
        crit_high = stats["critical_count"] + stats["high_count"]
        _render_metric_card("Critical / High", str(crit_high), DESIGN_TOKENS["risk_critical"])
    with m4:
        _render_metric_card("Medium Risk", str(stats["medium_count"]), DESIGN_TOKENS["risk_medium"])
    with m5:
        _render_metric_card("Flagged Volume", f"{stats['total_flagged_volume_btc']:.2f} BTC", DESIGN_TOKENS["accent"])

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    # 1. Risk Score Distribution
    with col_left:
        st.markdown("#### 🎯 Risk Score Distribution")
        scores = [float(item.get("final_risk_score", 0.0)) for item in evidence_list]

        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
        ax.set_facecolor(DESIGN_TOKENS["surface"])

        n, bins, patches = ax.hist(
            scores, bins=10, range=(0, 100), color=DESIGN_TOKENS["accent"], edgecolor=DESIGN_TOKENS["border"], alpha=0.9
        )

        for i, patch in enumerate(patches):
            center = (bins[i] + bins[i + 1]) / 2
            if center >= 90:
                patch.set_facecolor(DESIGN_TOKENS["risk_critical"])
            elif center >= 70:
                patch.set_facecolor(DESIGN_TOKENS["risk_high"])
            elif center >= 40:
                patch.set_facecolor(DESIGN_TOKENS["risk_medium"])
            else:
                patch.set_facecolor(DESIGN_TOKENS["risk_low"])

        ax.set_xlabel("Final Risk Score (0–100)", color=DESIGN_TOKENS["text_muted"], fontsize=9, fontfamily="monospace")
        ax.set_ylabel("Wallet Count", color=DESIGN_TOKENS["text_muted"], fontsize=9)
        ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5)
        ax.grid(axis="y", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
        for spine in ax.spines.values():
            spine.set_color(DESIGN_TOKENS["border"])

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    # 2. Behavioral Pattern Frequency
    with col_right:
        st.markdown("#### 🔄 Behavioral Pattern Frequency")
        pattern_data = stats["pattern_counts"]
        if pattern_data:
            pat_df = (
                pd.DataFrame(list(pattern_data.items()), columns=["Pattern", "Count"])
                .sort_values(by="Count", ascending=True)
            )

            fig, ax = plt.subplots(figsize=(6, 3.8))
            fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
            ax.set_facecolor(DESIGN_TOKENS["surface"])

            colors = [
                DESIGN_TOKENS["accent"],
                DESIGN_TOKENS["risk_high"],
                DESIGN_TOKENS["risk_critical"],
                DESIGN_TOKENS["risk_low"],
                DESIGN_TOKENS["text_muted"],
            ]
            bar_colors = [colors[i % len(colors)] for i in range(len(pat_df))]

            bars = ax.barh(pat_df["Pattern"], pat_df["Count"], color=bar_colors, height=0.55)
            ax.set_xlabel("Number of Flagged Wallets", color=DESIGN_TOKENS["text_muted"], fontsize=9)
            ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5)
            ax.grid(axis="x", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
            for spine in ax.spines.values():
                spine.set_color(DESIGN_TOKENS["border"])

            for bar in bars:
                w = bar.get_width()
                ax.text(
                    w + 0.05,
                    bar.get_y() + bar.get_height() / 2,
                    f" {int(w)}",
                    va="center",
                    color=DESIGN_TOKENS["text"],
                    fontsize=8.5,
                    fontfamily="monospace",
                )

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    st.markdown("---")

    col_geo, col_bands = st.columns(2)

    # 3. Geographic IP Exposure
    with col_geo:
        st.markdown("#### 🌍 Flagged Jurisdictions & Broadcast IPs")
        country_data = stats["country_counts"]
        if country_data:
            c_df = (
                pd.DataFrame(list(country_data.items()), columns=["Country", "IP Count"])
                .sort_values(by="IP Count", ascending=False)
                .head(8)
            )

            fig, ax = plt.subplots(figsize=(6, 3.5))
            fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
            ax.set_facecolor(DESIGN_TOKENS["surface"])

            ax.bar(c_df["Country"], c_df["IP Count"], color=DESIGN_TOKENS["risk_high"], edgecolor=DESIGN_TOKENS["border"], width=0.5)
            ax.set_ylabel("Distinct Broadcast IPs", color=DESIGN_TOKENS["text_muted"], fontsize=9)
            ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5, rotation=25)
            ax.grid(axis="y", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
            for spine in ax.spines.values():
                spine.set_color(DESIGN_TOKENS["border"])

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("No IP geolocation records present in evidence subgraphs.")

    # 4. Risk Severity Breakdown
    with col_bands:
        st.markdown("#### 🛡️ Risk Severity Band Breakdown")
        bands_data = {
            "Critical (≥90)": stats["critical_count"],
            "High (70–89)": stats["high_count"],
            "Medium (40–69)": stats["medium_count"],
            "Low (<40)": stats["low_count"],
        }
        b_df = pd.DataFrame(list(bands_data.items()), columns=["Severity Band", "Count"])

        fig, ax = plt.subplots(figsize=(6, 3.5))
        fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
        ax.set_facecolor(DESIGN_TOKENS["surface"])

        b_colors = [
            DESIGN_TOKENS["risk_critical"],
            DESIGN_TOKENS["risk_high"],
            DESIGN_TOKENS["risk_medium"],
            DESIGN_TOKENS["risk_low"],
        ]
        ax.bar(b_df["Severity Band"], b_df["Count"], color=b_colors, width=0.5, edgecolor=DESIGN_TOKENS["border"])
        ax.set_ylabel("Wallet Count", color=DESIGN_TOKENS["text_muted"], fontsize=9)
        ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5, rotation=15)
        ax.grid(axis="y", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
        for spine in ax.spines.values():
            spine.set_color(DESIGN_TOKENS["border"])

        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)


def render_model_insights_tab(evidence_list: list[dict[str, Any]]) -> None:
    """Render Tab 5: Model Insights with component risk correlations and global SHAP drivers."""
    st.markdown("### 🧠 Model Insights & Ensemble Signals")
    st.caption("Decomposition of anomaly detection scores, graph community risks, and global feature attributions.")

    if not evidence_list:
        st.info("No evidence records available.")
        return

    col1, col2 = st.columns(2)

    # 1. Global SHAP Feature Importance Ranking
    with col1:
        st.markdown("#### ⚡ Global SHAP Feature Impact")
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
                .tail(8)
            )

            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
            ax.set_facecolor(DESIGN_TOKENS["surface"])

            ax.barh(f_df["Feature"], f_df["Aggregate Impact"], color=DESIGN_TOKENS["accent"], height=0.5)
            ax.set_xlabel("Mean Absolute SHAP Value", color=DESIGN_TOKENS["text_muted"], fontsize=9)
            ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5)
            ax.grid(axis="x", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
            for spine in ax.spines.values():
                spine.set_color(DESIGN_TOKENS["border"])

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

    # 2. Risk Distribution by Pattern Type
    with col2:
        st.markdown("#### 📈 Risk Score Distribution by Pattern")
        rows = []
        for item in evidence_list:
            rows.append(
                {
                    "Pattern": item.get("pattern_hint", "unknown"),
                    "Risk Score": float(item.get("final_risk_score", 0.0)),
                }
            )
        p_df = pd.DataFrame(rows)

        if not p_df.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor(DESIGN_TOKENS["surface"])
            ax.set_facecolor(DESIGN_TOKENS["surface"])

            patterns = p_df["Pattern"].unique()
            data_by_pat = [p_df[p_df["Pattern"] == p]["Risk Score"].values for p in patterns]

            bp = ax.boxplot(data_by_pat, tick_labels=patterns, patch_artist=True)
            for box in bp["boxes"]:
                box.set_facecolor(DESIGN_TOKENS["surface_raised"])
                box.set_edgecolor(DESIGN_TOKENS["accent"])
            for whisker in bp["whiskers"]:
                whisker.set_color(DESIGN_TOKENS["text_muted"])
            for cap in bp["caps"]:
                cap.set_color(DESIGN_TOKENS["text_muted"])
            for median in bp["medians"]:
                median.set_color(DESIGN_TOKENS["risk_critical"])
                median.set_linewidth(2)

            ax.set_ylabel("Risk Score (0–100)", color=DESIGN_TOKENS["text_muted"], fontsize=9)
            ax.tick_params(colors=DESIGN_TOKENS["text_muted"], labelsize=8.5, rotation=20)
            ax.grid(axis="y", linestyle="--", alpha=0.2, color=DESIGN_TOKENS["border"])
            for spine in ax.spines.values():
                spine.set_color(DESIGN_TOKENS["border"])

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)


def _render_metric_card(label: str, value: str, top_color: str) -> None:
    """Render a styled forensic metric card matching design system tokens."""
    st.markdown(
        f"""
        <div style="background-color: {DESIGN_TOKENS['surface']}; border: 1px solid {DESIGN_TOKENS['border']}; border-top: 3px solid {top_color}; border-radius: 6px; padding: 12px 14px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);">
            <div style="font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: {DESIGN_TOKENS['text_muted']}; margin-bottom: 4px;">
                {label}
            </div>
            <div style="font-size: 1.6rem; font-weight: bold; font-family: 'IBM Plex Mono', Courier, monospace; color: {DESIGN_TOKENS['text']}; line-height: 1.1;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
