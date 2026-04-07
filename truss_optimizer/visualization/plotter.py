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

    def plot_cost_vs_weight_comparison(self, comparison, title: Optional[str] = None) -> None:
        """Plot a detailed cost vs weight comparison from a ComparisonResult."""
        from ..core.optimizer import ComparisonResult
        cr: ComparisonResult = comparison

        fig, axes = plt.subplots(2, 2, figsize=(self.figsize[0], self.figsize[1] + 2))

        # Top-left: Weight and Cost bars
        ax = axes[0][0]
        labels = ["Weight (kg)", "Cost ($)"]
        initial = [cr.initial_analysis.total_weight, cr.initial_analysis.total_cost]
        min_w = [cr.weight_result.final_weight, cr.weight_result.final_cost]
        min_c = [cr.cost_result.final_weight, cr.cost_result.final_cost]
        x = np.arange(len(labels))
        w = 0.25
        ax.bar(x - w, initial, w, label="Initial", color="#999999", alpha=0.8)
        ax.bar(x, min_w, w, label="Min Weight", color="#2196F3", alpha=0.8)
        ax.bar(x + w, min_c, w, label="Min Cost", color="#4CAF50", alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend(fontsize=8)
        ax.set_title("Weight & Cost Comparison")
        ax.grid(True, alpha=0.3, axis="y")

        # Top-right: Element areas comparison
        ax = axes[0][1]
        eids = sorted(cr.weight_result.optimized_areas.keys())
        x = np.arange(len(eids))
        areas_w = [cr.weight_result.optimized_areas[e] * 1e4 for e in eids]
        areas_c = [cr.cost_result.optimized_areas[e] * 1e4 for e in eids]
        ax.bar(x - 0.2, areas_w, 0.4, label="Min Weight", color="#2196F3", alpha=0.8)
        ax.bar(x + 0.2, areas_c, 0.4, label="Min Cost", color="#4CAF50", alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([str(e) for e in eids], fontsize=7)
        ax.set_xlabel("Element ID")
        ax.set_ylabel("Area (cm²)")
        ax.legend(fontsize=8)
        ax.set_title("Cross-Section Areas")
        ax.grid(True, alpha=0.3, axis="y")

        # Bottom-left: Stress comparison
        ax = axes[1][0]
        stress_w = [abs(cr.weight_result.analysis.element_stresses[e]) / 1e6 for e in eids]
        stress_c = [abs(cr.cost_result.analysis.element_stresses[e]) / 1e6 for e in eids]
        ax.bar(x - 0.2, stress_w, 0.4, label="Min Weight", color="#2196F3", alpha=0.8)
        ax.bar(x + 0.2, stress_c, 0.4, label="Min Cost", color="#4CAF50", alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([str(e) for e in eids], fontsize=7)
        ax.set_xlabel("Element ID")
        ax.set_ylabel("|Stress| (MPa)")
        ax.legend(fontsize=8)
        ax.set_title("Stress Distribution")
        ax.grid(True, alpha=0.3, axis="y")

        # Bottom-right: Summary text
        ax = axes[1][1]
        ax.axis("off")
        w_res = cr.weight_result
        c_res = cr.cost_result
        text = (
            f"Initial Design\n"
            f"  Weight: {cr.initial_analysis.total_weight:.1f} kg\n"
            f"  Cost:   ${cr.initial_analysis.total_cost:.2f}\n\n"
            f"Min Weight Design\n"
            f"  Weight: {w_res.final_weight:.1f} kg ({w_res.weight_reduction_pct:+.1f}%)\n"
            f"  Cost:   ${w_res.final_cost:.2f} ({w_res.cost_reduction_pct:+.1f}%)\n\n"
            f"Min Cost Design\n"
            f"  Weight: {c_res.final_weight:.1f} kg ({c_res.weight_reduction_pct:+.1f}%)\n"
            f"  Cost:   ${c_res.final_cost:.2f} ({c_res.cost_reduction_pct:+.1f}%)\n\n"
        )
        if w_res.final_cost > c_res.final_cost and w_res.final_weight < c_res.final_weight:
            savings_w = c_res.final_weight - w_res.final_weight
            savings_c = w_res.final_cost - c_res.final_cost
            text += (f"Tradeoff: ${savings_c:.2f} saved in cost\n"
                     f"costs {savings_w:.1f} kg extra weight")
        ax.text(0.05, 0.95, text, transform=ax.transAxes, fontsize=9,
                verticalalignment="top", fontfamily="monospace",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

        fig.suptitle(title or "Cost vs Weight Optimization", fontsize=14, fontweight="bold")
        plt.tight_layout()

    def plot_pareto_front(self, points, title: Optional[str] = None) -> None:
        """Plot the Pareto front from a list of ParetoPoints."""
        fig, axes = plt.subplots(1, 2, figsize=self.figsize)

        weights = [p.weight for p in points]
        costs = [p.cost for p in points]
        alphas = [p.alpha for p in points]
        feasible = [p.is_feasible for p in points]

        # Left: Pareto front (weight vs cost)
        ax = axes[0]
        for i, p in enumerate(points):
            color = "#4CAF50" if p.is_feasible else "#F44336"
            marker = "o" if p.is_feasible else "x"
            ax.plot(p.weight, p.cost, marker, color=color, markersize=10, zorder=5)
            ax.annotate(f"{p.alpha:.1f}", (p.weight, p.cost),
                        textcoords="offset points", xytext=(5, 5), fontsize=7)

        # Connect feasible points
        feas_pts = [(p.weight, p.cost) for p in points if p.is_feasible]
        if feas_pts:
            fw, fc = zip(*feas_pts)
            ax.plot(fw, fc, "--", color="gray", alpha=0.5, zorder=1)

        ax.set_xlabel("Weight (kg)")
        ax.set_ylabel("Cost ($)")
        ax.set_title("Pareto Front: Weight vs Cost")
        ax.grid(True, alpha=0.3)

        # Mark extremes
        if feas_pts:
            min_w_idx = weights.index(min(w for w, p in zip(weights, points) if p.is_feasible))
            min_c_idx = costs.index(min(c for c, p in zip(costs, points) if p.is_feasible))
            ax.annotate("Min Weight", (points[min_w_idx].weight, points[min_w_idx].cost),
                        fontsize=8, fontweight="bold", color="#2196F3",
                        textcoords="offset points", xytext=(-10, -15))
            ax.annotate("Min Cost", (points[min_c_idx].weight, points[min_c_idx].cost),
                        fontsize=8, fontweight="bold", color="#4CAF50",
                        textcoords="offset points", xytext=(-10, 10))

        # Right: Alpha sweep showing weight and cost trends
        ax = axes[1]
        ax.plot(alphas, weights, "o-", color="#2196F3", label="Weight (kg)", markersize=6)
        ax2 = ax.twinx()
        ax2.plot(alphas, costs, "s-", color="#4CAF50", label="Cost ($)", markersize=6)
        ax.set_xlabel("Alpha (0=min cost, 1=min weight)")
        ax.set_ylabel("Weight (kg)", color="#2196F3")
        ax2.set_ylabel("Cost ($)", color="#4CAF50")
        ax.set_title("Objective Sweep")
        ax.grid(True, alpha=0.3)

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc="center right", fontsize=8)

        fig.suptitle(title or "Pareto Front Analysis", fontsize=14, fontweight="bold")
        plt.tight_layout()

    def show(self):
        plt.show()

    def save_figure(self, path: str, dpi: int = 150):
        plt.savefig(path, dpi=dpi, bbox_inches="tight")
