"""
Example scripts demonstrating the truss optimizer tool.

Run with: python -m truss_optimizer.examples
"""

from __future__ import annotations

import numpy as np

from .core.truss_model import TrussModel, Material, SupportType
from .core.analysis import TrussAnalyzer
from .core.optimizer import TrussOptimizer, ObjectiveType, OptimizationConstraints


def example_simple_bridge():
    """Analyze and optimize a simple 6-node bridge truss."""
    print("=" * 60)
    print("Example: Simple Bridge Truss (Warren type)")
    print("=" * 60)

    steel = Material.steel()
    model = TrussModel("Simple Bridge")

    # Bottom chord: nodes 0-3
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0)
    model.add_node(2, 8.0, 0.0)
    model.add_node(3, 12.0, 0.0, SupportType.ROLLER_X)

    # Top chord: nodes 4-5
    model.add_node(4, 4.0, 3.0)
    model.add_node(5, 8.0, 3.0)

    # Elements (initial area = 50 cm²)
    area = 50e-4
    model.add_element(0, 0, 1, area, steel)  # bottom
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 2, 3, area, steel)
    model.add_element(3, 0, 4, area, steel)  # diagonals
    model.add_element(4, 4, 2, area, steel)
    model.add_element(5, 1, 5, area, steel)
    model.add_element(6, 5, 3, area, steel)
    model.add_element(7, 4, 5, area, steel)  # top chord
    model.add_element(8, 4, 1, area, steel)  # verticals
    model.add_element(9, 5, 2, area, steel)

    # Loads: 100 kN downward at nodes 1 and 2
    model.add_load(1, 0, -100e3)
    model.add_load(2, 0, -100e3)

    # 1) Analyze
    print("\n--- Initial Analysis ---")
    analyzer = TrussAnalyzer(model)
    result = analyzer.analyze()
    print(result.summary())

    # 2) Optimize
    print("\n--- Optimization (min weight, SF=1.5) ---")
    constraints = OptimizationConstraints(
        max_displacement=0.02,
        safety_factor=1.5,
        min_area=1e-4,
        max_area=0.05,
    )
    optimizer = TrussOptimizer(model, ObjectiveType.WEIGHT, constraints)
    opt_result = optimizer.optimize(verbose=False)
    print(opt_result.summary())
    print()
    print(opt_result.analysis.summary())

    # 3) Save
    model.save("truss_optimizer/data/simple_bridge.json")
    opt_result.optimized_model.save("truss_optimizer/data/simple_bridge_optimized.json")
    print("\nModels saved to truss_optimizer/data/")

    return model, result, opt_result


def example_roof_truss():
    """Analyze a Pratt roof truss."""
    print("\n" + "=" * 60)
    print("Example: Pratt Roof Truss")
    print("=" * 60)

    aluminum = Material.aluminum()
    model = TrussModel("Pratt Roof Truss")

    span = 10.0
    height = 2.5
    n_panels = 4
    pw = span / n_panels

    # Bottom chord
    for i in range(n_panels + 1):
        support = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE
        )
        model.add_node(i, i * pw, 0.0, support)

    # Top chord (pitched)
    for i in range(n_panels + 1):
        x = i * pw
        y = height * (1 - abs(2 * x / span - 1))  # triangular pitch
        model.add_node(n_panels + 1 + i, x, y)

    area = 30e-4
    eid = 0

    # Bottom chord
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, aluminum)
        eid += 1

    # Top chord
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, aluminum)
        eid += 1

    # Verticals
    for i in range(n_panels + 1):
        model.add_element(eid, i, n_panels + 1 + i, area, aluminum)
        eid += 1

    # Diagonals
    for i in range(n_panels):
        model.add_element(eid, i, n_panels + 2 + i, area, aluminum)
        eid += 1

    # Roof load at top chord nodes
    for i in range(1, n_panels):
        model.add_load(n_panels + 1 + i, 0, -20e3)

    # Analyze
    analyzer = TrussAnalyzer(model)
    result = analyzer.analyze()
    print(result.summary())

    # Optimize
    constraints = OptimizationConstraints(
        max_displacement=0.03,
        safety_factor=2.0,
        min_area=5e-5,
        max_area=0.02,
    )
    optimizer = TrussOptimizer(model, ObjectiveType.COST, constraints)
    opt_result = optimizer.optimize()
    print("\n--- Cost Optimization ---")
    print(opt_result.summary())

    return model, result, opt_result


def example_ml_pipeline():
    """Demonstrate the ML training and prediction pipeline."""
    print("\n" + "=" * 60)
    print("Example: ML Prediction Pipeline")
    print("=" * 60)

    from .ml.dataset import TrussDatasetGenerator
    from .ml.model import TrussPredictionModel

    # Generate small dataset
    print("\nGenerating 30 training samples (this may take a minute)...")
    gen = TrussDatasetGenerator(seed=123)
    X, y, feature_names = gen.generate_dataset(30, verbose=True)
    print(f"Dataset shape: X={X.shape}, y={y.shape}")

    if len(X) < 10:
        print("Not enough converged samples for training. Skipping ML demo.")
        return

    # Train model
    print("\nTraining neural network...")
    ml_model = TrussPredictionModel(hidden_layers=(64, 32), max_iter=500)
    result = ml_model.train(X, y, feature_names)
    print(result.summary())

    # Save model
    ml_model.save("truss_optimizer/data/truss_predictor.pkl")
    print("\nModel saved to truss_optimizer/data/truss_predictor.pkl")


if __name__ == "__main__":
    example_simple_bridge()
    example_roof_truss()
    try:
        example_ml_pipeline()
    except ImportError as e:
        print(f"\nSkipping ML example (missing dependency): {e}")
