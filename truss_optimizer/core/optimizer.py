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
