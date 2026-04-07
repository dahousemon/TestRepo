"""
Command-line interface for the Truss Optimizer tool.

Usage:
    python -m truss_optimizer analyze <model.json>
    python -m truss_optimizer optimize <model.json> [--objective weight|cost]
    python -m truss_optimizer generate-data <n_samples> <output_path>
    python -m truss_optimizer train <dataset.npz> <model_output.pkl>
    python -m truss_optimizer predict <model.json> <trained_model.pkl>
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from .core.truss_model import TrussModel
from .core.analysis import TrussAnalyzer
from .core.optimizer import TrussOptimizer, ObjectiveType, OptimizationConstraints


def cmd_analyze(args):
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")
    analyzer = TrussAnalyzer(model)
    result = analyzer.analyze()
    print(result.summary())


def cmd_optimize(args):
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")

    objective = ObjectiveType(args.objective)
    constraints = OptimizationConstraints(
        max_displacement=args.max_disp,
        safety_factor=args.safety_factor,
    )

    optimizer = TrussOptimizer(model, objective, constraints)
    print(f"Optimizing for minimum {args.objective}...")
    result = optimizer.optimize(verbose=args.verbose)
    print(result.summary())
    print()
    print(result.analysis.summary())

    if args.output:
        result.optimized_model.save(args.output)
        print(f"\nOptimized model saved to {args.output}")


def cmd_generate_data(args):
    from .ml.dataset import TrussDatasetGenerator

    gen = TrussDatasetGenerator(seed=args.seed)
    print(f"Generating {args.n_samples} training samples...")
    X, y, feature_names = gen.generate_dataset(
        args.n_samples, verbose=True,
    )
    gen.save_dataset(X, y, feature_names, args.output)
    print(f"Dataset saved: X={X.shape}, y={y.shape}")
    print(f"Features: {len(feature_names)}")


def cmd_train(args):
    from .ml.dataset import TrussDatasetGenerator
    from .ml.model import TrussPredictionModel

    X, y, feature_names = TrussDatasetGenerator.load_dataset(args.dataset)
    print(f"Loaded dataset: X={X.shape}, y={y.shape}")

    model = TrussPredictionModel(
        hidden_layers=tuple(args.layers),
        max_iter=args.max_iter,
    )
    result = model.train(X, y, feature_names)
    print(result.summary())

    model.save(args.output)
    print(f"\nModel saved to {args.output}")


def cmd_compare(args):
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")

    from .core.optimizer import TrussComparison
    constraints = OptimizationConstraints(
        max_displacement=args.max_disp,
        safety_factor=args.safety_factor,
    )

    comparison = TrussComparison(model, constraints)

    print("Running weight vs cost comparison...")
    result = comparison.compare(verbose=args.verbose)
    print(result.summary())

    if args.pareto:
        print(f"\nGenerating Pareto front ({args.pareto_points} points)...")
        points = comparison.pareto_front(n_points=args.pareto_points)
        print(TrussComparison.pareto_summary(points))


def cmd_shape_opt(args):
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")

    from .core.advanced import ShapeOptimizer, ShapeOptConstraints
    constraints = ShapeOptConstraints(
        max_displacement=args.max_disp,
        safety_factor=args.safety_factor,
        max_node_move_x=args.max_move_x,
        max_node_move_y=args.max_move_y,
        min_height=args.min_height,
    )

    optimizer = ShapeOptimizer(model, constraints)
    print("Running shape optimization (min cost, moving nodes + sizing)...")
    result = optimizer.optimize(verbose=args.verbose)
    print(result.summary())

    if args.output:
        result.optimized_model.save(args.output)
        print(f"\nOptimized model saved to {args.output}")


def cmd_multi_load(args):
    import json
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")

    from .core.advanced import MultiLoadCaseOptimizer, MultiLoadConstraints, LoadCase
    from .core.truss_model import Load

    # Load cases from JSON file
    with open(args.load_cases) as f:
        cases_data = json.load(f)

    load_cases = []
    for case in cases_data:
        loads = [Load(node_id=l["node_id"], fx=l.get("fx", 0), fy=l.get("fy", 0))
                 for l in case["loads"]]
        load_cases.append(LoadCase(case["name"], loads))

    print(f"Load cases: {len(load_cases)}")
    for lc in load_cases:
        print(f"  - {lc.name}: {len(lc.loads)} loads")

    constraints = MultiLoadConstraints(
        max_displacement=args.max_disp,
        safety_factor=args.safety_factor,
    )

    optimizer = MultiLoadCaseOptimizer(model, load_cases, constraints)
    print("Running multi-load-case optimization (min cost)...")
    result = optimizer.optimize(verbose=args.verbose)
    print(result.summary())

    if args.output:
        result.optimized_model.save(args.output)
        print(f"\nOptimized model saved to {args.output}")


def cmd_genetic(args):
    model = TrussModel.load(args.model)
    print(f"Loaded: {model}")

    from .core.genetic import GeneticOptimizer, GAConfig
    config = GAConfig(
        population_size=args.population,
        generations=args.generations,
        max_displacement=args.max_disp,
        safety_factor=args.safety_factor,
        allow_topology_mutation=args.topology,
    )

    optimizer = GeneticOptimizer(model, config)
    print(f"Running genetic algorithm (pop={args.population}, gen={args.generations}, "
          f"topology={'on' if args.topology else 'off'})...")
    result = optimizer.optimize(verbose=args.verbose, seed=args.seed)
    print(result.summary())

    if args.output:
        result.best_model.save(args.output)
        print(f"\nOptimized model saved to {args.output}")


def cmd_predict(args):
    from .ml.model import TrussPredictionModel

    truss = TrussModel.load(args.model)
    ml_model = TrussPredictionModel.load(args.trained_model)

    predicted_areas = ml_model.predict_for_model(truss)
    print("Predicted optimal areas:")
    for eid, area in sorted(predicted_areas.items()):
        print(f"  Element {eid}: {area * 1e4:.4f} cm²")


def main():
    parser = argparse.ArgumentParser(
        prog="truss_optimizer",
        description="Truss structural analysis, optimization, and ML prediction tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Run FEA analysis on a truss model")
    p_analyze.add_argument("model", help="Path to truss model JSON file")

    # optimize
    p_opt = subparsers.add_parser("optimize", help="Optimize truss cross-sections")
    p_opt.add_argument("model", help="Path to truss model JSON file")
    p_opt.add_argument("--objective", choices=["weight", "cost"], default="weight")
    p_opt.add_argument("--max-disp", type=float, default=0.05)
    p_opt.add_argument("--safety-factor", type=float, default=1.5)
    p_opt.add_argument("--output", "-o", help="Save optimized model to path")
    p_opt.add_argument("--verbose", "-v", action="store_true")

    # generate-data
    p_gen = subparsers.add_parser("generate-data", help="Generate training dataset")
    p_gen.add_argument("n_samples", type=int, help="Number of samples")
    p_gen.add_argument("output", help="Output path (.npz)")
    p_gen.add_argument("--seed", type=int, default=42)

    # train
    p_train = subparsers.add_parser("train", help="Train ML prediction model")
    p_train.add_argument("dataset", help="Path to dataset (.npz)")
    p_train.add_argument("output", help="Output model path (.pkl)")
    p_train.add_argument("--layers", type=int, nargs="+", default=[128, 64, 32])
    p_train.add_argument("--max-iter", type=int, default=1000)

    # compare
    p_cmp = subparsers.add_parser("compare", help="Compare cost vs weight optimization")
    p_cmp.add_argument("model", help="Path to truss model JSON file")
    p_cmp.add_argument("--max-disp", type=float, default=0.05)
    p_cmp.add_argument("--safety-factor", type=float, default=1.5)
    p_cmp.add_argument("--pareto", action="store_true", help="Also generate Pareto front")
    p_cmp.add_argument("--pareto-points", type=int, default=11)
    p_cmp.add_argument("--verbose", "-v", action="store_true")

    # shape-opt
    p_shape = subparsers.add_parser("shape-opt", help="Shape optimization (move nodes + size for min cost)")
    p_shape.add_argument("model", help="Path to truss model JSON file")
    p_shape.add_argument("--max-disp", type=float, default=0.05)
    p_shape.add_argument("--safety-factor", type=float, default=1.5)
    p_shape.add_argument("--max-move-x", type=float, default=2.0, help="Max node movement in x (m)")
    p_shape.add_argument("--max-move-y", type=float, default=2.0, help="Max node movement in y (m)")
    p_shape.add_argument("--min-height", type=float, default=0.5, help="Minimum truss height (m)")
    p_shape.add_argument("--output", "-o", help="Save optimized model to path")
    p_shape.add_argument("--verbose", "-v", action="store_true")

    # multi-load
    p_multi = subparsers.add_parser("multi-load", help="Multi-load-case optimization (min cost)")
    p_multi.add_argument("model", help="Path to truss model JSON file")
    p_multi.add_argument("load_cases", help="Path to load cases JSON file")
    p_multi.add_argument("--max-disp", type=float, default=0.05)
    p_multi.add_argument("--safety-factor", type=float, default=1.5)
    p_multi.add_argument("--output", "-o", help="Save optimized model to path")
    p_multi.add_argument("--verbose", "-v", action="store_true")

    # genetic
    p_ga = subparsers.add_parser("genetic", help="Genetic algorithm optimization (topology + sizing)")
    p_ga.add_argument("model", help="Path to truss model JSON file")
    p_ga.add_argument("--population", type=int, default=60, help="Population size")
    p_ga.add_argument("--generations", type=int, default=100, help="Max generations")
    p_ga.add_argument("--max-disp", type=float, default=0.05)
    p_ga.add_argument("--safety-factor", type=float, default=1.5)
    p_ga.add_argument("--topology", action="store_true", default=True,
                      help="Allow topology mutation (add/remove members)")
    p_ga.add_argument("--no-topology", dest="topology", action="store_false",
                      help="Sizing only, no topology changes")
    p_ga.add_argument("--seed", type=int, default=42)
    p_ga.add_argument("--output", "-o", help="Save optimized model to path")
    p_ga.add_argument("--verbose", "-v", action="store_true")

    # predict
    p_pred = subparsers.add_parser("predict", help="Predict optimal areas using ML model")
    p_pred.add_argument("model", help="Path to truss model JSON")
    p_pred.add_argument("trained_model", help="Path to trained ML model (.pkl)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "analyze": cmd_analyze,
        "optimize": cmd_optimize,
        "compare": cmd_compare,
        "shape-opt": cmd_shape_opt,
        "multi-load": cmd_multi_load,
        "genetic": cmd_genetic,
        "generate-data": cmd_generate_data,
        "train": cmd_train,
        "predict": cmd_predict,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
