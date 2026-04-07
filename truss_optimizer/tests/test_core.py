"""Tests for the truss analysis and optimization core."""

import math
import pytest
import numpy as np

from truss_optimizer.core.truss_model import (
    Node, Element, Material, Load, TrussModel, SupportType,
)
from truss_optimizer.core.analysis import TrussAnalyzer
from truss_optimizer.core.optimizer import (
    TrussOptimizer, ObjectiveType, OptimizationConstraints,
    TrussComparison, ComparisonResult,
)


def make_simple_truss() -> TrussModel:
    """Create a simple 3-node truss for testing."""
    model = TrussModel("Test Triangle")
    steel = Material.steel()

    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0, SupportType.ROLLER_X)
    model.add_node(2, 2.0, 3.0)

    area = 0.005  # 50 cm²
    model.add_element(0, 0, 2, area, steel)
    model.add_element(1, 2, 1, area, steel)
    model.add_element(2, 0, 1, area, steel)

    model.add_load(2, 0, -50e3)
    return model


def make_bridge_truss() -> TrussModel:
    """Create a 6-node bridge truss."""
    model = TrussModel("Test Bridge")
    steel = Material.steel()

    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 3.0, 0.0)
    model.add_node(2, 6.0, 0.0, SupportType.ROLLER_X)
    model.add_node(3, 1.5, 2.0)
    model.add_node(4, 4.5, 2.0)

    area = 0.003
    model.add_element(0, 0, 1, area, steel)
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 0, 3, area, steel)
    model.add_element(3, 3, 1, area, steel)
    model.add_element(4, 1, 4, area, steel)
    model.add_element(5, 4, 2, area, steel)
    model.add_element(6, 3, 4, area, steel)

    model.add_load(1, 0, -80e3)
    return model


class TestTrussModel:
    def test_node_creation(self):
        n = Node(0, 1.0, 2.0, SupportType.PIN)
        assert n.coords == (1.0, 2.0)
        assert n.is_constrained_x()
        assert n.is_constrained_y()

    def test_roller_constraints(self):
        n_rx = Node(0, 0, 0, SupportType.ROLLER_X)
        assert not n_rx.is_constrained_x()
        assert n_rx.is_constrained_y()

        n_ry = Node(1, 0, 0, SupportType.ROLLER_Y)
        assert n_ry.is_constrained_x()
        assert not n_ry.is_constrained_y()

    def test_material_presets(self):
        steel = Material.steel()
        assert steel.E == 200e9
        assert steel.density == 7850

        alum = Material.aluminum()
        assert alum.E == 69e9

    def test_element_properties(self):
        model = make_simple_truss()
        elem = model.elements[2]  # bottom chord 0->1
        length = elem.length(model.nodes)
        assert abs(length - 4.0) < 1e-10

    def test_model_validation(self):
        model = make_simple_truss()
        errors = model.validate()
        assert len(errors) == 0

    def test_model_validation_fails_no_nodes(self):
        model = TrussModel("Empty")
        errors = model.validate()
        assert len(errors) > 0

    def test_model_counts(self):
        model = make_simple_truss()
        assert model.num_nodes == 3
        assert model.num_elements == 3
        assert model.num_dofs == 6

    def test_constrained_dofs(self):
        model = make_simple_truss()
        constrained = model.get_constrained_dofs()
        # Node 0 (PIN): dof 0, 1; Node 1 (ROLLER_X): dof 3
        assert 0 in constrained
        assert 1 in constrained
        assert 3 in constrained
        assert len(constrained) == 3

    def test_serialization_roundtrip(self, tmp_path):
        model = make_simple_truss()
        path = tmp_path / "test_truss.json"
        model.save(path)
        loaded = TrussModel.load(path)
        assert loaded.num_nodes == model.num_nodes
        assert loaded.num_elements == model.num_elements
        assert len(loaded.loads) == len(model.loads)

    def test_total_weight(self):
        model = make_simple_truss()
        weight = model.total_weight
        assert weight > 0

    def test_add_element_validates_nodes(self):
        model = TrussModel("test")
        model.add_node(0, 0, 0)
        with pytest.raises(ValueError):
            model.add_element(0, 0, 99, 0.001)


