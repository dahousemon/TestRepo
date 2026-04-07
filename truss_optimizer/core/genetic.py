"""
Genetic algorithm optimizer for truss topology and sizing.

Evolves a population of truss designs through selection, crossover, and mutation
to find minimum-cost designs. Unlike gradient-based methods, the GA can:
  - Add/remove members (topology optimization)
  - Handle discrete design variables
  - Escape local optima by exploring diverse designs simultaneously
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .analysis import TrussAnalyzer, AnalysisResult
from .truss_model import TrussModel, Node, Element, Material, Load, SupportType


@dataclass
class GAConfig:
    """Configuration for the genetic algorithm."""
    population_size: int = 60
    generations: int = 100
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    elite_fraction: float = 0.1      # top % kept unchanged
    tournament_size: int = 3
    # Sizing bounds
    min_area: float = 1e-4            # m^2
    max_area: float = 0.05            # m^2
    # Constraints
    max_displacement: float = 0.05    # m
    safety_factor: float = 1.5
    # Penalties for infeasible designs
    stress_penalty: float = 1e6
    displacement_penalty: float = 1e6
    instability_penalty: float = 1e8
    # Topology mutation
    allow_topology_mutation: bool = True
    member_add_prob: float = 0.05     # probability of adding a member per mutation
    member_remove_prob: float = 0.05  # probability of removing a member per mutation


@dataclass
class Individual:
    """A single truss design in the GA population."""
    areas: dict[int, float]                    # element_id -> area
    active_elements: set[int]                  # which elements are active
    fitness: float = float("inf")
    cost: float = float("inf")
    weight: float = float("inf")
    max_displacement: float = float("inf")
    max_stress: float = float("inf")
    is_feasible: bool = False
    min_safety_factor: float = 0.0


@dataclass
class GAResult:
    """Results from genetic algorithm optimization."""
    best_model: TrussModel
    best_analysis: Optional[AnalysisResult]
    initial_cost: float
    final_cost: float
    initial_weight: float
    final_weight: float
    cost_reduction_pct: float
    generations_run: int
    population_size: int
    best_individual: Individual
    convergence_history: list[float]  # best fitness per generation
    removed_elements: list[int]       # element IDs removed from original
    converged: bool

    def summary(self) -> str:
        lines = [
            "=" * 65,
            "  GENETIC ALGORITHM OPTIMIZATION RESULTS (Min Cost)",
            "=" * 65,
            f"Generations:       {self.generations_run}",
            f"Population:        {self.population_size}",
            f"Cost:              ${self.initial_cost:.2f} -> ${self.final_cost:.2f} "
            f"({self.cost_reduction_pct:+.1f}%)",
            f"Weight:            {self.initial_weight:.2f} -> {self.final_weight:.2f} kg",
            f"Max Displacement:  {self.best_individual.max_displacement * 1e3:.3f} mm",
            f"Min Safety Factor: {self.best_individual.min_safety_factor:.2f}",
            f"Feasible:          {'Yes' if self.best_individual.is_feasible else 'No'}",
        ]

        if self.removed_elements:
            lines.append(f"Removed elements:  {self.removed_elements}")

        lines.extend([
            "",
            "  Optimized cross-sections:",
            f"  {'Elem':>4} {'Area (cm²)':>12} {'Status':>8}",
            "  " + "-" * 28,
        ])
        for eid, area in sorted(self.best_individual.areas.items()):
            active = "active" if eid in self.best_individual.active_elements else "removed"
            if eid in self.best_individual.active_elements:
                lines.append(f"  {eid:>4} {area * 1e4:>12.4f} {active:>8}")
            else:
                lines.append(f"  {eid:>4} {'---':>12} {active:>8}")

        # Convergence
        if len(self.convergence_history) > 5:
            lines.extend([
                "",
                "  Convergence (best cost per generation):",
                f"    Gen 1:   ${self.convergence_history[0]:.2f}",
            ])
            mid = len(self.convergence_history) // 2
            lines.append(f"    Gen {mid}:  ${self.convergence_history[mid - 1]:.2f}")
            lines.append(
                f"    Gen {len(self.convergence_history)}: "
                f"${self.convergence_history[-1]:.2f}"
            )

        return "\n".join(lines)


class GeneticOptimizer:
    """Genetic algorithm for truss topology and sizing optimization.

    The GA works on a 'ground structure' -- the initial truss with all possible
    members. It then evolves which members are active (topology) and their
    cross-sectional areas (sizing) to minimize cost while satisfying constraints.
    """

    def __init__(self, model: TrussModel, config: Optional[GAConfig] = None):
        self.base_model = model
        self.config = config or GAConfig()
        self._all_elem_ids = sorted(model.elements.keys())
        self._rng = random.Random(42)
        self._np_rng = np.random.RandomState(42)

        # Precompute which elements are essential for stability
        self._essential_elements = self._find_essential_elements()

    def _find_essential_elements(self) -> set[int]:
        """Find elements that cannot be removed without making the truss a mechanism.

        A simple heuristic: elements connected to support nodes are essential.
        """
        essential = set()
        support_nodes = {
            nid for nid, node in self.base_model.nodes.items()
            if node.support != SupportType.FREE
        }
        for elem in self.base_model.elements.values():
            if elem.node_i in support_nodes or elem.node_j in support_nodes:
                essential.add(elem.id)
        return essential

    def _create_model_from_individual(self, ind: Individual) -> TrussModel:
        """Build a TrussModel from an individual's genome."""
        model = copy.deepcopy(self.base_model)

        # Remove inactive elements
        for eid in list(model.elements.keys()):
            if eid not in ind.active_elements:
                del model.elements[eid]
            else:
                model.elements[eid].area = ind.areas.get(eid, self.config.min_area)

        return model

    def _evaluate(self, ind: Individual) -> None:
        """Evaluate fitness of an individual. Lower fitness = better."""
        model = self._create_model_from_individual(ind)

        # Check minimum connectivity
        if len(model.elements) < len(model.nodes) - 1:
            ind.fitness = self.config.instability_penalty
            ind.is_feasible = False
            return

        try:
            errors = model.validate()
            if errors:
                ind.fitness = self.config.instability_penalty
                ind.is_feasible = False
                return

            analyzer = TrussAnalyzer(model)
            result = analyzer.analyze()
        except (ValueError, np.linalg.LinAlgError):
            ind.fitness = self.config.instability_penalty
            ind.is_feasible = False
            return

        ind.cost = model.total_cost
        ind.weight = model.total_weight
        ind.max_displacement = result.max_displacement
        ind.max_stress = result.max_stress
        ind.min_safety_factor = (
            min(result.safety_factors.values()) if result.safety_factors else 0.0
        )

        # Penalty-based fitness
        penalty = 0.0

        # Stress penalty
        for eid in ind.active_elements:
            if eid in result.safety_factors:
                sf = result.safety_factors[eid]
                if sf < self.config.safety_factor:
                    deficit = self.config.safety_factor - sf
                    penalty += self.config.stress_penalty * deficit ** 2

        # Displacement penalty
        if result.max_displacement > self.config.max_displacement:
            excess = result.max_displacement - self.config.max_displacement
            penalty += self.config.displacement_penalty * excess ** 2

        ind.fitness = model.total_cost + penalty
        ind.is_feasible = (penalty == 0.0)

    def _create_random_individual(self) -> Individual:
        """Create a random individual."""
        areas = {}
        active = set()

        for eid in self._all_elem_ids:
            # Random area
            log_min = math.log(self.config.min_area)
            log_max = math.log(self.config.max_area)
            areas[eid] = math.exp(self._rng.uniform(log_min, log_max))

            # Random topology (keep essential, randomly include others)
            if eid in self._essential_elements:
                active.add(eid)
            elif self._rng.random() < 0.7:  # 70% chance of keeping non-essential
                active.add(eid)

        return Individual(areas=areas, active_elements=active)

    def _create_initial_individual(self) -> Individual:
        """Create an individual matching the original design."""
        areas = {eid: self.base_model.elements[eid].area for eid in self._all_elem_ids}
        active = set(self._all_elem_ids)
        return Individual(areas=areas, active_elements=active)

    def _tournament_select(self, population: list[Individual]) -> Individual:
        """Select an individual via tournament selection."""
        contestants = self._rng.sample(population,
                                        min(self.config.tournament_size, len(population)))
        return min(contestants, key=lambda ind: ind.fitness)

    def _crossover(self, parent1: Individual, parent2: Individual) -> tuple[Individual, Individual]:
        """Uniform crossover of areas and topology."""
        areas1, areas2 = {}, {}
        active1, active2 = set(), set()

        for eid in self._all_elem_ids:
            if self._rng.random() < 0.5:
                areas1[eid] = parent1.areas.get(eid, self.config.min_area)
                areas2[eid] = parent2.areas.get(eid, self.config.min_area)
            else:
                areas1[eid] = parent2.areas.get(eid, self.config.min_area)
                areas2[eid] = parent1.areas.get(eid, self.config.min_area)

            # Topology crossover
            if eid in self._essential_elements:
                active1.add(eid)
                active2.add(eid)
            else:
                p1_has = eid in parent1.active_elements
                p2_has = eid in parent2.active_elements
                if self._rng.random() < 0.5:
                    if p1_has:
                        active1.add(eid)
                    if p2_has:
                        active2.add(eid)
                else:
                    if p2_has:
                        active1.add(eid)
                    if p1_has:
                        active2.add(eid)

        return (
            Individual(areas=areas1, active_elements=active1),
            Individual(areas=areas2, active_elements=active2),
        )

    def _mutate(self, ind: Individual) -> Individual:
        """Mutate an individual's areas and topology."""
        areas = dict(ind.areas)
        active = set(ind.active_elements)

        for eid in self._all_elem_ids:
            if self._rng.random() < self.config.mutation_rate:
                # Mutate area with log-normal perturbation
                if eid in areas:
                    log_area = math.log(areas[eid])
                    log_area += self._rng.gauss(0, 0.3)
                    new_area = math.exp(log_area)
                    areas[eid] = max(self.config.min_area,
                                     min(self.config.max_area, new_area))

        # Topology mutation
        if self.config.allow_topology_mutation:
            for eid in self._all_elem_ids:
                if eid in self._essential_elements:
                    continue
                # Add member
                if eid not in active and self._rng.random() < self.config.member_add_prob:
                    active.add(eid)
                    if eid not in areas:
                        log_min = math.log(self.config.min_area)
                        log_max = math.log(self.config.max_area)
                        areas[eid] = math.exp(self._rng.uniform(log_min, log_max))
                # Remove member
                elif eid in active and self._rng.random() < self.config.member_remove_prob:
                    active.discard(eid)

        return Individual(areas=areas, active_elements=active)

    def optimize(self, verbose: bool = False, seed: int = 42) -> GAResult:
        """Run the genetic algorithm optimization."""
        self._rng = random.Random(seed)
        self._np_rng = np.random.RandomState(seed)

        errors = self.base_model.validate()
        if errors:
            raise ValueError(f"Model validation failed: {'; '.join(errors)}")

        initial_cost = self.base_model.total_cost
        initial_weight = self.base_model.total_weight

        # Initialize population
        population: list[Individual] = []
        # Always include the original design
        population.append(self._create_initial_individual())
        # Fill rest with random individuals
        for _ in range(self.config.population_size - 1):
            population.append(self._create_random_individual())

        # Evaluate initial population
        for ind in population:
            self._evaluate(ind)

        convergence = []
        n_elite = max(1, int(self.config.elite_fraction * self.config.population_size))
        stagnation_count = 0
        best_ever_fitness = float("inf")

        for gen in range(self.config.generations):
            # Sort by fitness
            population.sort(key=lambda ind: ind.fitness)
            best = population[0]
            convergence.append(best.cost if best.is_feasible else best.fitness)

            if verbose and (gen + 1) % 10 == 0:
                feasible_count = sum(1 for ind in population if ind.is_feasible)
                print(f"  Gen {gen + 1:>4}: best_cost=${best.cost:.2f} "
                      f"fitness={best.fitness:.2f} "
                      f"feasible={feasible_count}/{len(population)} "
                      f"elements={len(best.active_elements)}")

            # Check stagnation
            if best.fitness < best_ever_fitness - 0.01:
                best_ever_fitness = best.fitness
                stagnation_count = 0
            else:
                stagnation_count += 1

            if stagnation_count > 30:
                if verbose:
                    print(f"  Converged after {gen + 1} generations (stagnation)")
                break

            # Elitism: keep top individuals
            new_population = population[:n_elite]

            # Generate offspring
            while len(new_population) < self.config.population_size:
                parent1 = self._tournament_select(population)
                parent2 = self._tournament_select(population)

                if self._rng.random() < self.config.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1 = Individual(areas=dict(parent1.areas),
                                        active_elements=set(parent1.active_elements))
                    child2 = Individual(areas=dict(parent2.areas),
                                        active_elements=set(parent2.active_elements))

                child1 = self._mutate(child1)
                child2 = self._mutate(child2)

                self._evaluate(child1)
                self._evaluate(child2)

                new_population.append(child1)
                if len(new_population) < self.config.population_size:
                    new_population.append(child2)

            population = new_population

        # Final sort and extract best
        population.sort(key=lambda ind: ind.fitness)
        best = population[0]

        best_model = self._create_model_from_individual(best)

        # Try to get analysis for best model
        best_analysis = None
        try:
            best_analysis = TrussAnalyzer(best_model).analyze()
        except (ValueError, np.linalg.LinAlgError):
            pass

        removed = [eid for eid in self._all_elem_ids
                    if eid not in best.active_elements]

        final_cost = best.cost if best.is_feasible else best_model.total_cost
        cost_pct = ((final_cost - initial_cost) / initial_cost * 100
                    if initial_cost > 0 else 0.0)

        return GAResult(
            best_model=best_model,
            best_analysis=best_analysis,
            initial_cost=initial_cost,
            final_cost=final_cost,
            initial_weight=initial_weight,
            final_weight=best.weight if best.is_feasible else best_model.total_weight,
            cost_reduction_pct=cost_pct,
            generations_run=len(convergence),
            population_size=self.config.population_size,
            best_individual=best,
            convergence_history=convergence,
            removed_elements=removed,
            converged=stagnation_count > 30 or len(convergence) == self.config.generations,
        )
