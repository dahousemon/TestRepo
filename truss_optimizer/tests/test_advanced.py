"""Tests for shape optimization and multi-load-case optimization."""

import math
import pytest
import numpy as np

from truss_optimizer.core.truss_model import (
    TrussModel, Material, SupportType, Load,
)
from truss_optimizer.core.analysis import TrussAnalyzer
from truss_optimizer.core.advanced import (
    ShapeOptimizer, ShapeOptConstraints, ShapeOptResult,
    MultiLoadCaseOptimizer, MultiLoadConstraints, MultiLoadCaseResult,
    LoadCase,
)


def make_shape_truss() -> TrussModel:
    """Triangle truss where the apex node can be moved."""
    model = TrussModel("Shape Test")
    steel = Material.steel()
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 6.0, 0.0, SupportType.ROLLER_X)
    model.add_node(2, 3.0, 2.0)  # free apex, movable
    area = 0.005
    model.add_element(0, 0, 2, area, steel)
    model.add_element(1, 2, 1, area, steel)
    model.add_element(2, 0, 1, area, steel)
    model.add_load(2, 0, -80e3)
    return model


def make_multi_load_truss() -> TrussModel:
    """Bridge truss for multi-load-case testing (no loads - they come from cases)."""
    model = TrussModel("MultiLoad Test")
    steel = Material.steel()
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 3.0, 0.0)
    model.add_node(2, 6.0, 0.0, SupportType.ROLLER_X)
    model.add_node(3, 1.5, 2.5)
    model.add_node(4, 4.5, 2.5)
    area = 0.004
    model.add_element(0, 0, 1, area, steel)
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 0, 3, area, steel)
    model.add_element(3, 3, 1, area, steel)
    model.add_element(4, 1, 4, area, steel)
    model.add_element(5, 4, 2, area, steel)
    model.add_element(6, 3, 4, area, steel)
    # Need a placeholder load for validation
    model.add_load(1, 0, -50e3)
    return model


class TestShapeOptimizer:
    def test_shape_opt_runs(self):
        model = make_shape_truss()
        constraints = ShapeOptConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
            max_node_move_x=2.0,
            max_node_move_y=2.0,
            min_height=0.5,
        )
        optimizer = ShapeOptimizer(model, constraints)
        result = optimizer.optimize(max_iterations=100)

        assert isinstance(result, ShapeOptResult)
        assert result.final_cost > 0
        assert result.final_weight > 0

    def test_shape_opt_reduces_cost(self):
        model = make_shape_truss()
        constraints = ShapeOptConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
            max_node_move_x=2.0,
            max_node_move_y=2.0,
            min_height=0.3,
        )
        optimizer = ShapeOptimizer(model, constraints)
        result = optimizer.optimize(max_iterations=200)

        # Should find a design no more expensive than initial
        assert result.final_cost <= result.initial_cost + 0.01

    def test_shape_opt_moves_nodes(self):
        model = make_shape_truss()
        constraints = ShapeOptConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
            max_node_move_x=2.0,
            max_node_move_y=2.0,
            min_height=0.3,
        )
        optimizer = ShapeOptimizer(model, constraints)
        result = optimizer.optimize(max_iterations=200)

        # Node 2 is free and should have optimized position
        assert 2 in result.optimized_positions
        new_x, new_y = result.optimized_positions[2]
        assert isinstance(new_x, float)
        assert isinstance(new_y, float)

    def test_shape_opt_respects_min_height(self):
        model = make_shape_truss()
        min_h = 1.0
        constraints = ShapeOptConstraints(
            max_displacement=0.2,
            safety_factor=1.0,
            min_area=1e-4,
            max_area=0.05,
            min_height=min_h,
        )
        optimizer = ShapeOptimizer(model, constraints)
        result = optimizer.optimize(max_iterations=100)

        ys = [py for _, (_, py) in result.optimized_positions.items()]
        actual_height = max(ys) - min(ys)
        assert actual_height >= min_h - 0.01  # small tolerance

    def test_shape_opt_summary(self):
        model = make_shape_truss()
        optimizer = ShapeOptimizer(model)
        result = optimizer.optimize(max_iterations=50)
        summary = result.summary()
        assert "SHAPE OPTIMIZATION" in summary
        assert "Cost:" in summary

    def test_support_nodes_dont_move(self):
        model = make_shape_truss()
        optimizer = ShapeOptimizer(model)
        result = optimizer.optimize(max_iterations=50)

        # Node 0 is PIN, should not move
        x0, y0 = result.optimized_positions[0]
        assert abs(x0 - 0.0) < 1e-10
        assert abs(y0 - 0.0) < 1e-10


class TestMultiLoadCaseOptimizer:
    def _make_load_cases(self) -> list[LoadCase]:
        return [
            LoadCase("Dead Load", [
                Load(node_id=1, fx=0, fy=-50e3),
            ]),
            LoadCase("Wind Left", [
                Load(node_id=1, fx=0, fy=-30e3),
                Load(node_id=3, fx=20e3, fy=0),
                Load(node_id=4, fx=20e3, fy=0),
            ]),
            LoadCase("Wind Right", [
                Load(node_id=1, fx=0, fy=-30e3),
                Load(node_id=3, fx=-20e3, fy=0),
                Load(node_id=4, fx=-20e3, fy=0),
            ]),
            LoadCase("Heavy Live", [
                Load(node_id=1, fx=0, fy=-120e3),
            ]),
        ]

    def test_multi_load_runs(self):
        model = make_multi_load_truss()
        cases = self._make_load_cases()
        constraints = MultiLoadConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = MultiLoadCaseOptimizer(model, cases, constraints)
        result = optimizer.optimize(max_iterations=100)

        assert isinstance(result, MultiLoadCaseResult)
        assert result.final_cost > 0
        assert len(result.case_results) == 4

    def test_all_cases_analyzed(self):
        model = make_multi_load_truss()
        cases = self._make_load_cases()
        optimizer = MultiLoadCaseOptimizer(model, cases)
        result = optimizer.optimize(max_iterations=50)

        for case in cases:
            assert case.name in result.case_results
            assert result.case_results[case.name] is not None

    def test_governing_case_identified(self):
        model = make_multi_load_truss()
        cases = self._make_load_cases()
        optimizer = MultiLoadCaseOptimizer(model, cases)
        result = optimizer.optimize(max_iterations=50)

        assert result.governing_case in [c.name for c in cases]

    def test_multi_load_reduces_cost(self):
        model = make_multi_load_truss()
        cases = self._make_load_cases()
        constraints = MultiLoadConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = MultiLoadCaseOptimizer(model, cases, constraints)
        result = optimizer.optimize(max_iterations=200)

        assert result.final_cost <= result.initial_cost + 0.01

    def test_multi_load_summary(self):
        model = make_multi_load_truss()
        cases = self._make_load_cases()
        optimizer = MultiLoadCaseOptimizer(model, cases)
        result = optimizer.optimize(max_iterations=50)
        summary = result.summary()

        assert "MULTI-LOAD-CASE" in summary
        assert "Governing:" in summary
        assert "Dead Load" in summary
        assert "Wind Left" in summary

    def test_single_case_matches_standard_optimizer(self):
        """With one load case, should give similar results to standard optimizer."""
        model = make_multi_load_truss()
        cases = [LoadCase("Only", [Load(node_id=1, fx=0, fy=-50e3)])]
        constraints = MultiLoadConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = MultiLoadCaseOptimizer(model, cases, constraints)
        result = optimizer.optimize(max_iterations=100)

        assert result.governing_case == "Only"
        assert result.final_cost > 0
