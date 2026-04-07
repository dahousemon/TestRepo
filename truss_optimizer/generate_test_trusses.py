"""
Generate 100 test truss JSON files with varied topologies, spans, materials, and loads.

Produces a diverse dataset covering:
  - Warren, Pratt, Howe trusses (3-8 panels)
  - Simple triangle trusses
  - Mixed-material trusses (steel + aluminum)
  - Various span/height ratios (5m-30m span, 1m-8m height)
  - Light to heavy loading (10kN - 500kN)
  - Different support conditions

Output: truss_optimizer/data/test_trusses/truss_001.json ... truss_100.json
        truss_optimizer/data/test_trusses/manifest.json (index of all trusses)
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from truss_optimizer.core.truss_model import TrussModel, Material, SupportType


def generate_warren(idx: int, rng: random.Random) -> TrussModel:
    n_panels = rng.randint(3, 8)
    span = rng.uniform(6, 25)
    height = rng.uniform(span * 0.15, span * 0.35)
    load = rng.uniform(20e3, 400e3)
    mat = rng.choice([Material.steel(), Material.aluminum()])
    pw = span / n_panels

    model = TrussModel(f"Warren_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels):
        model.add_node(n_panels + 1 + i, (i + 0.5) * pw, height)

    area = rng.uniform(10e-4, 60e-4)
    eid = 0
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, mat); eid += 1
    for i in range(n_panels):
        top = n_panels + 1 + i
        model.add_element(eid, i, top, area, mat); eid += 1
        model.add_element(eid, top, i + 1, area, mat); eid += 1
    for i in range(n_panels - 1):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, mat); eid += 1
    for i in range(1, n_panels):
        model.add_load(i, 0, -load)
    return model


def generate_pratt(idx: int, rng: random.Random) -> TrussModel:
    n_panels = rng.randint(3, 7)
    span = rng.uniform(8, 30)
    height = rng.uniform(span * 0.15, span * 0.3)
    load = rng.uniform(20e3, 350e3)
    mat = rng.choice([Material.steel(), Material.aluminum()])
    pw = span / n_panels

    model = TrussModel(f"Pratt_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels + 1):
        model.add_node(n_panels + 1 + i, i * pw, height)

    area = rng.uniform(10e-4, 50e-4)
    eid = 0
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, mat); eid += 1
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, mat); eid += 1
    for i in range(n_panels + 1):
        model.add_element(eid, i, n_panels + 1 + i, area, mat); eid += 1
    mid = n_panels / 2
    for i in range(n_panels):
        if i < mid:
            model.add_element(eid, i, n_panels + 2 + i, area, mat)
        else:
            model.add_element(eid, i + 1, n_panels + 1 + i, area, mat)
        eid += 1
    for i in range(1, n_panels):
        model.add_load(i, 0, -load)
    return model


def generate_howe(idx: int, rng: random.Random) -> TrussModel:
    n_panels = rng.randint(3, 7)
    span = rng.uniform(8, 28)
    height = rng.uniform(span * 0.15, span * 0.35)
    load = rng.uniform(15e3, 300e3)
    mat = rng.choice([Material.steel(), Material.aluminum(), Material.timber()])
    pw = span / n_panels

    model = TrussModel(f"Howe_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels + 1):
        model.add_node(n_panels + 1 + i, i * pw, height)

    area = rng.uniform(10e-4, 55e-4)
    eid = 0
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, mat); eid += 1
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, mat); eid += 1
    for i in range(n_panels + 1):
        model.add_element(eid, i, n_panels + 1 + i, area, mat); eid += 1
    mid = n_panels / 2
    for i in range(n_panels):
        if i < mid:
            model.add_element(eid, i + 1, n_panels + 1 + i, area, mat)
        else:
            model.add_element(eid, i, n_panels + 2 + i, area, mat)
        eid += 1
    for i in range(1, n_panels):
        model.add_load(i, 0, -load)
    return model


def generate_mixed_material(idx: int, rng: random.Random) -> TrussModel:
    """Bridge truss with steel chords and aluminum diagonals."""
    n_panels = rng.randint(3, 6)
    span = rng.uniform(8, 20)
    height = rng.uniform(2, 5)
    load = rng.uniform(30e3, 250e3)
    pw = span / n_panels

    steel = Material.steel()
    alum = Material.aluminum()

    model = TrussModel(f"Mixed_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels + 1):
        model.add_node(n_panels + 1 + i, i * pw, height)

    area = rng.uniform(15e-4, 50e-4)
    eid = 0
    # Bottom chord: steel
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, steel); eid += 1
    # Top chord: steel
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, steel); eid += 1
    # Verticals: aluminum
    for i in range(n_panels + 1):
        model.add_element(eid, i, n_panels + 1 + i, area * 0.7, alum); eid += 1
    # Diagonals: aluminum
    for i in range(n_panels):
        model.add_element(eid, i, n_panels + 2 + i, area * 0.8, alum); eid += 1

    for i in range(1, n_panels):
        model.add_load(i, 0, -load)
    return model


def generate_roof_truss(idx: int, rng: random.Random) -> TrussModel:
    """Pitched roof truss (triangular top chord)."""
    n_panels = rng.choice([4, 6, 8])
    span = rng.uniform(6, 16)
    peak_height = rng.uniform(1.5, 4)
    load = rng.uniform(10e3, 80e3)
    mat = rng.choice([Material.steel(), Material.timber()])
    pw = span / n_panels

    model = TrussModel(f"Roof_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels + 1):
        x = i * pw
        y = peak_height * (1 - abs(2 * x / span - 1))
        model.add_node(n_panels + 1 + i, x, y)

    area = rng.uniform(8e-4, 40e-4)
    eid = 0
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, mat); eid += 1
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, mat); eid += 1
    # Verticals -- skip where top and bottom nodes coincide (at supports)
    for i in range(n_panels + 1):
        top_id = n_panels + 1 + i
        bot = model.nodes[i]
        top = model.nodes[top_id]
        if abs(top.x - bot.x) > 1e-6 or abs(top.y - bot.y) > 1e-6:
            model.add_element(eid, i, top_id, area, mat)
        eid += 1
    # Diagonals -- skip if top target node coincides with bottom source
    for i in range(n_panels):
        top_id = n_panels + 2 + i
        bot = model.nodes[i]
        top = model.nodes[top_id]
        if abs(top.x - bot.x) > 1e-6 or abs(top.y - bot.y) > 1e-6:
            model.add_element(eid, i, top_id, area, mat)
        eid += 1

    # Roof load on top chord (skip nodes at supports where height=0)
    for i in range(1, n_panels):
        top_id = n_panels + 1 + i
        if model.nodes[top_id].y > 0.01:
            model.add_load(top_id, 0, -load)
    # Ensure at least one load exists
    if not model.loads:
        model.add_load(n_panels + 1 + n_panels // 2, 0, -load)
    return model


def generate_simple_triangle(idx: int, rng: random.Random) -> TrussModel:
    span = rng.uniform(3, 10)
    height = rng.uniform(1, span * 0.5)
    load = rng.uniform(10e3, 200e3)
    mat = rng.choice([Material.steel(), Material.aluminum()])

    model = TrussModel(f"Triangle_{span:.0f}m")
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, span, 0.0, SupportType.ROLLER_X)
    model.add_node(2, span / 2, height)
    area = rng.uniform(10e-4, 50e-4)
    model.add_element(0, 0, 2, area, mat)
    model.add_element(1, 2, 1, area, mat)
    model.add_element(2, 0, 1, area, mat)
    model.add_load(2, 0, -load)
    return model


def generate_heavy_industrial(idx: int, rng: random.Random) -> TrussModel:
    """Heavy-duty industrial truss with large loads."""
    n_panels = rng.randint(4, 8)
    span = rng.uniform(15, 30)
    height = rng.uniform(3, 6)
    load = rng.uniform(200e3, 500e3)
    pw = span / n_panels
    steel = Material.steel()

    model = TrussModel(f"Industrial_{n_panels}p_{span:.0f}m")
    for i in range(n_panels + 1):
        sup = SupportType.PIN if i == 0 else (
            SupportType.ROLLER_X if i == n_panels else SupportType.FREE)
        model.add_node(i, i * pw, 0.0, sup)
    for i in range(n_panels + 1):
        model.add_node(n_panels + 1 + i, i * pw, height)

    area = rng.uniform(30e-4, 80e-4)
    eid = 0
    for i in range(n_panels):
        model.add_element(eid, i, i + 1, area, steel); eid += 1
    for i in range(n_panels):
        model.add_element(eid, n_panels + 1 + i, n_panels + 2 + i, area, steel); eid += 1
    for i in range(n_panels + 1):
        model.add_element(eid, i, n_panels + 1 + i, area, steel); eid += 1
    for i in range(n_panels):
        model.add_element(eid, i, n_panels + 2 + i, area, steel); eid += 1
    # Every bottom node gets loaded
    for i in range(1, n_panels):
        model.add_load(i, 0, -load)
    return model


GENERATORS = [
    (generate_warren, 20),
    (generate_pratt, 20),
    (generate_howe, 15),
    (generate_mixed_material, 15),
    (generate_roof_truss, 12),
    (generate_simple_triangle, 8),
    (generate_heavy_industrial, 10),
]


def main():
    out_dir = Path("truss_optimizer/data/test_trusses")
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    manifest = []
    idx = 1

    for generator, count in GENERATORS:
        for _ in range(count):
            model = generator(idx, rng)
            filename = f"truss_{idx:03d}.json"
            filepath = out_dir / filename
            model.save(filepath)

            manifest.append({
                "id": idx,
                "file": filename,
                "name": model.name,
                "topology": generator.__name__.replace("generate_", ""),
                "nodes": model.num_nodes,
                "elements": model.num_elements,
                "loads": len(model.loads),
                "weight_kg": round(model.total_weight, 2),
                "cost_usd": round(model.total_cost, 2),
            })
            idx += 1

    # Save manifest
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {idx - 1} test trusses in {out_dir}/")
    print(f"Manifest saved to {out_dir}/manifest.json")

    # Summary
    from collections import Counter
    types = Counter(m["topology"] for m in manifest)
    print("\nTopology breakdown:")
    for t, c in sorted(types.items()):
        print(f"  {t}: {c}")
    print(f"\nNode range: {min(m['nodes'] for m in manifest)}-{max(m['nodes'] for m in manifest)}")
    print(f"Element range: {min(m['elements'] for m in manifest)}-{max(m['elements'] for m in manifest)}")
    print(f"Weight range: {min(m['weight_kg'] for m in manifest):.0f}-{max(m['weight_kg'] for m in manifest):.0f} kg")
    print(f"Cost range: ${min(m['cost_usd'] for m in manifest):.0f}-${max(m['cost_usd'] for m in manifest):.0f}")


if __name__ == "__main__":
    main()
