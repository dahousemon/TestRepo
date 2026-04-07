"""
Core data model for 2D truss structures.

Defines nodes, elements, materials, loads, and the composite TrussModel
that ties them together for analysis and optimization.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class SupportType(Enum):
    FREE = "free"
    PIN = "pin"           # Fixed in x and y
    ROLLER_X = "roller_x"  # Fixed in y, free in x
    ROLLER_Y = "roller_y"  # Fixed in x, free in y


@dataclass
class Node:
    id: int
    x: float
    y: float
    support: SupportType = SupportType.FREE

    @property
    def coords(self) -> tuple[float, float]:
        return (self.x, self.y)

    def is_constrained_x(self) -> bool:
        return self.support in (SupportType.PIN, SupportType.ROLLER_Y)

    def is_constrained_y(self) -> bool:
        return self.support in (SupportType.PIN, SupportType.ROLLER_X)


@dataclass
class Material:
    name: str
    E: float              # Young's modulus (Pa)
    density: float        # kg/m^3
    yield_stress: float   # Pa
    cost_per_kg: float = 1.0  # $/kg

    @classmethod
    def steel(cls) -> Material:
        return cls("Steel", E=200e9, density=7850, yield_stress=250e6, cost_per_kg=0.80)

    @classmethod
    def aluminum(cls) -> Material:
        return cls("Aluminum", E=69e9, density=2700, yield_stress=270e6, cost_per_kg=2.50)

    @classmethod
    def timber(cls) -> Material:
        return cls("Timber", E=12.5e9, density=600, yield_stress=40e6, cost_per_kg=0.50)


@dataclass
class Element:
    id: int
    node_i: int           # Start node ID
    node_j: int           # End node ID
    area: float           # Cross-sectional area (m^2)
    material: Material = field(default_factory=Material.steel)

    def length(self, nodes: dict[int, Node]) -> float:
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        return math.hypot(nj.x - ni.x, nj.y - ni.y)

    def angle(self, nodes: dict[int, Node]) -> float:
        ni, nj = nodes[self.node_i], nodes[self.node_j]
        return math.atan2(nj.y - ni.y, nj.x - ni.x)

    def weight(self, nodes: dict[int, Node]) -> float:
        return self.area * self.length(nodes) * self.material.density

    def cost(self, nodes: dict[int, Node]) -> float:
        return self.weight(nodes) * self.material.cost_per_kg


@dataclass
class Load:
    node_id: int
    fx: float = 0.0  # Force in x (N)
    fy: float = 0.0  # Force in y (N)


class TrussModel:
    """Complete 2D truss model containing nodes, elements, loads, and materials."""

    def __init__(self, name: str = "Untitled Truss"):
        self.name = name
        self.nodes: dict[int, Node] = {}
        self.elements: dict[int, Element] = {}
        self.loads: list[Load] = []

    def add_node(self, id: int, x: float, y: float,
                 support: SupportType = SupportType.FREE) -> Node:
        node = Node(id=id, x=x, y=y, support=support)
        self.nodes[id] = node
        return node

    def add_element(self, id: int, node_i: int, node_j: int, area: float,
                    material: Optional[Material] = None) -> Element:
        if node_i not in self.nodes or node_j not in self.nodes:
            raise ValueError(f"Nodes {node_i} and {node_j} must exist before adding element")
        mat = material or Material.steel()
        elem = Element(id=id, node_i=node_i, node_j=node_j, area=area, material=mat)
        self.elements[id] = elem
        return elem

    def add_load(self, node_id: int, fx: float = 0.0, fy: float = 0.0) -> Load:
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} must exist before adding load")
        load = Load(node_id=node_id, fx=fx, fy=fy)
        self.loads.append(load)
        return load

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_elements(self) -> int:
        return len(self.elements)

    @property
    def num_dofs(self) -> int:
        return 2 * self.num_nodes

    @property
    def total_weight(self) -> float:
        return sum(e.weight(self.nodes) for e in self.elements.values())

    @property
    def total_cost(self) -> float:
        return sum(e.cost(self.nodes) for e in self.elements.values())

    def get_constrained_dofs(self) -> list[int]:
        constrained = []
        for node in self.nodes.values():
            if node.is_constrained_x():
                constrained.append(2 * node.id)
            if node.is_constrained_y():
                constrained.append(2 * node.id + 1)
        return sorted(constrained)

    def get_free_dofs(self) -> list[int]:
        constrained = set(self.get_constrained_dofs())
        return [i for i in range(self.num_dofs) if i not in constrained]

    def validate(self) -> list[str]:
        errors = []
        if self.num_nodes < 2:
            errors.append("Truss must have at least 2 nodes")
        if self.num_elements < 1:
            errors.append("Truss must have at least 1 element")
        if not self.loads:
            errors.append("Truss must have at least 1 load")

        constrained = self.get_constrained_dofs()
        if len(constrained) < 3:
            errors.append("Truss needs at least 3 constrained DOFs for stability")

        for elem in self.elements.values():
            if elem.area <= 0:
                errors.append(f"Element {elem.id} has non-positive area")
            if elem.length(self.nodes) == 0:
                errors.append(f"Element {elem.id} has zero length")

        return errors

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "nodes": [
                {"id": n.id, "x": n.x, "y": n.y, "support": n.support.value}
                for n in self.nodes.values()
            ],
            "elements": [
                {
                    "id": e.id, "node_i": e.node_i, "node_j": e.node_j,
                    "area": e.area,
                    "material": {
                        "name": e.material.name, "E": e.material.E,
                        "density": e.material.density,
                        "yield_stress": e.material.yield_stress,
                        "cost_per_kg": e.material.cost_per_kg,
                    }
                }
                for e in self.elements.values()
            ],
            "loads": [
                {"node_id": l.node_id, "fx": l.fx, "fy": l.fy}
                for l in self.loads
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> TrussModel:
        model = cls(name=data.get("name", "Untitled"))
        for nd in data["nodes"]:
            model.add_node(nd["id"], nd["x"], nd["y"], SupportType(nd["support"]))
        for ed in data["elements"]:
            mat_data = ed["material"]
            mat = Material(
                name=mat_data["name"], E=mat_data["E"],
                density=mat_data["density"],
                yield_stress=mat_data["yield_stress"],
                cost_per_kg=mat_data.get("cost_per_kg", 1.0),
            )
            model.add_element(ed["id"], ed["node_i"], ed["node_j"], ed["area"], mat)
        for ld in data["loads"]:
            model.add_load(ld["node_id"], ld["fx"], ld["fy"])
        return model

    def save(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> TrussModel:
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def __repr__(self) -> str:
        return (f"TrussModel('{self.name}', nodes={self.num_nodes}, "
                f"elements={self.num_elements}, loads={len(self.loads)})")
