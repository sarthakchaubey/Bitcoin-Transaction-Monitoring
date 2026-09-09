"""Pipeline entry point for the Bitcoin transaction monitoring project."""

from pathlib import Path

import pandas as pd

from features.build_features import build_feature_table
from features.pipeline import FeaturePipeline
from explain.evidence_package import build_all_evidence_packages

from explain.shap_explainer import ShapExplainer
from geoip.enrich import enrich_dataframe
from geoip.lookup import GeoIPLookup
from geoip.risk import flag_high_risk_geo
from graph.builder import build_graph as build_entity_graph
from graph.clustering import (
    annotate_graph_with_clusters,
    common_input_ownership_clusters,
    merge_change_addresses_into_clusters,
)
from graph.features import compute_wallet_features
from graph.visualization_export import graph_summary_stats
from ingestion.loader import load_transactions
from models.anomaly_detector import AnomalyDetector
from models.ensemble import combine_scores, rank_alerts
from models.evaluate import evaluate_against_ground_truth
from models.graph_detector import detect_communities, score_communities


def app(environ, start_response):
    """Return a lightweight Vercel health response for the CLI-oriented project."""
    import json

    payload = {
        "service": "bitcoin-transaction-monitoring",
        "status": "ok",
        "message": "Use Streamlit for the interactive dashboard.",
        "dashboard_command": "streamlit run dashboard/app.py",
    }
    body = json.dumps(payload).encode("utf-8")
    start_response(
        "200 OK",
        [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))],
    )
    return [body]


def load_or_generate_dataset():
    """Load an existing dataset or generate synthetic data in Phase 1."""
    print("[Phase 1] not yet implemented")


def ingest_data(path: str = "data/raw/transactions.csv"):
    """Load and validate the Phase 1 transaction dataset for later phases."""
    transactions = load_transactions(path)
    print(f"[Phase 2] loaded {len(transactions)} valid transactions")
    return transactions


def build_graph(df):
    """Build, cluster, annotate, and feature-engineer the Phase 4 graph."""
    graph = build_entity_graph(df)
    clusters = common_input_ownership_clusters(df)
    clusters = merge_change_addresses_into_clusters(df, clusters)
    annotate_graph_with_clusters(graph, clusters)
    wallet_features = compute_wallet_features(graph, df)
    print(f"[Phase 4] graph summary: {graph_summary_stats(graph)}")
    return graph, wallet_features


def engineer_features(wallet_df, raw_tx_df):
    """Build the human-readable feature table and scaled ML matrix."""
    feature_table = build_feature_table(wallet_df, raw_tx_df)
    pipeline = FeaturePipeline()
    feature_matrix = pipeline.fit_transform(feature_table)
    print(f"[Phase 5] feature matrix shape: {feature_matrix.shape}")
    print(f"[Phase 5] feature names: {pipeline.feature_names_}")
    return feature_matrix, feature_table, pipeline


def run_models(
    feature_matrix,
    feature_table,
    graph,
    ground_truth_path: str = "data/ground_truth/ground_truth.csv",
):
    """Fit anomaly/community detectors, rank wallets, and evaluate alerts."""
    anomaly_detector = AnomalyDetector().fit(feature_matrix)
    wallet_ids = (
        feature_table["wallet_id"]
        if "wallet_id" in feature_table.columns
        else feature_table["cluster_id"]
    )
    anomaly_scores = pd.Series(
        anomaly_detector.score(feature_matrix), index=wallet_ids, name="anomaly_score"
    )
    communities = detect_communities(graph)
    community_table = score_communities(graph, communities, feature_table)
    community_scores = community_table.set_index("wallet_id")["community_risk_score"]
    final_scores = combine_scores(anomaly_scores, community_scores)
    review_table = feature_table.copy()
    review_table["anomaly_score"] = anomaly_scores.to_numpy()
    review_table["community_risk_score"] = community_scores.reindex(wallet_ids).fillna(0.0).to_numpy()
    ranked_alerts = rank_alerts(review_table, final_scores, top_n=10)
    print("[Phase 6] top alerts:")
    print(ranked_alerts.to_string(index=False))
    evaluation = None
    if Path(ground_truth_path).exists():
        evaluation = evaluate_against_ground_truth(ranked_alerts, ground_truth_path)
    else:
        print(f"[Phase 6] ground truth not found; skipped evaluation: {ground_truth_path}")
    return ranked_alerts, evaluation, anomaly_detector


def generate_explanations(
    feature_matrix,
    feature_table,
    feature_pipeline,
    anomaly_detector,
    ranked_alerts,
    graph,
):
    """Generate SHAP explanations and save dashboard-ready evidence packages."""
    explainer = ShapExplainer().fit(anomaly_detector, feature_matrix)
    feature_ids = (
        feature_table["wallet_id"]
        if "wallet_id" in feature_table.columns
        else feature_table["cluster_id"]
    )
    positions = {wallet_id: position for position, wallet_id in enumerate(feature_ids)}
    ranked_positions = [positions[wallet_id] for wallet_id in ranked_alerts["wallet_id"]]
    ranked_matrix = feature_matrix[ranked_positions]
    explanations = explainer.explain_batch(
        ranked_matrix, feature_pipeline.feature_names_, top_k=3
    )
    packages = build_all_evidence_packages(
        ranked_alerts, graph, explanations, output_path="data/evidence_packages.json"
    )
    print("[Phase 7] top explanation reasons:")
    for package in packages[:5]:
        print(f"- {package['wallet_id']}: {package['reason_sentence']}")
    return packages


def launch_dashboard():
    """Launch instructions for the Streamlit monitoring dashboard in Phase 8."""
    print("[Phase 8] Run `streamlit run dashboard/app.py` to launch the dashboard.")


if __name__ == "__main__":
    load_or_generate_dataset()
    transactions = ingest_data()
    geoip_lookup = GeoIPLookup()
    transactions = enrich_dataframe(transactions, geoip_lookup)
    transactions = flag_high_risk_geo(transactions)
    geoip_summary = transactions.attrs.get("geoip_summary", {})
    flagged_rows = int(
        transactions["src_high_risk_geo"].sum()
        + transactions["dst_high_risk_geo"].sum()
    )
    print(
        "[Phase 3] GeoIP enrichment: "
        f"{geoip_summary.get('unique_ips', 0)} unique IPs, "
        f"{geoip_summary.get('resolution_rate', 0.0):.1%} resolution rate, "
        f"{flagged_rows} high-risk endpoint flags"
    )
    geoip_lookup.close()
    graph, wallet_features = build_graph(transactions)
    feature_matrix, feature_table, feature_pipeline = engineer_features(
        wallet_features, transactions
    )
    ranked_alerts, evaluation, anomaly_detector = run_models(
        feature_matrix, feature_table, graph
    )
    generate_explanations(
        feature_matrix, feature_table, feature_pipeline, anomaly_detector,
        ranked_alerts, graph,
    )
    launch_dashboard()
