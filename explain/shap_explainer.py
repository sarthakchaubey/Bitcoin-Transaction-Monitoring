"""SHAP explanations for Isolation Forest anomaly scores."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)


class ShapExplainer:
    """Explain Isolation Forest outputs with TreeSHAP or a KernelSHAP fallback."""

    def __init__(self) -> None:
        """Initialize an unfitted explainability wrapper."""
        self.explainer = None
        self.model = None
        self.method: str | None = None
        self._predicts_risk = False

    def fit(self, model: Any, background_X: np.ndarray) -> "ShapExplainer":
        """Create a SHAP explainer using a capped random background sample.

        TreeSHAP is attempted first for Isolation Forest. If the installed SHAP
        version cannot explain that estimator, KernelSHAP is used with a small
        background and a risk-oriented prediction function instead.
        """
        try:
            import shap
        except ImportError as exc:
            raise ImportError("SHAP is required for explainability; install requirements.txt") from exc

        matrix = np.asarray(background_X, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("background_X must be a non-empty two-dimensional array")
        rng = np.random.default_rng(42)
        indices = rng.choice(matrix.shape[0], size=min(100, matrix.shape[0]), replace=False)
        background = matrix[indices]
        estimator = getattr(model, "model", model)
        self.model = model
        try:
            self.explainer = shap.TreeExplainer(estimator)
            self.method = "TreeSHAP"
            self._predicts_risk = False
            LOGGER.info("Using TreeSHAP for Isolation Forest explanations")
        except Exception as tree_error:
            LOGGER.info("TreeSHAP unavailable (%s); falling back to KernelSHAP", tree_error)

            def risk_prediction(values: np.ndarray) -> np.ndarray:
                decision = estimator.decision_function(np.asarray(values, dtype=float))
                return -np.asarray(decision)

            self.explainer = shap.KernelExplainer(risk_prediction, background)
            self.method = "KernelSHAP"
            self._predicts_risk = True
        return self

    @staticmethod
    def _extract_values(shap_values: Any) -> np.ndarray:
        """Normalize SHAP's array/list/Explanation return variants."""
        values = getattr(shap_values, "values", shap_values)
        if isinstance(values, list):
            values = values[0]
        return np.asarray(values, dtype=float)

    def explain_wallet(
        self,
        X_row: np.ndarray,
        feature_names: list[str],
        top_k: int = 3,
    ) -> list[dict]:
        """Return the strongest signed feature contributions for one wallet."""
        if self.explainer is None:
            raise RuntimeError("ShapExplainer must be fitted before explaining rows")
        row = np.asarray(X_row, dtype=float).reshape(1, -1)
        values = self._extract_values(self.explainer.shap_values(row)).reshape(-1)
        if not self._predicts_risk:
            # TreeSHAP explains the estimator's normality output; invert it so
            # positive values consistently mean increased anomaly risk.
            values = -values
        order = np.argsort(np.abs(values))[::-1][:max(0, top_k)]
        return [
            {
                "feature": feature_names[index] if index < len(feature_names) else f"feature_{index}",
                "shap_value": float(values[index]),
                "direction": "increases_risk" if values[index] >= 0 else "decreases_risk",
                "raw_value": float(row[0, index]),
            }
            for index in order
        ]

    def explain_batch(
        self,
        X: np.ndarray,
        feature_names: list[str],
        top_k: int = 3,
    ) -> list[list[dict]]:
        """Explain a batch of wallets and log progress every ten rows."""
        matrix = np.asarray(X, dtype=float)
        explanations = []
        for index, row in enumerate(matrix):
            explanations.append(self.explain_wallet(row, feature_names, top_k=top_k))
            if (index + 1) % 10 == 0 or index + 1 == len(matrix):
                LOGGER.info("Generated SHAP explanations for %d/%d wallets", index + 1, len(matrix))
        return explanations
