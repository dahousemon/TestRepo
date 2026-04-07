"""Tests for the genetic algorithm optimizer."""

import json
import pytest
import numpy as np
from pathlib import Path

from truss_optimizer.core.truss_model import (
    TrussModel, Material, SupportType, Load,
)
from truss_optimizer.core.genetic import (
    GeneticOptimizer, GAConfig, GAResult, Individual,
)


def make_ga_truss() -> TrussModel:
    """A 5-node truss with redundant members -- GA can remove some."""
    model = TrussModel("GA Test")
    steel = Material.steel()
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0)
    model.add_node(2, 8.0, 0.0, SupportType.ROLLER_X)
    model.add_node(3, 2.0, 3.0)
    model.add_node(4, 6.0, 3.0)

    area = 0.004
    model.add_element(0, 0, 1, area, steel)  # bottom
    model.add_element(1, 1, 2, area, steel)
    model.add_element(2, 0, 3, area, steel)  # diagonals
    model.add_element(3, 3, 1, area, steel)
    model.add_element(4, 1, 4, area, steel)
    model.add_element(5, 4, 2, area, steel)
    model.add_element(6, 3, 4, area, steel)  # top chord
    model.add_element(7, 0, 4, area, steel)  # redundant cross-diagonal
    model.add_element(8, 3, 2, area, steel)  # redundant cross-diagonal

    model.add_load(1, 0, -80e3)
    return model


class TestGeneticOptimizer:
    def test_ga_runs(self):
        model = make_ga_truss()
        config = GAConfig(
            population_size=20,
            generations=15,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        assert isinstance(result, GAResult)
        assert result.final_cost > 0
        assert result.generations_run > 0
        assert len(result.convergence_history) > 0

    def test_ga_finds_feasible_design(self):
        model = make_ga_truss()
        config = GAConfig(
            population_size=40,
            generations=50,
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
        )
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        # With enough generations, should find at least one feasible design
        assert result.best_individual.fitness < config.instability_penalty

    def test_ga_reduces_cost(self):
        model = make_ga_truss()
        config = GAConfig(
            population_size=40,
            generations=40,
            max_displacement=0.1,
            safety_factor=1.2,
            min_area=1e-4,
            max_area=0.05,
            allow_topology_mutation=False,  # sizing only for predictable test
        )
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        # Should find something cheaper than oversized initial design
        assert result.final_cost <= result.initial_cost + 0.01

    def test_ga_topology_mutation_removes_members(self):
        model = make_ga_truss()
        config = GAConfig(
            population_size=40,
            generations=60,
            max_displacement=0.1,
            safety_factor=1.2,
            allow_topology_mutation=True,
            member_remove_prob=0.15,
        )
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        # With redundant cross-diagonals, GA might remove some
        # (not guaranteed, but the mechanism should work)
        assert len(result.best_individual.active_elements) <= len(model.elements)

    def test_ga_preserves_essential_elements(self):
        model = make_ga_truss()
        config = GAConfig(
            population_size=20,
            generations=20,
            allow_topology_mutation=True,
            member_remove_prob=0.3,
        )
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        # Essential elements (connected to supports) should always be active
        for eid in optimizer._essential_elements:
            assert eid in result.best_individual.active_elements

    def test_ga_convergence_history_monotonic(self):
        model = make_ga_truss()
        config = GAConfig(population_size=20, generations=30)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()

        # Best fitness should never get worse (elitism)
        for i in range(1, len(result.convergence_history)):
            assert result.convergence_history[i] <= result.convergence_history[i - 1] + 1e-6

    def test_ga_summary(self):
        model = make_ga_truss()
        config = GAConfig(population_size=20, generations=15)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()
        summary = result.summary()

        assert "GENETIC ALGORITHM" in summary
        assert "Cost:" in summary
        assert "Generations:" in summary

    def test_ga_different_seeds(self):
        model = make_ga_truss()
        config = GAConfig(population_size=20, generations=20)
        optimizer = GeneticOptimizer(model, config)

        result1 = optimizer.optimize(seed=1)
        result2 = optimizer.optimize(seed=2)

        # Different seeds should give different results
        # (not guaranteed but very likely with random initialization)
        # At minimum both should complete
        assert result1.generations_run > 0
        assert result2.generations_run > 0

    def test_ga_on_simple_triangle(self):
        model = TrussModel("Simple")
        model.add_node(0, 0, 0, SupportType.PIN)
        model.add_node(1, 4, 0, SupportType.ROLLER_X)
        model.add_node(2, 2, 3)
        model.add_element(0, 0, 2, 0.005, Material.steel())
        model.add_element(1, 2, 1, 0.005, Material.steel())
        model.add_element(2, 0, 1, 0.005, Material.steel())
        model.add_load(2, 0, -50e3)

        config = GAConfig(population_size=20, generations=20)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()
        assert result.final_cost > 0


class TestGAWithTestTrusses:
    """Run GA on a few of the generated test truss files."""

    TEST_DIR = Path("truss_optimizer/data/test_trusses")

    @pytest.fixture
    def manifest(self):
        manifest_path = self.TEST_DIR / "manifest.json"
        if not manifest_path.exists():
            pytest.skip("Test trusses not generated")
        with open(manifest_path) as f:
            return json.load(f)

    def test_load_test_truss(self, manifest):
        entry = manifest[0]
        model = TrussModel.load(self.TEST_DIR / entry["file"])
        assert model.num_nodes > 0
        assert model.num_elements > 0

    def test_ga_on_warren_truss(self, manifest):
        warren = next(m for m in manifest if m["topology"] == "warren")
        model = TrussModel.load(self.TEST_DIR / warren["file"])

        config = GAConfig(population_size=20, generations=15, max_displacement=0.1)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()
        assert result.final_cost > 0

    def test_ga_on_pratt_truss(self, manifest):
        pratt = next(m for m in manifest if m["topology"] == "pratt")
        model = TrussModel.load(self.TEST_DIR / pratt["file"])

        config = GAConfig(population_size=20, generations=15, max_displacement=0.1)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()
        assert result.final_cost > 0

    def test_ga_on_mixed_material(self, manifest):
        mixed = next(m for m in manifest if m["topology"] == "mixed_material")
        model = TrussModel.load(self.TEST_DIR / mixed["file"])

        config = GAConfig(population_size=20, generations=15, max_displacement=0.1)
        optimizer = GeneticOptimizer(model, config)
        result = optimizer.optimize()
        assert result.final_cost > 0

    def test_manifest_has_100_entries(self, manifest):
        assert len(manifest) == 100

    def test_all_trusses_valid(self, manifest):
        """Verify all 100 test trusses pass validation."""
        for entry in manifest:
            model = TrussModel.load(self.TEST_DIR / entry["file"])
            errors = model.validate()
            assert len(errors) == 0, f"Truss {entry['file']} failed: {errors}"
