"""
Synthetic dataset generator for training the truss ML model.

Generates random truss topologies (Warren, Pratt, Howe, K-truss),
runs optimization on each, and collects features + optimal areas
for supervised learning.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from ..core.truss_model import TrussModel, Material, SupportType
from ..core.optimizer import TrussOptimizer, ObjectiveType, OptimizationConstraints
from .model import TrussPredictionModel


class TrussDatasetGenerator:
    """Generates training datasets by creating random trusses and optimizing them."""

    TOPOLOGIES = ["warren", "pratt", "howe", "simple"]

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    def generate_warren_truss(self, n_panels: int, span: float, height: float,
                               material: Material, load: float) -> TrussModel:
        """Generate a Warren truss (zigzag diagonals, no verticals)."""
        model = TrussModel(f"Warren_{n_panels}p")
        panel_width = span / n_panels

        # Bottom chord nodes
        for i in range(n_panels + 1):
            support = SupportType.PIN if i == 0 else (
                SupportType.ROLLER_X if i == n_panels else SupportType.FREE
            )
            model.add_node(i, i * panel_width, 0.0, support)

        # Top chord nodes
        for i in range(n_panels):
            model.add_node(n_panels + 1 + i, (i + 0.5) * panel_width, height)

        area = 0.005  # initial area
        eid = 0

        # Bottom chord
        for i in range(n_panels):
            model.add_element(eid, i, i + 1, area, material)
            eid += 1

        # Diagonals (Warren pattern)
        for i in range(n_panels):
            top_node = n_panels + 1 + i
            model.add_element(eid, i, top_node, area, material)
            eid += 1
            model.add_element(eid, top_node, i + 1, area, material)
            eid += 1

        # Top chord
        for i in range(n_panels - 1):
            model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, material)
            eid += 1

        # Loads at bottom chord nodes (except supports)
        for i in range(1, n_panels):
            model.add_load(i, 0, -load)

        return model

    def generate_pratt_truss(self, n_panels: int, span: float, height: float,
                              material: Material, load: float) -> TrussModel:
        """Generate a Pratt truss (verticals + diagonals slanting toward center)."""
        model = TrussModel(f"Pratt_{n_panels}p")
        panel_width = span / n_panels

        # Bottom chord
        for i in range(n_panels + 1):
            support = SupportType.PIN if i == 0 else (
                SupportType.ROLLER_X if i == n_panels else SupportType.FREE
            )
            model.add_node(i, i * panel_width, 0.0, support)

        # Top chord
        for i in range(n_panels + 1):
            model.add_node(n_panels + 1 + i, i * panel_width, height)

        area = 0.005
        eid = 0

        # Bottom chord
        for i in range(n_panels):
            model.add_element(eid, i, i + 1, area, material)
            eid += 1

        # Top chord
        for i in range(n_panels):
            model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, material)
            eid += 1

        # Verticals
        for i in range(n_panels + 1):
            model.add_element(eid, i, n_panels + 1 + i, area, material)
            eid += 1

        # Diagonals (Pratt pattern: diagonals slope toward center)
        mid = n_panels / 2
        for i in range(n_panels):
            if i < mid:
                model.add_element(eid, i, n_panels + 2 + i, area, material)
            else:
                model.add_element(eid, i + 1, n_panels + 1 + i, area, material)
            eid += 1

        # Loads
        for i in range(1, n_panels):
            model.add_load(i, 0, -load)

        return model

    def generate_howe_truss(self, n_panels: int, span: float, height: float,
                             material: Material, load: float) -> TrussModel:
        """Generate a Howe truss (verticals + diagonals slanting away from center)."""
        model = TrussModel(f"Howe_{n_panels}p")
        panel_width = span / n_panels

        # Bottom chord
        for i in range(n_panels + 1):
            support = SupportType.PIN if i == 0 else (
                SupportType.ROLLER_X if i == n_panels else SupportType.FREE
            )
            model.add_node(i, i * panel_width, 0.0, support)

        # Top chord
        for i in range(n_panels + 1):
            model.add_node(n_panels + 1 + i, i * panel_width, height)

        area = 0.005
        eid = 0

        # Bottom chord
        for i in range(n_panels):
            model.add_element(eid, i, i + 1, area, material)
            eid += 1

        # Top chord
        for i in range(n_panels):
            model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, material)
            eid += 1

        # Verticals
        for i in range(n_panels + 1):
            model.add_element(eid, i, n_panels + 1 + i, area, material)
            eid += 1

        # Diagonals (Howe pattern: opposite of Pratt)
        mid = n_panels / 2
        for i in range(n_panels):
            if i < mid:
                model.add_element(eid, i + 1, n_panels + 1 + i, area, material)
            else:
                model.add_element(eid, i, n_panels + 2 + i, area, material)
            eid += 1

        # Loads
        for i in range(1, n_panels):
            model.add_load(i, 0, -load)

        return model

    def generate_simple_truss(self, span: float, height: float,
                               material: Material, load: float) -> TrussModel:
        """Generate a simple 3-node triangle truss for basic testing."""
        model = TrussModel("Simple_triangle")
        model.add_node(0, 0.0, 0.0, SupportType.PIN)
        model.add_node(1, span, 0.0, SupportType.ROLLER_X)
        model.add_node(2, span / 2, height)
        area = 0.005
        model.add_element(0, 0, 2, area, material)
        model.add_element(1, 2, 1, area, material)
        model.add_element(2, 0, 1, area, material)
        model.add_load(2, 0, -load)
        return model

    def generate_random_truss(self) -> TrussModel:
        """Generate a random truss with random topology, dimensions, and loading."""
        topology = self.rng.choice(self.TOPOLOGIES)
        span = self.rng.uniform(5.0, 30.0)
        height = self.rng.uniform(1.0, span * 0.4)
        load = self.rng.uniform(10e3, 500e3)

        materials = [Material.steel(), Material.aluminum(), Material.timber()]
        material = self.rng.choice(materials)

        if topology == "simple":
            return self.generate_simple_truss(span, height, material, load)

        n_panels = self.rng.randint(3, 8)

        if topology == "warren":
            return self.generate_warren_truss(n_panels, span, height, material, load)
        elif topology == "pratt":
            return self.generate_pratt_truss(n_panels, span, height, material, load)
        else:
            return self.generate_howe_truss(n_panels, span, height, material, load)

    def generate_dataset(self, n_samples: int, verbose: bool = False,
                         constraints: Optional[OptimizationConstraints] = None
                         ) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Generate a dataset of (features, optimal_areas) pairs.

        Returns:
            X: feature matrix (n_samples, n_features)
            y: optimal areas matrix (n_samples, max_elements)
            feature_names: list of feature column names
        """
        constraints = constraints or OptimizationConstraints()

        all_features: list[dict[str, float]] = []
        all_areas: list[list[float]] = []
        max_elements = 0

        successes = 0
        attempts = 0

        while successes < n_samples:
            attempts += 1
            if attempts > n_samples * 5:
                print(f"Warning: Stopping after {attempts} attempts ({successes} successes)")
                break

            truss = self.generate_random_truss()

            try:
                optimizer = TrussOptimizer(
                    truss, ObjectiveType.WEIGHT, constraints
                )
                result = optimizer.optimize(max_iterations=100)

                if not result.converged:
                    continue

                features = TrussPredictionModel.extract_features(truss)
                areas = [result.optimized_areas[eid]
                         for eid in sorted(result.optimized_areas.keys())]

                all_features.append(features)
                all_areas.append(areas)
                max_elements = max(max_elements, len(areas))
                successes += 1

                if verbose and successes % 50 == 0:
                    print(f"  Generated {successes}/{n_samples} samples "
                          f"({attempts} attempts)")

            except (ValueError, np.linalg.LinAlgError):
                continue

        # Build uniform feature matrix
        all_feature_keys = sorted(
            set().union(*(f.keys() for f in all_features))
        )

        X = np.zeros((len(all_features), len(all_feature_keys)))
        for i, feat in enumerate(all_features):
            for j, key in enumerate(all_feature_keys):
                X[i, j] = feat.get(key, 0.0)

        # Pad areas to max_elements
        y = np.zeros((len(all_areas), max_elements))
        for i, areas in enumerate(all_areas):
            y[i, :len(areas)] = areas

        return X, y, all_feature_keys

    def save_dataset(self, X: np.ndarray, y: np.ndarray,
                     feature_names: list[str], path: str | Path) -> None:
        """Save dataset to disk."""
        path = Path(path)
        np.savez(path, X=X, y=y)
        meta_path = path.with_suffix(".meta.json")
        with open(meta_path, "w") as f:
            json.dump({"feature_names": feature_names}, f, indent=2)

    @staticmethod
    def load_dataset(path: str | Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
        """Load dataset from disk."""
        path = Path(path)
        data = np.load(path)
        meta_path = path.with_suffix("").with_suffix(".meta.json")
        with open(meta_path) as f:
            meta = json.load(f)
        return data["X"], data["y"], meta["feature_names"]
