"""
Visualization module for truss structures.

Renders truss geometry, deformed shapes, stress distributions,
and optimization comparison plots using matplotlib.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    from matplotlib.patches import FancyArrowPatch
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from ..core.truss_model import TrussModel, SupportType
from ..core.analysis import AnalysisResult


def _require_matplotlib():
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "matplotlib is required for visualization. "
            "Install with: pip install matplotlib"
        )


class TrussPlotter:
    """Visualizes truss structures, results, and optimization comparisons."""

    def __init__(self, figsize: tuple[float, float] = (12, 8)):
        _require_matplotlib()
        self.figsize = figsize

    def plot_geometry(self, model: TrussModel, ax=None,
                      show_labels: bool = True,
                      title: Optional[str] = None) -> None:
        """Plot the undeformed truss geometry."""
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=self.figsize)

        # Draw elements
        for elem in model.elements.values():
            ni = model.nodes[elem.node_i]
            nj = model.nodes[elem.node_j]
            ax.plot([ni.x, nj.x], [ni.y, nj.y], "b-", linewidth=2)
            if show_labels:
                mx = (ni.x + nj.x) / 2
                my = (ni.y + nj.y) / 2
                ax.annotate(str(elem.id), (mx, my), fontsize=8,
                            color="blue", ha="center",
                            bbox=dict(boxstyle="round,pad=0.2",
                                      facecolor="lightyellow", alpha=0.8))

        # Draw nodes
        for node in model.nodes.values():
            marker = "s" if node.support != SupportType.FREE else "o"
            color = "red" if node.support != SupportType.FREE else "black"
            ax.plot(node.x, node.y, marker, color=color, markersize=8, zorder=5)
            if show_labels:
                ax.annotate(str(node.id), (node.x, node.y),
                            textcoords="offset points", xytext=(5, 5),
                            fontsize=9, fontweight="bold")

        # Draw support symbols
        for node in model.nodes.values():
            if node.support == SupportType.PIN:
                self._draw_pin_support(ax, node.x, node.y)
            elif node.support == SupportType.ROLLER_X:
                self._draw_roller_support(ax, node.x, node.y, "x")
            elif node.support == SupportType.ROLLER_Y:
                self._draw_roller_support(ax, node.x, node.y, "y")

        # Draw loads
        max_load = max(
            (abs(l.fx) + abs(l.fy) for l in model.loads), default=1
        )
        for load in model.loads:
            node = model.nodes[load.node_id]
            scale = 0.3 * max(
                abs(model.nodes[n].x) for n in model.nodes
            ) / max_load if max_load > 0 else 0.5
            if abs(load.fx) > 0:
                ax.annotate("", xy=(node.x, node.y),
                            xytext=(node.x - load.fx * scale, node.y),
                            arrowprops=dict(arrowstyle="->", color="green", lw=2))
            if abs(load.fy) > 0:
                ax.annotate("", xy=(node.x, node.y),
                            xytext=(node.x, node.y - load.fy * scale),
                            arrowprops=dict(arrowstyle="->", color="green", lw=2))

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_title(title or model.name)
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

    def plot_deformed(self, model: TrussModel, result: AnalysisResult,
                      scale: float = 100.0, ax=None,
                      title: Optional[str] = None) -> None:
        """Plot original and deformed truss shape."""
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=self.figsize)

        u = result.displacements

        # Original (gray dashed)
        for elem in model.elements.values():
            ni = model.nodes[elem.node_i]
            nj = model.nodes[elem.node_j]
            ax.plot([ni.x, nj.x], [ni.y, nj.y], "--", color="gray",
                    linewidth=1, alpha=0.5)

        # Deformed (colored by stress)
        stresses = list(result.element_stresses.values())
        max_s = max(abs(s) for s in stresses) if stresses else 1
        norm = plt.Normalize(-max_s, max_s)
        cmap = cm.RdYlBu_r

        for elem in model.elements.values():
            ni = model.nodes[elem.node_i]
            nj = model.nodes[elem.node_j]
            di = u[2 * elem.node_i: 2 * elem.node_i + 2]
            dj = u[2 * elem.node_j: 2 * elem.node_j + 2]

            x_def = [ni.x + scale * di[0], nj.x + scale * dj[0]]
            y_def = [ni.y + scale * di[1], nj.y + scale * dj[1]]

            stress = result.element_stresses[elem.id]
            color = cmap(norm(stress))
            ax.plot(x_def, y_def, "-", color=color, linewidth=3)

        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, label="Axial Stress (Pa)")

        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_title(title or f"Deformed Shape (scale={scale}x)")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

    def plot_stress_distribution(self, result: AnalysisResult,
                                  ax=None, title: Optional[str] = None) -> None:
        """Bar chart of element stresses with yield limit line."""
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=self.figsize)

        elem_ids = sorted(result.element_stresses.keys())
        stresses = [result.element_stresses[eid] / 1e6 for eid in elem_ids]
        colors = ["red" if result.safety_factors[eid] < 1.0
                   else ("orange" if result.safety_factors[eid] < 1.5 else "green")
                   for eid in elem_ids]

        ax.bar(range(len(elem_ids)), stresses, color=colors, alpha=0.8)
        ax.set_xticks(range(len(elem_ids)))
        ax.set_xticklabels([str(eid) for eid in elem_ids])
        ax.set_xlabel("Element ID")
        ax.set_ylabel("Stress (MPa)")
        ax.set_title(title or "Element Stress Distribution")
        ax.axhline(y=0, color="black", linewidth=0.5)
        ax.grid(True, alpha=0.3, axis="y")

    def plot_optimization_comparison(self, initial: AnalysisResult,
                                      optimized: AnalysisResult,
                                      title: Optional[str] = None) -> None:
        """Side-by-side comparison of initial vs optimized areas and stresses."""
        fig, axes = plt.subplots(1, 2, figsize=(self.figsize[0], self.figsize[1]))

        elem_ids = sorted(initial.element_stresses.keys())
        x = range(len(elem_ids))

        # Stress comparison
        ax = axes[0]
        init_stress = [abs(initial.element_stresses[eid]) / 1e6 for eid in elem_ids]
        opt_stress = [abs(optimized.element_stresses[eid]) / 1e6 for eid in elem_ids]
        width = 0.35
        ax.bar([xi - width / 2 for xi in x], init_stress, width, label="Initial", alpha=0.7)
        ax.bar([xi + width / 2 for xi in x], opt_stress, width, label="Optimized", alpha=0.7)
        ax.set_xticks(list(x))
        ax.set_xticklabels([str(eid) for eid in elem_ids])
        ax.set_xlabel("Element ID")
        ax.set_ylabel("|Stress| (MPa)")
        ax.set_title("Stress Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        # Weight/cost summary
        ax = axes[1]
        labels = ["Weight (kg)", "Cost ($)"]
        init_vals = [initial.total_weight, initial.total_cost]
        opt_vals = [optimized.total_weight, optimized.total_cost]
        x2 = range(len(labels))
        ax.bar([xi - width / 2 for xi in x2], init_vals, width,
               label="Initial", alpha=0.7)
        ax.bar([xi + width / 2 for xi in x2], opt_vals, width,
               label="Optimized", alpha=0.7, color="green")
        ax.set_xticks(list(x2))
        ax.set_xticklabels(labels)
        ax.set_title("Weight & Cost Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        fig.suptitle(title or "Optimization Comparison", fontsize=14)
        plt.tight_layout()

    @staticmethod
    def _draw_pin_support(ax, x, y, size=0.3):
        triangle = plt.Polygon(
            [(x, y), (x - size / 2, y - size), (x + size / 2, y - size)],
            fill=False, edgecolor="red", linewidth=2
        )
        ax.add_patch(triangle)

    @staticmethod
    def _draw_roller_support(ax, x, y, direction, size=0.3):
        if direction == "x":
            triangle = plt.Polygon(
                [(x, y), (x - size / 2, y - size), (x + size / 2, y - size)],
                fill=False, edgecolor="red", linewidth=2
            )
            ax.add_patch(triangle)
            ax.plot([x - size / 2, x + size / 2], [y - size - 0.05, y - size - 0.05],
                    "r-", linewidth=2)
        else:
            triangle = plt.Polygon(
                [(x, y), (x - size, y - size / 2), (x - size, y + size / 2)],
                fill=False, edgecolor="red", linewidth=2
            )
            ax.add_patch(triangle)

    def show(self):
        plt.show()

    def save_figure(self, path: str, dpi: int = 150):
        plt.savefig(path, dpi=dpi, bbox_inches="tight")
