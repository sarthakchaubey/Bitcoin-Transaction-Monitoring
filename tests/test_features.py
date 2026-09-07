"""Tests for Phase 5 derived features and reusable preprocessing."""

from __future__ import annotations

import numpy as np
import pandas as pd

from features.build_features import build_feature_table
from features.derived import add_derived_features
from features.pipeline import FeaturePipeline


def feature_fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return wallet and raw transaction fixtures with a known burst."""
    wallet_df = pd.DataFrame(
        {
            "cluster_id": [0, 1],
            "tx_count": [3, 3], "fan_in": [0, 1], "fan_out": [1, 0],
            "avg_amount": [1.0, 0.456], "std_amount": [0.0, np.nan],
            "total_amount": [3.0, 1.368], "avg_fee": [0.01, 0.02],
            "time_between_tx_mean": [600.0, 120.0], "time_between_tx_std": [0.0, 10.0],
            "distinct_ips": [1, 2], "distinct_countries": [1, 2],
            "shared_ip_with_n_wallets": [0, 1], "high_risk_geo_ratio": [0.0, 0.5],
            "script_type": ["p2pkh", "p2wpkh"],
        }
    )
    raw_tx_df = pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "txid": "a", "src_ip": "1.1.1.1",
             "input_addresses": ["A"], "output_addresses": ["X"],
             "input_amounts": [1.0], "output_amounts": [1.0]},
            {"timestamp": "2024-01-01T00:05:00Z", "txid": "b", "src_ip": "1.1.1.1",
             "input_addresses": ["A"], "output_addresses": ["X"],
             "input_amounts": [1.0], "output_amounts": [1.0]},
            {"timestamp": "2024-01-01T00:20:00Z", "txid": "c", "src_ip": "1.1.1.1",
             "input_addresses": ["A"], "output_addresses": ["X"],
             "input_amounts": [1.0], "output_amounts": [1.0]},
            {"timestamp": "2024-01-01T01:00:00Z", "txid": "d", "src_ip": "2.2.2.2",
             "input_addresses": ["B"], "output_addresses": ["Y"],
             "input_amounts": [0.123], "output_amounts": [0.123]},
            {"timestamp": "2024-01-01T01:04:00Z", "txid": "e", "src_ip": "2.2.2.2",
             "input_addresses": ["B"], "output_addresses": ["Y"],
             "input_amounts": [0.456], "output_amounts": [0.456]},
            {"timestamp": "2024-01-01T01:08:00Z", "txid": "f", "src_ip": "3.3.3.3",
             "input_addresses": ["B"], "output_addresses": ["Y"],
             "input_amounts": [0.789], "output_amounts": [0.789]},
        ]
    )
    return wallet_df, raw_tx_df


def test_amount_entropy_is_lower_for_repeated_amounts():
    wallet_df, raw_tx_df = feature_fixtures()

    result = add_derived_features(wallet_df, raw_tx_df).set_index("cluster_id")

    assert result.loc[0, "amount_entropy"] == 0.0
    assert result.loc[1, "amount_entropy"] > result.loc[0, "amount_entropy"]


def test_round_number_ratio_distinguishes_round_amounts():
    wallet_df, raw_tx_df = feature_fixtures()

    result = add_derived_features(wallet_df, raw_tx_df).set_index("cluster_id")

    assert result.loc[0, "round_number_ratio"] == 1.0
    assert result.loc[1, "round_number_ratio"] == 0.0


def test_burst_score_counts_ten_minute_transaction_burst():
    wallet_df, raw_tx_df = feature_fixtures()

    result = add_derived_features(wallet_df, raw_tx_df).set_index("cluster_id")

    assert result.loc[0, "burst_score"] == 2.0
    assert result.loc[1, "burst_score"] == 3.0


def test_feature_pipeline_is_stable_for_repeated_transforms():
    wallet_df, raw_tx_df = feature_fixtures()
    table = build_feature_table(wallet_df, raw_tx_df)

    pipeline = FeaturePipeline()
    first = pipeline.fit_transform(table)
    second = pipeline.transform(table)

    assert first.shape == second.shape
    assert first.shape[0] == len(table)
    assert first.shape[1] == len(pipeline.feature_names_)
    np.testing.assert_allclose(first, second)


def test_feature_pipeline_joblib_round_trip(tmp_path):
    wallet_df, raw_tx_df = feature_fixtures()
    table = build_feature_table(wallet_df, raw_tx_df)
    pipeline = FeaturePipeline()
    expected = pipeline.fit_transform(table)
    path = tmp_path / "feature_pipeline.joblib"

    pipeline.save(path)
    restored = FeaturePipeline.load(path)

    np.testing.assert_allclose(expected, restored.transform(table))
    assert restored.feature_names_ == pipeline.feature_names_
