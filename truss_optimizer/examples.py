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


def example_cost_vs_weight():
    """Compare cost vs weight optimization on the same bridge truss."""
    print("\n" + "=" * 60)
    print("Example: Cost vs Weight Comparison")
    print("=" * 60)

    from .core.optimizer import TrussComparison

    steel = Material.steel()
    model = TrussModel("Cost vs Weight Bridge")

    # 8-node bridge with mixed materials to make cost/weight tradeoff interesting
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 3.0, 0.0)
    model.add_node(2, 6.0, 0.0)
    model.add_node(3, 9.0, 0.0, SupportType.ROLLER_X)
    model.add_node(4, 1.5, 2.5)
    model.add_node(5, 4.5, 2.5)
    model.add_node(6, 7.5, 2.5)

    area = 40e-4
    aluminum = Material.aluminum()

    # Bottom chord (steel - cheap but heavy)
    model.add_element(0, 0, 1, area, steel)
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 2, 3, area, steel)
    # Top chord (aluminum - light but expensive)
    model.add_element(3, 4, 5, area, aluminum)
    model.add_element(4, 5, 6, area, aluminum)
    # Diagonals (steel)
    model.add_element(5, 0, 4, area, steel)
    model.add_element(6, 4, 1, area, steel)
    model.add_element(7, 1, 5, area, steel)
    model.add_element(8, 5, 2, area, steel)
    model.add_element(9, 2, 6, area, steel)
    model.add_element(10, 6, 3, area, steel)

    model.add_load(1, 0, -80e3)
    model.add_load(2, 0, -80e3)

    # Run comparison
    constraints = OptimizationConstraints(
        max_displacement=0.03,
        safety_factor=1.5,
        min_area=1e-4,
        max_area=0.05,
    )
    comparison = TrussComparison(model, constraints)

    print("\nRunning weight vs cost optimization...")
    result = comparison.compare()
    print(result.summary())

    # Pareto front
    print("\nGenerating Pareto front (7 points)...")
    points = comparison.pareto_front(n_points=7)
    print(TrussComparison.pareto_summary(points))

    return result, points


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


def example_shape_optimization():
    """Demonstrate shape optimization: move nodes + size members for min cost."""
    print("\n" + "=" * 60)
    print("Example: Shape Optimization (Min Cost)")
    print("=" * 60)

    from .core.advanced import ShapeOptimizer, ShapeOptConstraints

    steel = Material.steel()
    model = TrussModel("Shape Opt Bridge")

    # Simple bridge: bottom chord fixed, top chord nodes can move
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0)
    model.add_node(2, 8.0, 0.0)
    model.add_node(3, 12.0, 0.0, SupportType.ROLLER_X)
    model.add_node(4, 4.0, 3.0)   # free - can move
    model.add_node(5, 8.0, 3.0)   # free - can move

    area = 40e-4
    model.add_element(0, 0, 1, area, steel)
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 2, 3, area, steel)
    model.add_element(3, 0, 4, area, steel)
    model.add_element(4, 4, 2, area, steel)
    model.add_element(5, 1, 5, area, steel)
    model.add_element(6, 5, 3, area, steel)
    model.add_element(7, 4, 5, area, steel)
    model.add_element(8, 4, 1, area, steel)
    model.add_element(9, 5, 2, area, steel)

    model.add_load(1, 0, -100e3)
    model.add_load(2, 0, -100e3)

    print(f"\nInitial design: cost=${model.total_cost:.2f}, weight={model.total_weight:.2f} kg")
    print(f"Initial node 4 position: ({model.nodes[4].x}, {model.nodes[4].y})")
    print(f"Initial node 5 position: ({model.nodes[5].x}, {model.nodes[5].y})")

    constraints = ShapeOptConstraints(
        max_displacement=0.03,
        safety_factor=1.5,
        min_area=1e-4,
        max_area=0.05,
        max_node_move_x=3.0,
        max_node_move_y=2.0,
        min_height=1.0,
    )

    optimizer = ShapeOptimizer(model, constraints)
    result = optimizer.optimize(max_iterations=300)
    print(result.summary())

    return result


def example_multi_load_case():
    """Demonstrate multi-load-case optimization: dead + wind + live."""
    print("\n" + "=" * 60)
    print("Example: Multi-Load-Case Optimization (Min Cost)")
    print("=" * 60)

    from .core.advanced import MultiLoadCaseOptimizer, MultiLoadConstraints, LoadCase
    from .core.truss_model import Load

    steel = Material.steel()
    model = TrussModel("Multi-Load Bridge")

    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0)
    model.add_node(2, 8.0, 0.0)
    model.add_node(3, 12.0, 0.0, SupportType.ROLLER_X)
    model.add_node(4, 4.0, 3.0)
    model.add_node(5, 8.0, 3.0)

    area = 40e-4
    model.add_element(0, 0, 1, area, steel)
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 2, 3, area, steel)
    model.add_element(3, 0, 4, area, steel)
    model.add_element(4, 4, 2, area, steel)
    model.add_element(5, 1, 5, area, steel)
    model.add_element(6, 5, 3, area, steel)
    model.add_element(7, 4, 5, area, steel)
    model.add_element(8, 4, 1, area, steel)
    model.add_element(9, 5, 2, area, steel)

    # Placeholder load for validation
    model.add_load(1, 0, -50e3)

    # Define load cases
    load_cases = [
        LoadCase("1.4D (Dead Only)", [
            Load(1, 0, -70e3),
            Load(2, 0, -70e3),
        ]),
        LoadCase("1.2D + 1.6L", [
            Load(1, 0, -60e3 + -128e3),   # dead + live
            Load(2, 0, -60e3 + -128e3),
        ]),
        LoadCase("1.2D + W (Left)", [
            Load(1, 0, -60e3),
            Load(2, 0, -60e3),
            Load(4, 30e3, -10e3),   # wind on top chord
            Load(5, 30e3, -10e3),
        ]),
        LoadCase("1.2D + W (Right)", [
            Load(1, 0, -60e3),
            Load(2, 0, -60e3),
            Load(4, -30e3, -10e3),  # wind from other direction
            Load(5, -30e3, -10e3),
        ]),
        LoadCase("0.9D + W (Uplift)", [
            Load(1, 0, -45e3),
            Load(2, 0, -45e3),
            Load(4, 30e3, 15e3),    # wind uplift
            Load(5, 30e3, 15e3),
        ]),
    ]

    print(f"\nLoad cases: {len(load_cases)}")
    for lc in load_cases:
        print(f"  - {lc.name}: {len(lc.loads)} loads")

    constraints = MultiLoadConstraints(
        max_displacement=0.03,
        safety_factor=1.5,
        min_area=1e-4,
        max_area=0.05,
    )

    optimizer = MultiLoadCaseOptimizer(model, load_cases, constraints)
    result = optimizer.optimize(max_iterations=300)
    print(result.summary())

    return result


if __name__ == "__main__":
    example_simple_bridge()
    example_roof_truss()
    example_cost_vs_weight()
    example_shape_optimization()
    example_multi_load_case()
    try:
        example_ml_pipeline()
    except ImportError as e:
        print(f"\nSkipping ML example (missing dependency): {e}")
