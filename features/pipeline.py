"""Reusable imputation, encoding, and scaling pipeline for wallet features."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class FeaturePipeline:
    """Fit-once preprocessing pipeline that produces stable ML feature matrices."""

    def __init__(self) -> None:
        """Initialize an unfitted pipeline."""
        self.numeric_columns_: list[str] = []
        self.categorical_columns_: list[str] = []
        self.numeric_imputer_: SimpleImputer | None = None
        self.categorical_imputer_: SimpleImputer | None = None
        self.encoder_: OneHotEncoder | None = None
        self.scaler_: StandardScaler | None = None
        self.feature_names_: list[str] = []
        self._fitted = False

    def fit(self, wallet_df: pd.DataFrame) -> FeaturePipeline:
        """Fit imputers, categorical encoding, and numeric scaling on training data.

        ``cluster_id`` is an identifier rather than a behavioral signal, so it
        is excluded. Numeric missing values use training-set medians, with zero
        as the fallback for an entirely missing column. Categorical missing
        values use an explicit ``__missing__`` category and unknown categories
        at inference are ignored by the one-hot encoder.
        """
        model_df = wallet_df.drop(columns=["cluster_id"], errors="ignore").copy()
        self.numeric_columns_ = [
            column for column in model_df.columns if pd.api.types.is_numeric_dtype(model_df[column])
        ]
        self.categorical_columns_ = [
            column for column in model_df.columns if column not in self.numeric_columns_
        ]

        if self.numeric_columns_:
            numeric_imputer = SimpleImputer(strategy="median", keep_empty_features=True)
            numeric_values = numeric_imputer.fit_transform(model_df[self.numeric_columns_])
            self.numeric_imputer_ = numeric_imputer
            self.scaler_ = StandardScaler().fit(numeric_values)
        else:
            self.numeric_imputer_ = None
            self.scaler_ = None

        if self.categorical_columns_:
            categorical_imputer = SimpleImputer(strategy="constant", fill_value="__missing__")
            try:
                encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            except TypeError:  # compatibility with older scikit-learn releases
                encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
            categorical_imputer.fit(model_df[self.categorical_columns_])
            categorical_values = categorical_imputer.transform(model_df[self.categorical_columns_])
            encoder.fit(categorical_values)
            self.categorical_imputer_ = categorical_imputer
            self.encoder_ = encoder
        else:
            self.categorical_imputer_ = None
            self.encoder_ = None

        numeric_names = list(self.numeric_columns_)
        categorical_names = (
            list(self.encoder_.get_feature_names_out(self.categorical_columns_))
            if self.encoder_ is not None else []
        )
        self.feature_names_ = numeric_names + categorical_names
        self._fitted = True
        return self

    def transform(self, wallet_df: pd.DataFrame) -> np.ndarray:
        """Transform new wallet rows using the already-fitted preprocessing objects."""
        if not self._fitted:
            raise RuntimeError("FeaturePipeline must be fitted before transform()")
        model_df = wallet_df.drop(columns=["cluster_id"], errors="ignore").reindex(
            columns=self.numeric_columns_ + self.categorical_columns_
        )
        blocks: list[np.ndarray] = []
        if self.numeric_columns_ and self.numeric_imputer_ is not None and self.scaler_ is not None:
            numeric_values = self.numeric_imputer_.transform(model_df[self.numeric_columns_])
            blocks.append(self.scaler_.transform(numeric_values))
        if self.categorical_columns_ and self.categorical_imputer_ is not None and self.encoder_ is not None:
            categorical_values = self.categorical_imputer_.transform(model_df[self.categorical_columns_])
            blocks.append(self.encoder_.transform(categorical_values))
        if not blocks:
            return np.empty((len(wallet_df), 0), dtype=float)
        return np.hstack(blocks).astype(float)

    def fit_transform(self, wallet_df: pd.DataFrame) -> np.ndarray:
        """Fit the pipeline on a training table and return its transformed matrix."""
        return self.fit(wallet_df).transform(wallet_df)

    def save(self, path: str | Path) -> None:
        """Serialize the fitted pipeline to a joblib file."""
        if not self._fitted:
            raise RuntimeError("Cannot save an unfitted FeaturePipeline")
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> FeaturePipeline:
        """Load a previously serialized pipeline from joblib."""
        pipeline = joblib.load(path)
        if not isinstance(pipeline, cls):
            raise TypeError(f"Expected a {cls.__name__} artifact, got {type(pipeline).__name__}")
        return pipeline
