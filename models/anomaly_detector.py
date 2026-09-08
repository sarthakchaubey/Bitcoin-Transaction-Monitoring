"""Unsupervised anomaly detectors for wallet feature matrices."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest


def _normalize_scores(values: np.ndarray) -> np.ndarray:
    """Convert arbitrary anomaly values to a stable 0-100 range."""
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    minimum, maximum = np.nanmin(values), np.nanmax(values)
    if np.isclose(minimum, maximum):
        return np.zeros(values.shape, dtype=float)
    return 100.0 * (values - minimum) / (maximum - minimum)


class AnomalyDetector:
    """Isolation Forest wrapper with normalized, higher-is-riskier scores."""

    def __init__(
        self,
        contamination: str | float = "auto",
        random_state: int = 42,
        **kwargs: Any,
    ) -> None:
        """Initialize Isolation Forest configuration.

        ``contamination`` roughly controls the expected fraction of flagged
        wallets. ``auto`` is a robust starting point when labels are unavailable;
        it can later be tuned against the evaluation ground truth.
        """
        self.contamination = contamination
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            **kwargs,
        )
        self._fitted = False

    def fit(self, X: np.ndarray) -> AnomalyDetector:
        """Train Isolation Forest on the scaled feature matrix."""
        matrix = np.asarray(X, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("X must be a non-empty two-dimensional array")
        self.model.fit(matrix)
        self._fitted = True
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores from 0 to 100, with higher meaning riskier."""
        if not self._fitted:
            raise RuntimeError("AnomalyDetector must be fitted before score()")
        # Isolation Forest's decision_function is lower for more anomalous rows.
        return _normalize_scores(-self.model.decision_function(np.asarray(X, dtype=float)))

    def save(self, path: str | Path) -> None:
        """Save the fitted Isolation Forest wrapper with joblib."""
        if not self._fitted:
            raise RuntimeError("Cannot save an unfitted AnomalyDetector")
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str | Path) -> AnomalyDetector:
        """Load a previously saved Isolation Forest wrapper."""
        detector = joblib.load(path)
        if not isinstance(detector, cls):
            raise TypeError(f"Expected {cls.__name__}, got {type(detector).__name__}")
        return detector


class AutoencoderDetector:
    """Optional PyTorch reconstruction-error detector."""

    def __init__(
        self,
        hidden_dim: int = 16,
        latent_dim: int = 8,
        epochs: int = 50,
        learning_rate: float = 1e-3,
        random_state: int = 42,
    ) -> None:
        """Configure a small three-layer encoder/decoder autoencoder."""
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.model = None
        self.input_dim: int | None = None
        self._fitted = False

    def _build_model(self, input_dim: int):
        """Create the torch network lazily so Isolation Forest users need no torch import."""
        try:
            from torch import nn
        except ImportError as exc:
            raise ImportError("PyTorch is required to use AutoencoderDetector") from exc
        return nn.Sequential(
            nn.Linear(input_dim, self.hidden_dim), nn.ReLU(),
            nn.Linear(self.hidden_dim, self.latent_dim), nn.ReLU(),
            nn.Linear(self.latent_dim, self.hidden_dim), nn.ReLU(),
            nn.Linear(self.hidden_dim, input_dim),
        )

    def fit(self, X: np.ndarray) -> AutoencoderDetector:
        """Train the autoencoder to reconstruct normal feature vectors."""
        import torch

        torch.manual_seed(self.random_state)
        matrix = np.asarray(X, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError("X must be a non-empty two-dimensional array")
        self.input_dim = matrix.shape[1]
        input_dim = self.input_dim
        if input_dim is None:
            raise RuntimeError("Unable to determine autoencoder input dimension")
        self.model = self._build_model(input_dim)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        loss_function = torch.nn.MSELoss()
        tensor = torch.from_numpy(matrix)
        self.model.train()
        for _ in range(self.epochs):
            optimizer.zero_grad()
            loss = loss_function(self.model(tensor), tensor)
            loss.backward()
            optimizer.step()
        self._fitted = True
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Return normalized reconstruction-error scores from 0 to 100."""
        import torch

        if not self._fitted or self.model is None:
            raise RuntimeError("AutoencoderDetector must be fitted before score()")
        self.model.eval()
        with torch.no_grad():
            tensor = torch.from_numpy(np.asarray(X, dtype=np.float32))
            errors = torch.mean((self.model(tensor) - tensor) ** 2, dim=1).numpy()
        return _normalize_scores(errors)

    def save(self, path: str | Path) -> None:
        """Save autoencoder weights and configuration with torch.save."""
        import torch

        if not self._fitted or self.model is None or self.input_dim is None:
            raise RuntimeError("Cannot save an unfitted AutoencoderDetector")
        torch.save({
            "config": self.__dict__ | {"model": None},
            "state_dict": self.model.state_dict(),
        }, path)

    @classmethod
    def load(cls, path: str | Path) -> AutoencoderDetector:
        """Load an autoencoder detector from a torch checkpoint."""
        import torch

        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        detector = cls(**{
            key: checkpoint["config"][key]
            for key in ("hidden_dim", "latent_dim", "epochs", "learning_rate", "random_state")
        })
        detector.input_dim = checkpoint["config"]["input_dim"]
        if detector.input_dim is None:
            raise ValueError("Autoencoder checkpoint is missing input_dim")
        detector.model = detector._build_model(detector.input_dim)
        detector.model.load_state_dict(checkpoint["state_dict"])
        detector._fitted = True
        return detector
