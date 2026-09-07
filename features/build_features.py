"""Orchestration for the human-readable Phase 5 feature table."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .derived import add_derived_features


def build_feature_table(wallet_df: pd.DataFrame, raw_tx_df: pd.DataFrame) -> pd.DataFrame:
    """Add derived signals and return a finite, dashboard-ready feature table."""
    result = add_derived_features(wallet_df, raw_tx_df)
    result = result.replace([np.inf, -np.inf], np.nan)
    numeric_columns = result.select_dtypes(include=[np.number]).columns
    result[numeric_columns] = result[numeric_columns].fillna(0.0)
    categorical_columns = result.select_dtypes(include=["object", "string", "category"]).columns
    result[categorical_columns] = result[categorical_columns].fillna("__missing__")
    if np.isinf(result.select_dtypes(include=[np.number]).to_numpy()).any():
        raise ValueError("Feature table contains infinite numeric values")
    if result[numeric_columns].isna().any().any() or result[categorical_columns].isna().any().any():
        raise ValueError("Feature table contains unexpected missing values")
    return result
