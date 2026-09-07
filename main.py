"""Pipeline entry point for the Bitcoin transaction monitoring project."""

from features.build_features import build_feature_table
from features.pipeline import FeaturePipeline
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


def run_models():
    """Run anomaly detection and graph-based models in Phase 6."""
    print("[Phase 6] not yet implemented")


def generate_explanations():
    """Generate SHAP-based explanations for model results in Phase 7."""
    print("[Phase 7] not yet implemented")


def launch_dashboard():
    """Launch the Streamlit monitoring dashboard in Phase 8."""
    print("[Phase 8] not yet implemented")


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
    run_models()
    generate_explanations()
    launch_dashboard()