class TestAnalysis:
    def test_simple_truss_analysis(self):
        model = make_simple_truss()
        analyzer = TrussAnalyzer(model)
        result = analyzer.analyze()

        # Node 2 should deflect downward
        assert result.displacements[5] < 0  # y-dof of node 2
        assert result.max_displacement > 0
        assert result.max_stress > 0

    def test_equilibrium(self):
        """Sum of reactions should equal sum of applied loads."""
        model = make_simple_truss()
        analyzer = TrussAnalyzer(model)
        result = analyzer.analyze()

        # Applied loads
        total_fx = sum(l.fx for l in model.loads)
        total_fy = sum(l.fy for l in model.loads)

        # Reactions at constrained DOFs
        constrained = model.get_constrained_dofs()
        rx = sum(result.reactions[d] for d in constrained if d % 2 == 0)
        ry = sum(result.reactions[d] for d in constrained if d % 2 == 1)

        assert abs(rx + total_fx) < 1e-6
        assert abs(ry + total_fy) < 1e-6

    def test_bridge_truss_analysis(self):
        model = make_bridge_truss()
        analyzer = TrussAnalyzer(model)
        result = analyzer.analyze()
        assert result.max_displacement > 0
        assert len(result.element_forces) == 7

    def test_all_elements_have_results(self):
        model = make_simple_truss()
        analyzer = TrussAnalyzer(model)
        result = analyzer.analyze()
        assert set(result.element_forces.keys()) == {0, 1, 2}
        assert set(result.element_stresses.keys()) == {0, 1, 2}
        assert set(result.safety_factors.keys()) == {0, 1, 2}

    def test_invalid_model_raises(self):
        model = TrussModel("Bad")
        model.add_node(0, 0, 0)
        analyzer = TrussAnalyzer(model)
        with pytest.raises(ValueError):
            analyzer.analyze()

    def test_summary_string(self):
        model = make_simple_truss()
        result = TrussAnalyzer(model).analyze()
        summary = result.summary()
        assert "Max displacement" in summary
        assert "Max stress" in summary


class TestOptimizer:
    def test_weight_optimization_reduces_weight(self):
        model = make_simple_truss()
        initial_weight = model.total_weight

        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = TrussOptimizer(model, ObjectiveType.WEIGHT, constraints)
        result = optimizer.optimize(max_iterations=200)

        # Optimizer should reduce weight from the oversized initial design
        assert result.final_weight <= initial_weight + 1e-6

    def test_cost_optimization(self):
        model = make_simple_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-5,
            max_area=0.05,
        )
        optimizer = TrussOptimizer(model, ObjectiveType.COST, constraints)
        result = optimizer.optimize(max_iterations=50)
        assert result.converged
        assert result.final_cost > 0

    def test_optimized_model_is_feasible(self):
        model = make_bridge_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.05,
            safety_factor=1.5,
            min_area=1e-5,
            max_area=0.05,
        )
        optimizer = TrussOptimizer(model, ObjectiveType.WEIGHT, constraints)
        result = optimizer.optimize(max_iterations=100)
        if result.converged:
            assert result.analysis.is_feasible

    def test_optimization_summary(self):
        model = make_simple_truss()
        optimizer = TrussOptimizer(model)
        result = optimizer.optimize(max_iterations=30)
        summary = result.summary()
        assert "Weight:" in summary
        assert "Cost:" in summary


class TestComparison:
    def test_compare_returns_both_results(self):
        model = make_bridge_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        comparison = TrussComparison(model, constraints)
        result = comparison.compare(max_iterations=50)

        assert isinstance(result, ComparisonResult)
        assert result.weight_result.final_weight > 0
        assert result.cost_result.final_cost > 0
        assert result.initial_analysis.total_weight > 0

    def test_comparison_summary_has_all_sections(self):
        model = make_simple_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        comparison = TrussComparison(model, constraints)
        result = comparison.compare(max_iterations=50)
        summary = result.summary()

        assert "COST vs WEIGHT" in summary
        assert "Weight (kg)" in summary
        assert "Cost ($)" in summary
        assert "Max Displacement" in summary
        assert "Max Stress" in summary

    def test_pareto_front_generates_points(self):
        model = make_simple_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        comparison = TrussComparison(model, constraints)
        points = comparison.pareto_front(n_points=5, max_iterations=50)

        assert len(points) > 0
        # First point (alpha=0) should favor cost, last (alpha=1) should favor weight
        for p in points:
            assert p.weight > 0
            assert p.cost > 0
            assert 0.0 <= p.alpha <= 1.0

    def test_pareto_summary_string(self):
        model = make_simple_truss()
        constraints = OptimizationConstraints(
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        comparison = TrussComparison(model, constraints)
        points = comparison.pareto_front(n_points=3, max_iterations=30)
        summary = TrussComparison.pareto_summary(points)
        assert "PARETO FRONT" in summary
        assert "Alpha" in summary
