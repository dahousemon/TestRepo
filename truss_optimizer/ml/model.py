"""
ML model for fast prediction of optimal truss cross-sections.

Uses a neural network (scikit-learn MLPRegressor) trained on optimization
results to predict optimal areas given truss features, bypassing the
expensive scipy optimization loop.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

try:
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from ..core.truss_model import TrussModel
from ..core.analysis import TrussAnalyzer


def _require_sklearn():
    if not HAS_SKLEARN:
        raise ImportError(
            "scikit-learn is required for ML features. "
            "Install with: pip install scikit-learn"
        )


@dataclass
class TrainingResult:
    train_mse: float
    test_mse: float
    train_r2: float
    test_r2: float
    n_train: int
    n_test: int
    feature_names: list[str]

    def summary(self) -> str:
        return (
            f"=== ML Training Results ===\n"
            f"Training samples: {self.n_train}\n"
            f"Test samples:     {self.n_test}\n"
            f"Train MSE:        {self.train_mse:.8f}\n"
            f"Test MSE:         {self.test_mse:.8f}\n"
            f"Train R²:         {self.train_r2:.4f}\n"
            f"Test R²:          {self.test_r2:.4f}\n"
            f"Features:         {len(self.feature_names)}"
        )


class TrussPredictionModel:
    """Neural network model that predicts optimal cross-sectional areas."""

    def __init__(self, hidden_layers: tuple[int, ...] = (128, 64, 32),
                 max_iter: int = 1000, learning_rate: float = 0.001):
        _require_sklearn()
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            activation="relu",
            solver="adam",
            learning_rate_init=learning_rate,
            max_iter=max_iter,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
            verbose=False,
        )
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.is_trained = False
        self.feature_names: list[str] = []
        self.n_elements: int = 0

    @staticmethod
    def extract_features(model: TrussModel) -> dict[str, float]:
        """Extract features from a TrussModel for ML prediction.

        Features include:
        - Per-element: length, angle, material properties
        - Global: total span, height, load magnitudes, node count
        - Topology: connectivity patterns
        """
        nodes = model.nodes
        elements = model.elements
        elem_ids = sorted(elements.keys())

        features = {}

        # Global features
        xs = [n.x for n in nodes.values()]
        ys = [n.y for n in nodes.values()]
        features["span"] = max(xs) - min(xs) if xs else 0
        features["height"] = max(ys) - min(ys) if ys else 0
        features["n_nodes"] = len(nodes)
        features["n_elements"] = len(elements)
        features["n_loads"] = len(model.loads)
        features["n_supports"] = len(model.get_constrained_dofs())

        # Total load magnitude
        total_fx = sum(abs(l.fx) for l in model.loads)
        total_fy = sum(abs(l.fy) for l in model.loads)
        features["total_load_x"] = total_fx
        features["total_load_y"] = total_fy
        features["total_load_mag"] = np.sqrt(total_fx**2 + total_fy**2)

        # Per-element features
        for i, eid in enumerate(elem_ids):
            elem = elements[eid]
            features[f"elem_{i}_length"] = elem.length(nodes)
            features[f"elem_{i}_angle"] = elem.angle(nodes)
            features[f"elem_{i}_E"] = elem.material.E
            features[f"elem_{i}_density"] = elem.material.density
            features[f"elem_{i}_yield"] = elem.material.yield_stress

        return features

    def train(self, X: np.ndarray, y: np.ndarray,
              feature_names: Optional[list[str]] = None,
              test_size: float = 0.2) -> TrainingResult:
        """Train the model on feature matrix X and target areas y."""
        _require_sklearn()

        self.feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]
        self.n_elements = y.shape[1] if y.ndim > 1 else 1

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        X_train_scaled = self.scaler_X.fit_transform(X_train)
        y_train_scaled = self.scaler_y.fit_transform(y_train)
        X_test_scaled = self.scaler_X.transform(X_test)

        self.model.fit(X_train_scaled, y_train_scaled)

        y_train_pred = self.scaler_y.inverse_transform(
            self.model.predict(X_train_scaled)
        )
        y_test_pred = self.scaler_y.inverse_transform(
            self.model.predict(X_test_scaled)
        )

        self.is_trained = True

        return TrainingResult(
            train_mse=float(mean_squared_error(y_train, y_train_pred)),
            test_mse=float(mean_squared_error(y_test, y_test_pred)),
            train_r2=float(r2_score(y_train, y_train_pred)),
            test_r2=float(r2_score(y_test, y_test_pred)),
            n_train=len(X_train),
            n_test=len(X_test),
            feature_names=self.feature_names,
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict optimal areas for given feature vectors."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")
        X_scaled = self.scaler_X.transform(X)
        y_scaled = self.model.predict(X_scaled)
        return self.scaler_y.inverse_transform(y_scaled)

    def predict_for_model(self, truss: TrussModel) -> dict[int, float]:
        """Predict optimal areas for a TrussModel and return a dict of elem_id -> area."""
        features = self.extract_features(truss)
        # Ensure feature order matches training
        X = np.array([[features.get(name, 0.0) for name in self.feature_names]])
        areas = self.predict(X)[0]

        elem_ids = sorted(truss.elements.keys())
        return {eid: max(float(areas[i]), 1e-5) for i, eid in enumerate(elem_ids)}

    def save(self, path: str | Path) -> None:
        """Save the trained model to disk."""
        path = Path(path)
        data = {
            "model": self.model,
            "scaler_X": self.scaler_X,
            "scaler_y": self.scaler_y,
            "feature_names": self.feature_names,
            "n_elements": self.n_elements,
            "is_trained": self.is_trained,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path: str | Path) -> TrussPredictionModel:
        """Load a trained model from disk."""
        _require_sklearn()
        with open(path, "rb") as f:
            data = pickle.load(f)
        instance = cls.__new__(cls)
        instance.model = data["model"]
        instance.scaler_X = data["scaler_X"]
        instance.scaler_y = data["scaler_y"]
        instance.feature_names = data["feature_names"]
        instance.n_elements = data["n_elements"]
        instance.is_trained = data["is_trained"]
        return instance
