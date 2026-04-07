"""
Finite Element Analysis for 2D truss structures using the Direct Stiffness Method.

Computes displacements, reaction forces, element stresses, and safety factors.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .truss_model import TrussModel


@dataclass
class AnalysisResult:
    """Results from a truss FEA analysis."""
    displacements: np.ndarray       # (num_dofs,) nodal displacements
    reactions: np.ndarray            # (num_dofs,) reaction forces
    element_forces: dict[int, float] # element_id -> axial force (+ = tension)
    element_stresses: dict[int, float]  # element_id -> axial stress
    safety_factors: dict[int, float]    # element_id -> safety factor
    max_displacement: float
    max_stress: float
    total_weight: float
    total_cost: float
    is_feasible: bool                # True if all safety factors >= 1.0

    def summary(self) -> str:
        lines = [
            "=== Truss Analysis Results ===",
            f"Max displacement: {self.max_displacement:.6f} m",
            f"Max stress:       {self.max_stress / 1e6:.2f} MPa",
            f"Total weight:     {self.total_weight:.2f} kg",
            f"Total cost:       ${self.total_cost:.2f}",
            f"Feasible:         {'Yes' if self.is_feasible else 'NO - overstressed!'}",
            "",
            "Element Results:",
            f"{'ID':>4} {'Force (kN)':>12} {'Stress (MPa)':>14} {'SF':>8} {'Status':>10}",
            "-" * 52,
        ]
        for eid in sorted(self.element_forces):
            force = self.element_forces[eid] / 1e3
            stress = self.element_stresses[eid] / 1e6
            sf = self.safety_factors[eid]
            status = "OK" if sf >= 1.0 else "FAIL"
            typ = "T" if self.element_forces[eid] >= 0 else "C"
            lines.append(f"{eid:>4} {force:>12.3f} {stress:>14.3f} {sf:>8.2f} {status:>6} ({typ})")
        return "\n".join(lines)


class TrussAnalyzer:
    """Performs FEA on a TrussModel using the direct stiffness method."""

    def __init__(self, model: TrussModel):
        self.model = model

    def _element_stiffness_global(self, elem_id: int) -> np.ndarray:
        """Compute 4x4 element stiffness matrix in global coordinates."""
        elem = self.model.elements[elem_id]
        nodes = self.model.nodes
        L = elem.length(nodes)
        theta = elem.angle(nodes)
        c = math.cos(theta)
        s = math.sin(theta)

        k = elem.material.E * elem.area / L
        # Transformation: [c^2, cs, -c^2, -cs; cs, s^2, -cs, -s^2; ...]
        ke = k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s],
        ])
        return ke

    def _assemble_global_stiffness(self) -> np.ndarray:
        """Assemble the global stiffness matrix."""
        n_dofs = self.model.num_dofs
        K = np.zeros((n_dofs, n_dofs))

        for elem in self.model.elements.values():
            ke = self._element_stiffness_global(elem.id)
            # DOF mapping: node_i -> [2*i, 2*i+1], node_j -> [2*j, 2*j+1]
            dofs = [2 * elem.node_i, 2 * elem.node_i + 1,
                    2 * elem.node_j, 2 * elem.node_j + 1]
            for i in range(4):
                for j in range(4):
                    K[dofs[i], dofs[j]] += ke[i, j]

        return K

    def _assemble_force_vector(self) -> np.ndarray:
        """Assemble the global force vector from applied loads."""
        F = np.zeros(self.model.num_dofs)
        for load in self.model.loads:
            F[2 * load.node_id] += load.fx
            F[2 * load.node_id + 1] += load.fy
        return F

    def analyze(self) -> AnalysisResult:
        """Run the full FEA analysis. Returns an AnalysisResult."""
        errors = self.model.validate()
        if errors:
            raise ValueError(f"Model validation failed: {'; '.join(errors)}")

        K = self._assemble_global_stiffness()
        F = self._assemble_force_vector()

        free_dofs = self.model.get_free_dofs()
        constrained_dofs = self.model.get_constrained_dofs()

        # Solve reduced system: K_ff * u_f = F_f
        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f = F[free_dofs]

        try:
            u_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            raise ValueError("Stiffness matrix is singular - truss may be a mechanism")

        # Full displacement vector
        u = np.zeros(self.model.num_dofs)
        for i, dof in enumerate(free_dofs):
            u[dof] = u_f[i]

        # Reaction forces
        reactions = K @ u - F

        # Element forces and stresses
        element_forces = {}
        element_stresses = {}
        safety_factors = {}

        for elem in self.model.elements.values():
            nodes = self.model.nodes
            L = elem.length(nodes)
            theta = elem.angle(nodes)
            c = math.cos(theta)
            s = math.sin(theta)

            # Local displacements
            dofs = [2 * elem.node_i, 2 * elem.node_i + 1,
                    2 * elem.node_j, 2 * elem.node_j + 1]
            u_elem = u[dofs]

            # Axial deformation in local coords
            delta = (-c * u_elem[0] - s * u_elem[1] +
                     c * u_elem[2] + s * u_elem[3])

            axial_force = elem.material.E * elem.area * delta / L
            axial_stress = axial_force / elem.area

            element_forces[elem.id] = axial_force
            element_stresses[elem.id] = axial_stress

            if abs(axial_stress) > 0:
                safety_factors[elem.id] = elem.material.yield_stress / abs(axial_stress)
            else:
                safety_factors[elem.id] = float("inf")

        max_disp = float(np.max(np.abs(u)))
        max_stress = max(abs(s) for s in element_stresses.values()) if element_stresses else 0.0
        is_feasible = all(sf >= 1.0 for sf in safety_factors.values())

        return AnalysisResult(
            displacements=u,
            reactions=reactions,
            element_forces=element_forces,
            element_stresses=element_stresses,
            safety_factors=safety_factors,
            max_displacement=max_disp,
            max_stress=max_stress,
            total_weight=self.model.total_weight,
            total_cost=self.model.total_cost,
            is_feasible=is_feasible,
        )
