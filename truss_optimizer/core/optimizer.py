"""
Truss optimization engine.

Supports weight minimization and cost minimization subject to stress and
displacement constraints, using scipy's SLSQP optimizer.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from scipy.optimize import minimize

from .analysis import TrussAnalyzer, AnalysisResult
from .truss_model import TrussModel


class ObjectiveType(Enum):
    WEIGHT = "weight"
    COST = "cost"


@dataclass
class OptimizationConstraints:
    max_displacement: float = 0.05       # m (L/200 typical)
    min_area: float = 1e-5               # m^2
    max_area: float = 0.1                # m^2
    safety_factor: float = 1.5           # minimum required


@dataclass
class OptimizationResult:
    optimized_model: TrussModel
    analysis: AnalysisResult
    initial_weight: float
    final_weight: float
    initial_cost: float
    final_cost: float
    weight_reduction_pct: float
    cost_reduction_pct: float
    iterations: int
    converged: bool
    optimized_areas: dict[int, float]

    def summary(self) -> str:
        lines = [
            "=== Optimization Results ===",
            f"Converged:         {'Yes' if self.converged else 'No'}",
            f"Iterations:        {self.iterations}",
            f"Weight:            {self.initial_weight:.2f} -> {self.final_weight:.2f} kg "
            f"({self.weight_reduction_pct:+.1f}%)",
            f"Cost:              ${self.initial_cost:.2f} -> ${self.final_cost:.2f} "
            f"({self.cost_reduction_pct:+.1f}%)",
            "",
            "Optimized cross-sections:",
            f"{'Elem':>4} {'Area (cm²)':>12}",
            "-" * 20,
        ]
        for eid, area in sorted(self.optimized_areas.items()):
            lines.append(f"{eid:>4} {area * 1e4:>12.4f}")
        return "\n".join(lines)


class TrussOptimizer:
    """Optimizes truss cross-sectional areas for minimum weight or cost."""

    def __init__(self, model: TrussModel,
                 objective: ObjectiveType = ObjectiveType.WEIGHT,
                 constraints: Optional[OptimizationConstraints] = None):
        self.base_model = model
        self.objective = objective
        self.constraints = constraints or OptimizationConstraints()
        self._eval_count = 0

    def _create_model_with_areas(self, areas: np.ndarray) -> TrussModel:
        """Create a copy of the model with updated element areas."""
        model = copy.deepcopy(self.base_model)
        elem_ids = sorted(model.elements.keys())
        for i, eid in enumerate(elem_ids):
            model.elements[eid].area = float(areas[i])
        return model

    def _objective_fn(self, areas: np.ndarray) -> float:
        """Compute the objective function value."""
        model = self._create_model_with_areas(areas)
        if self.objective == ObjectiveType.WEIGHT:
            return model.total_weight
        else:
            return model.total_cost

    def _stress_constraint(self, areas: np.ndarray) -> np.ndarray:
        """Stress constraint: yield_stress / SF - |stress| >= 0 for each element."""
        model = self._create_model_with_areas(areas)
        try:
            analyzer = TrussAnalyzer(model)
            result = analyzer.analyze()
        except (ValueError, np.linalg.LinAlgError):
            return np.full(len(areas), -1e10)

        elem_ids = sorted(model.elements.keys())
        constraints = []
        for eid in elem_ids:
            allowable = model.elements[eid].material.yield_stress / self.constraints.safety_factor
            constraints.append(allowable - abs(result.element_stresses[eid]))
        return np.array(constraints)

    def _displacement_constraint(self, areas: np.ndarray) -> float:
        """Displacement constraint: max_disp_allowed - max_disp >= 0."""
        model = self._create_model_with_areas(areas)
        try:
            analyzer = TrussAnalyzer(model)
            result = analyzer.analyze()
        except (ValueError, np.linalg.LinAlgError):
            return -1e10
        return self.constraints.max_displacement - result.max_displacement

    def optimize(self, max_iterations: int = 200, tolerance: float = 1e-8,
                 verbose: bool = False) -> OptimizationResult:
        """Run the optimization."""
        errors = self.base_model.validate()
        if errors:
            raise ValueError(f"Model validation failed: {'; '.join(errors)}")

        # Initial areas
        elem_ids = sorted(self.base_model.elements.keys())
        x0 = np.array([self.base_model.elements[eid].area for eid in elem_ids])
        n = len(x0)

        # Bounds
        bounds = [(self.constraints.min_area, self.constraints.max_area)] * n

        # Initial analysis
        initial_analyzer = TrussAnalyzer(self.base_model)
        initial_result = initial_analyzer.analyze()

        # Constraints for scipy
        cons = [
            {"type": "ineq", "fun": self._stress_constraint},
            {"type": "ineq", "fun": self._displacement_constraint},
        ]

        callback_count = [0]

        def callback(xk):
            callback_count[0] += 1
            if verbose and callback_count[0] % 10 == 0:
                obj = self._objective_fn(xk)
                print(f"  Iteration {callback_count[0]}: objective = {obj:.4f}")

        result = minimize(
            self._objective_fn,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": max_iterations, "ftol": tolerance, "disp": verbose},
            callback=callback,
        )

        # Build optimized model and analyze
        optimized_model = self._create_model_with_areas(result.x)
        final_analyzer = TrussAnalyzer(optimized_model)
        final_result = final_analyzer.analyze()

        optimized_areas = {eid: float(result.x[i]) for i, eid in enumerate(elem_ids)}

        initial_weight = initial_result.total_weight
        final_weight = final_result.total_weight
        initial_cost = initial_result.total_cost
        final_cost = final_result.total_cost

        weight_pct = ((final_weight - initial_weight) / initial_weight * 100
                      if initial_weight > 0 else 0.0)
        cost_pct = ((final_cost - initial_cost) / initial_cost * 100
                    if initial_cost > 0 else 0.0)

        return OptimizationResult(
            optimized_model=optimized_model,
            analysis=final_result,
            initial_weight=initial_weight,
            final_weight=final_weight,
            initial_cost=initial_cost,
            final_cost=final_cost,
            weight_reduction_pct=weight_pct,
            cost_reduction_pct=cost_pct,
            iterations=result.nit,
            converged=result.success,
            optimized_areas=optimized_areas,
        )


@dataclass
class ComparisonResult:
    """Side-by-side results from optimizing the same truss for weight vs cost."""
    initial_analysis: AnalysisResult
    weight_result: OptimizationResult
    cost_result: OptimizationResult

    def summary(self) -> str:
        w = self.weight_result
        c = self.cost_result
        lines = [
            "=" * 65,
            "  COST vs WEIGHT OPTIMIZATION COMPARISON",
            "=" * 65,
            "",
            f"{'Metric':<30} {'Initial':>10} {'Min Weight':>12} {'Min Cost':>12}",
            "-" * 65,
            f"{'Weight (kg)':<30} {self.initial_analysis.total_weight:>10.2f} "
            f"{w.final_weight:>12.2f} {c.final_weight:>12.2f}",
            f"{'Cost ($)':<30} {self.initial_analysis.total_cost:>10.2f} "
            f"{w.final_cost:>12.2f} {c.final_cost:>12.2f}",
            f"{'Max Displacement (mm)':<30} {self.initial_analysis.max_displacement * 1e3:>10.3f} "
            f"{w.analysis.max_displacement * 1e3:>12.3f} {c.analysis.max_displacement * 1e3:>12.3f}",
            f"{'Max Stress (MPa)':<30} {self.initial_analysis.max_stress / 1e6:>10.2f} "
            f"{w.analysis.max_stress / 1e6:>12.2f} {c.analysis.max_stress / 1e6:>12.2f}",
            f"{'Feasible':<30} {'Yes' if self.initial_analysis.is_feasible else 'No':>10} "
            f"{'Yes' if w.analysis.is_feasible else 'No':>12} "
            f"{'Yes' if c.analysis.is_feasible else 'No':>12}",
            f"{'Converged':<30} {'---':>10} "
            f"{'Yes' if w.converged else 'No':>12} {'Yes' if c.converged else 'No':>12}",
            "",
            "  Element Cross-Section Comparison (cm^2):",
            f"  {'Elem':>4} {'Initial':>10} {'Min Weight':>12} {'Min Cost':>12}  {'Diff':>8}",
            "  " + "-" * 50,
        ]
        all_eids = sorted(
            set(w.optimized_areas.keys()) | set(c.optimized_areas.keys())
        )
        for eid in all_eids:
            a_init = self.weight_result.optimized_model.elements[eid].area  # we'll use initial
            # Get initial area from the weight result's initial value
            a_w = w.optimized_areas.get(eid, 0) * 1e4
            a_c = c.optimized_areas.get(eid, 0) * 1e4
            diff_pct = ((a_c - a_w) / a_w * 100) if a_w > 0 else 0
            lines.append(f"  {eid:>4} {'---':>10} {a_w:>12.4f} {a_c:>12.4f}  {diff_pct:>+7.1f}%")

        # Tradeoff summary
        lines.append("")
        if w.final_weight <= c.final_weight and w.final_cost <= c.final_cost:
            lines.append("  >> Min-weight design dominates in both weight AND cost.")
        elif c.final_weight <= w.final_weight and c.final_cost <= w.final_cost:
            lines.append("  >> Min-cost design dominates in both weight AND cost.")
        else:
            weight_saved = c.final_weight - w.final_weight
            cost_saved = w.final_cost - c.final_cost
            lines.append("  >> TRADEOFF EXISTS:")
            lines.append(f"     Choosing min-weight saves {weight_saved:.2f} kg "
                         f"but costs ${abs(cost_saved):.2f} {'more' if cost_saved > 0 else 'less'}")
            lines.append(f"     Choosing min-cost saves ${abs(cost_saved):.2f} "
                         f"but weighs {abs(weight_saved):.2f} kg {'more' if weight_saved > 0 else 'less'}")
            if weight_saved != 0 and cost_saved != 0:
                marginal = abs(cost_saved / weight_saved)
                lines.append(f"     Marginal cost of weight reduction: ${marginal:.2f}/kg")

        return "\n".join(lines)


@dataclass
class ParetoPoint:
    """A single point on the Pareto front."""
    alpha: float           # blend weight: 0 = pure cost, 1 = pure weight
    weight: float          # kg
    cost: float            # $
    max_displacement: float
    max_stress: float
    is_feasible: bool
    areas: dict[int, float]


class TrussComparison:
    """Compares cost vs weight optimization and explores the Pareto front."""

    def __init__(self, model: TrussModel,
                 constraints: Optional[OptimizationConstraints] = None):
        self.model = model
        self.constraints = constraints or OptimizationConstraints()

    def compare(self, max_iterations: int = 200,
                verbose: bool = False) -> ComparisonResult:
        """Optimize for both weight and cost, return side-by-side comparison."""
        initial_result = TrussAnalyzer(self.model).analyze()

        weight_opt = TrussOptimizer(
            self.model, ObjectiveType.WEIGHT, self.constraints
        )
        cost_opt = TrussOptimizer(
            self.model, ObjectiveType.COST, self.constraints
        )

        weight_result = weight_opt.optimize(max_iterations=max_iterations, verbose=verbose)
        cost_result = cost_opt.optimize(max_iterations=max_iterations, verbose=verbose)

        return ComparisonResult(
            initial_analysis=initial_result,
            weight_result=weight_result,
            cost_result=cost_result,
        )

    def pareto_front(self, n_points: int = 11,
                     max_iterations: int = 200) -> list[ParetoPoint]:
        """Sweep blended objective (alpha * weight + (1-alpha) * cost) to trace Pareto front.

        alpha=1.0 -> pure weight minimization
        alpha=0.0 -> pure cost minimization
        """
        alphas = np.linspace(0.0, 1.0, n_points)
        points = []

        for alpha in alphas:
            optimizer = _BlendedOptimizer(
                self.model, alpha, self.constraints
            )
            try:
                result = optimizer.optimize(max_iterations=max_iterations)
                points.append(ParetoPoint(
                    alpha=float(alpha),
                    weight=result.final_weight,
                    cost=result.final_cost,
                    max_displacement=result.analysis.max_displacement,
                    max_stress=result.analysis.max_stress,
                    is_feasible=result.analysis.is_feasible,
                    areas=result.optimized_areas,
                ))
            except (ValueError, np.linalg.LinAlgError):
                continue

        return points

    @staticmethod
    def pareto_summary(points: list[ParetoPoint]) -> str:
        lines = [
            "=" * 70,
            "  PARETO FRONT: Weight vs Cost Tradeoff",
            "=" * 70,
            "",
            f"{'Alpha':>6} {'Weight (kg)':>12} {'Cost ($)':>12} "
            f"{'Disp (mm)':>10} {'Stress (MPa)':>13} {'Feasible':>9}",
            "-" * 70,
        ]
        for p in points:
            lines.append(
                f"{p.alpha:>6.2f} {p.weight:>12.2f} {p.cost:>12.2f} "
                f"{p.max_displacement * 1e3:>10.3f} {p.max_stress / 1e6:>13.2f} "
                f"{'Yes' if p.is_feasible else 'No':>9}"
            )
        return "\n".join(lines)


class _BlendedOptimizer(TrussOptimizer):
    """Internal optimizer that blends weight and cost objectives."""

    def __init__(self, model: TrussModel, alpha: float,
                 constraints: Optional[OptimizationConstraints] = None):
        super().__init__(model, ObjectiveType.WEIGHT, constraints)
        self.alpha = alpha  # 1.0 = pure weight, 0.0 = pure cost
        # Normalization factors (computed from initial model)
        self._weight_scale = model.total_weight or 1.0
        self._cost_scale = model.total_cost or 1.0

    def _objective_fn(self, areas: np.ndarray) -> float:
        model = self._create_model_with_areas(areas)
        normalized_weight = model.total_weight / self._weight_scale
        normalized_cost = model.total_cost / self._cost_scale
        return self.alpha * normalized_weight + (1 - self.alpha) * normalized_cost
