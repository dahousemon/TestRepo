"""
Advanced truss optimization: shape optimization and multi-load-case optimization.

Shape optimization varies both node positions and cross-sectional areas
to find the minimum-cost geometry.

Multi-load-case optimization finds the minimum-cost design that satisfies
stress and displacement constraints across all load combinations simultaneously.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy.optimize import minimize

from .analysis import TrussAnalyzer, AnalysisResult
from .truss_model import TrussModel, Load, SupportType


@dataclass
class ShapeOptConstraints:
    """Constraints for shape optimization."""
    max_displacement: float = 0.05
    min_area: float = 1e-5
    max_area: float = 0.1
    safety_factor: float = 1.5
    # Node movement bounds (relative to initial position)
    max_node_move_x: float = 2.0   # max horizontal shift (m)
    max_node_move_y: float = 2.0   # max vertical shift (m)
    min_height: float = 0.5        # minimum truss height (m)


@dataclass
class ShapeOptResult:
    """Results from shape optimization."""
    optimized_model: TrussModel
    analysis: AnalysisResult
    initial_cost: float
    final_cost: float
    initial_weight: float
    final_weight: float
    cost_reduction_pct: float
    iterations: int
    converged: bool
    optimized_areas: dict[int, float]
    optimized_positions: dict[int, tuple[float, float]]
    moved_nodes: dict[int, tuple[float, float]]  # node_id -> (dx, dy)

    def summary(self) -> str:
        lines = [
            "=" * 60,
            "  SHAPE OPTIMIZATION RESULTS (Min Cost)",
            "=" * 60,
            f"Converged:     {'Yes' if self.converged else 'No'}",
            f"Iterations:    {self.iterations}",
            f"Cost:          ${self.initial_cost:.2f} -> ${self.final_cost:.2f} "
            f"({self.cost_reduction_pct:+.1f}%)",
            f"Weight:        {self.initial_weight:.2f} -> {self.final_weight:.2f} kg",
            f"Max Disp:      {self.analysis.max_displacement * 1e3:.3f} mm",
            f"Feasible:      {'Yes' if self.analysis.is_feasible else 'No'}",
            "",
            "  Optimized cross-sections:",
            f"  {'Elem':>4} {'Area (cm²)':>12}",
            "  " + "-" * 20,
        ]
        for eid, area in sorted(self.optimized_areas.items()):
            lines.append(f"  {eid:>4} {area * 1e4:>12.4f}")

        if self.moved_nodes:
            lines.append("")
            lines.append("  Node position changes:")
            lines.append(f"  {'Node':>4} {'dx (m)':>10} {'dy (m)':>10} "
                         f"{'New x':>10} {'New y':>10}")
            lines.append("  " + "-" * 44)
            for nid, (dx, dy) in sorted(self.moved_nodes.items()):
                nx, ny = self.optimized_positions[nid]
                lines.append(f"  {nid:>4} {dx:>+10.4f} {dy:>+10.4f} "
                             f"{nx:>10.4f} {ny:>10.4f}")

        return "\n".join(lines)


class ShapeOptimizer:
    """Optimizes both node positions and cross-sectional areas for minimum cost.

    Design variables:
      - Cross-sectional area of each element
      - x, y coordinates of each free (unsupported) node

    Support nodes are fixed in their constrained directions.
    """

    def __init__(self, model: TrussModel,
                 constraints: Optional[ShapeOptConstraints] = None):
        self.base_model = model
        self.constraints = constraints or ShapeOptConstraints()

        # Identify movable nodes and their DOFs
        self._elem_ids = sorted(model.elements.keys())
        self._n_areas = len(self._elem_ids)

        # Movable node DOFs: free nodes can move in x and y,
        # roller nodes can move in their free direction
        self._movable: list[tuple[int, str]] = []  # (node_id, 'x'|'y')
        for node in sorted(model.nodes.values(), key=lambda n: n.id):
            if node.support == SupportType.FREE:
                self._movable.append((node.id, "x"))
                self._movable.append((node.id, "y"))
            elif node.support == SupportType.ROLLER_X:
                # Fixed in y, free in x
                self._movable.append((node.id, "x"))
            elif node.support == SupportType.ROLLER_Y:
                # Fixed in x, free in y
                self._movable.append((node.id, "y"))
            # PIN nodes: fully fixed, not movable

        self._n_shape = len(self._movable)
        self._n_vars = self._n_areas + self._n_shape

        # Store initial positions for bounds
        self._initial_pos = {
            nid: (node.x, node.y) for nid, node in model.nodes.items()
        }

    def _unpack_variables(self, x: np.ndarray) -> tuple[np.ndarray, dict[int, tuple[float, float]]]:
        """Unpack design vector into areas and node positions."""
        areas = x[:self._n_areas]

        positions = {}
        for nid, node in self.base_model.nodes.items():
            positions[nid] = (node.x, node.y)

        for i, (nid, direction) in enumerate(self._movable):
            cur_x, cur_y = positions[nid]
            if direction == "x":
                positions[nid] = (x[self._n_areas + i], cur_y)
            else:
                positions[nid] = (cur_x, x[self._n_areas + i])

        return areas, positions

    def _create_model(self, x: np.ndarray) -> TrussModel:
        """Build a TrussModel from the design vector."""
        areas, positions = self._unpack_variables(x)
        model = copy.deepcopy(self.base_model)

        for i, eid in enumerate(self._elem_ids):
            model.elements[eid].area = float(areas[i])

        for nid, (px, py) in positions.items():
            model.nodes[nid].x = px
            model.nodes[nid].y = py

        return model

    def _objective(self, x: np.ndarray) -> float:
        model = self._create_model(x)
        return model.total_cost

    def _stress_constraint(self, x: np.ndarray) -> np.ndarray:
        model = self._create_model(x)
        try:
            result = TrussAnalyzer(model).analyze()
        except (ValueError, np.linalg.LinAlgError):
            return np.full(self._n_areas, -1e10)

        constraints = []
        for eid in self._elem_ids:
            allowable = model.elements[eid].material.yield_stress / self.constraints.safety_factor
            constraints.append(allowable - abs(result.element_stresses[eid]))
        return np.array(constraints)

    def _displacement_constraint(self, x: np.ndarray) -> float:
        model = self._create_model(x)
        try:
            result = TrussAnalyzer(model).analyze()
        except (ValueError, np.linalg.LinAlgError):
            return -1e10
        return self.constraints.max_displacement - result.max_displacement

    def _min_height_constraint(self, x: np.ndarray) -> float:
        """Ensure truss maintains minimum height."""
        _, positions = self._unpack_variables(x)
        ys = [py for _, (_, py) in positions.items()]
        height = max(ys) - min(ys) if ys else 0
        return height - self.constraints.min_height

    def _build_bounds(self) -> list[tuple[float, float]]:
        bounds = []
        # Area bounds
        for _ in self._elem_ids:
            bounds.append((self.constraints.min_area, self.constraints.max_area))
        # Position bounds
        for nid, direction in self._movable:
            init_x, init_y = self._initial_pos[nid]
            if direction == "x":
                bounds.append((
                    init_x - self.constraints.max_node_move_x,
                    init_x + self.constraints.max_node_move_x,
                ))
            else:
                bounds.append((
                    init_y - self.constraints.max_node_move_y,
                    init_y + self.constraints.max_node_move_y,
                ))
        return bounds

    def optimize(self, max_iterations: int = 300, tolerance: float = 1e-8,
                 verbose: bool = False) -> ShapeOptResult:
        errors = self.base_model.validate()
        if errors:
            raise ValueError(f"Model validation failed: {'; '.join(errors)}")

        # Initial values
        x0_areas = np.array([self.base_model.elements[eid].area
                             for eid in self._elem_ids])
        x0_shape = []
        for nid, direction in self._movable:
            node = self.base_model.nodes[nid]
            x0_shape.append(node.x if direction == "x" else node.y)
        x0 = np.concatenate([x0_areas, np.array(x0_shape)])

        initial_cost = self.base_model.total_cost
        initial_weight = self.base_model.total_weight

        bounds = self._build_bounds()
        cons = [
            {"type": "ineq", "fun": self._stress_constraint},
            {"type": "ineq", "fun": self._displacement_constraint},
            {"type": "ineq", "fun": self._min_height_constraint},
        ]

        result = minimize(
            self._objective, x0, method="SLSQP",
            bounds=bounds, constraints=cons,
            options={"maxiter": max_iterations, "ftol": tolerance, "disp": verbose},
        )

        optimized_model = self._create_model(result.x)
        final_result = TrussAnalyzer(optimized_model).analyze()

        areas, positions = self._unpack_variables(result.x)
        optimized_areas = {eid: float(areas[i]) for i, eid in enumerate(self._elem_ids)}

        moved_nodes = {}
        for nid in positions:
            init_x, init_y = self._initial_pos[nid]
            new_x, new_y = positions[nid]
            dx = new_x - init_x
            dy = new_y - init_y
            if abs(dx) > 1e-6 or abs(dy) > 1e-6:
                moved_nodes[nid] = (dx, dy)

        final_cost = optimized_model.total_cost
        cost_pct = ((final_cost - initial_cost) / initial_cost * 100
                    if initial_cost > 0 else 0.0)

        return ShapeOptResult(
            optimized_model=optimized_model,
            analysis=final_result,
            initial_cost=initial_cost,
            final_cost=final_cost,
            initial_weight=initial_weight,
            final_weight=optimized_model.total_weight,
            cost_reduction_pct=cost_pct,
            iterations=result.nit,
            converged=result.success,
            optimized_areas=optimized_areas,
            optimized_positions=positions,
            moved_nodes=moved_nodes,
        )


# ---------------------------------------------------------------------------
# Multi-Load-Case Optimization
# ---------------------------------------------------------------------------

@dataclass
class LoadCase:
    """A named collection of loads representing one loading scenario."""
    name: str
    loads: list[Load]
    weight_factor: float = 1.0  # importance weight for this case

    def __repr__(self) -> str:
        return f"LoadCase('{self.name}', {len(self.loads)} loads, factor={self.weight_factor})"


@dataclass
class MultiLoadConstraints:
    """Constraints for multi-load-case optimization."""
    max_displacement: float = 0.05
    min_area: float = 1e-5
    max_area: float = 0.1
    safety_factor: float = 1.5


@dataclass
class MultiLoadCaseResult:
    """Results from multi-load-case optimization."""
    optimized_model: TrussModel
    case_results: dict[str, AnalysisResult]  # case_name -> analysis
    initial_cost: float
    final_cost: float
    initial_weight: float
    final_weight: float
    cost_reduction_pct: float
    iterations: int
    converged: bool
    optimized_areas: dict[int, float]
    governing_case: str  # which load case governed the design

    def summary(self) -> str:
        lines = [
            "=" * 65,
            "  MULTI-LOAD-CASE OPTIMIZATION RESULTS (Min Cost)",
            "=" * 65,
            f"Converged:     {'Yes' if self.converged else 'No'}",
            f"Iterations:    {self.iterations}",
            f"Cost:          ${self.initial_cost:.2f} -> ${self.final_cost:.2f} "
            f"({self.cost_reduction_pct:+.1f}%)",
            f"Weight:        {self.initial_weight:.2f} -> {self.final_weight:.2f} kg",
            f"Governing:     {self.governing_case}",
            "",
            "  Optimized cross-sections:",
            f"  {'Elem':>4} {'Area (cm²)':>12}",
            "  " + "-" * 20,
        ]
        for eid, area in sorted(self.optimized_areas.items()):
            lines.append(f"  {eid:>4} {area * 1e4:>12.4f}")

        lines.append("")
        lines.append("  Per-case results:")
        lines.append(f"  {'Case':<20} {'Max Disp (mm)':>14} {'Max Stress (MPa)':>17} "
                     f"{'Min SF':>8} {'Feasible':>9}")
        lines.append("  " + "-" * 72)

        for name, result in sorted(self.case_results.items()):
            min_sf = min(result.safety_factors.values()) if result.safety_factors else 0
            gov = " <-- GOV" if name == self.governing_case else ""
            lines.append(
                f"  {name:<20} {result.max_displacement * 1e3:>14.3f} "
                f"{result.max_stress / 1e6:>17.2f} {min_sf:>8.2f} "
                f"{'Yes' if result.is_feasible else 'No':>9}{gov}"
            )

        return "\n".join(lines)


class MultiLoadCaseOptimizer:
    """Optimizes truss cross-sections for minimum cost across multiple load cases.

    The design must simultaneously satisfy stress and displacement constraints
    under ALL specified load combinations. The optimizer finds the lightest
    (cheapest) design that works for every case.
    """

    def __init__(self, base_model: TrussModel,
                 load_cases: list[LoadCase],
                 constraints: Optional[MultiLoadConstraints] = None):
        self.base_model = base_model
        self.load_cases = load_cases
        self.constraints = constraints or MultiLoadConstraints()
        self._elem_ids = sorted(base_model.elements.keys())

    def _create_model_with_areas(self, areas: np.ndarray) -> TrussModel:
        model = copy.deepcopy(self.base_model)
        for i, eid in enumerate(self._elem_ids):
            model.elements[eid].area = float(areas[i])
        return model

    def _apply_load_case(self, model: TrussModel, case: LoadCase) -> TrussModel:
        """Replace model loads with a specific load case."""
        m = copy.deepcopy(model)
        m.loads = list(case.loads)
        return m

    def _analyze_all_cases(self, areas: np.ndarray) -> dict[str, AnalysisResult]:
        """Run analysis for all load cases with the given areas."""
        base = self._create_model_with_areas(areas)
        results = {}
        for case in self.load_cases:
            m = self._apply_load_case(base, case)
            try:
                results[case.name] = TrussAnalyzer(m).analyze()
            except (ValueError, np.linalg.LinAlgError):
                results[case.name] = None
        return results

    def _objective(self, areas: np.ndarray) -> float:
        model = self._create_model_with_areas(areas)
        return model.total_cost

    def _stress_constraint(self, areas: np.ndarray) -> np.ndarray:
        """All elements must satisfy stress limits under ALL load cases."""
        case_results = self._analyze_all_cases(areas)
        n_elem = len(self._elem_ids)
        all_constraints = []

        for case in self.load_cases:
            result = case_results.get(case.name)
            if result is None:
                all_constraints.extend([-1e10] * n_elem)
                continue

            base = self._create_model_with_areas(areas)
            for eid in self._elem_ids:
                allowable = (base.elements[eid].material.yield_stress
                             / self.constraints.safety_factor)
                all_constraints.append(
                    allowable - abs(result.element_stresses[eid])
                )

        return np.array(all_constraints)

    def _displacement_constraint(self, areas: np.ndarray) -> np.ndarray:
        """Max displacement must be within limits for ALL load cases."""
        case_results = self._analyze_all_cases(areas)
        constraints = []

        for case in self.load_cases:
            result = case_results.get(case.name)
            if result is None:
                constraints.append(-1e10)
            else:
                constraints.append(
                    self.constraints.max_displacement - result.max_displacement
                )

        return np.array(constraints)

    def optimize(self, max_iterations: int = 300, tolerance: float = 1e-8,
                 verbose: bool = False) -> MultiLoadCaseResult:
        errors = self.base_model.validate()
        if errors:
            raise ValueError(f"Model validation failed: {'; '.join(errors)}")

        x0 = np.array([self.base_model.elements[eid].area for eid in self._elem_ids])

        bounds = [(self.constraints.min_area, self.constraints.max_area)] * len(x0)
        cons = [
            {"type": "ineq", "fun": self._stress_constraint},
            {"type": "ineq", "fun": self._displacement_constraint},
        ]

        initial_cost = self.base_model.total_cost
        initial_weight = self.base_model.total_weight

        result = minimize(
            self._objective, x0, method="SLSQP",
            bounds=bounds, constraints=cons,
            options={"maxiter": max_iterations, "ftol": tolerance, "disp": verbose},
        )

        optimized_model = self._create_model_with_areas(result.x)
        optimized_areas = {eid: float(result.x[i]) for i, eid in enumerate(self._elem_ids)}

        # Analyze all cases with final design
        case_results = {}
        governing_case = ""
        worst_min_sf = float("inf")

        for case in self.load_cases:
            m = self._apply_load_case(optimized_model, case)
            try:
                analysis = TrussAnalyzer(m).analyze()
                case_results[case.name] = analysis
                min_sf = min(analysis.safety_factors.values()) if analysis.safety_factors else 0
                if min_sf < worst_min_sf:
                    worst_min_sf = min_sf
                    governing_case = case.name
            except (ValueError, np.linalg.LinAlgError):
                case_results[case.name] = None

        final_cost = optimized_model.total_cost
        cost_pct = ((final_cost - initial_cost) / initial_cost * 100
                    if initial_cost > 0 else 0.0)

        return MultiLoadCaseResult(
            optimized_model=optimized_model,
            case_results=case_results,
            initial_cost=initial_cost,
            final_cost=final_cost,
            initial_weight=initial_weight,
            final_weight=optimized_model.total_weight,
            cost_reduction_pct=cost_pct,
            iterations=result.nit,
            converged=result.success,
            optimized_areas=optimized_areas,
            governing_case=governing_case,
        )
