"""
generate_multiobj_data.py — Generate multi-objective training data
For each ISPD 2005 chip, compute 5 quality metrics from the reference placement:
  - HPWL (wirelength)
  - Timing (estimated critical path delay)
  - Power (estimated dynamic power)
  - Area (sum of cell areas)
  - Congestion (estimated routing density)

This is the training data for our multi-objective predictors.
"""

import sys
import json
import time
import math
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from chipmind.core import parse_def, compute_hpwl
from chipmind.core.bookshelf import parse_bookshelf


def compute_area(components: dict) -> float:
    """Sum of cell sizes = total silicon area."""
    return sum(pos.get("width", 1) * pos.get("height", 1)
               for pos in components.values())


def estimate_timing(components: dict, nets: list) -> float:
    """
    Estimate critical path delay (in ps) using a simple RC model.

    Critical path ≈ longest chain of gates + wire delays.
    Wire delay ≈ HPWL * resistance_per_unit_length.
    """
    # Build cell -> net index
    cell_nets = defaultdict(list)
    for i, net in enumerate(nets):
        for c in net["components"]:
            if c in components:
                cell_nets[c].append(i)

    # Estimate wire delay: HPWL per net, scaled
    # (real wire delay = R*C per unit length, ~100ps/mm in 45nm)
    hpwl_per_net = []
    for net in nets:
        cells = [c for c in net["components"] if c in components]
        if len(cells) < 2:
            continue
        xs = [components[c]["x"] for c in cells]
        ys = [components[c]["y"] for c in cells]
        net_hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
        hpwl_per_net.append(net_hpwl)
    total_hpwl = sum(hpwl_per_net)

    # Simple timing model: critical path ≈ alpha * HPWL + beta * num_gates
    # Empirically tuned to give reasonable values (~ns for small chips)
    alpha = 0.0005  # ps per db unit
    beta = 0.05     # ps per gate

    n_gates = len(components)
    timing_ps = alpha * total_hpwl + beta * n_gates
    return timing_ps  # in ps


def estimate_power(components: dict, nets: list) -> float:
    """
    Estimate dynamic power consumption (in mW).
    Power = sum_over_nets of (toggle_rate * capacitance * VDD^2 * frequency)
    Approximated as: P = k * (HPWL * wire_capacitance) + base_power
    """
    cell_nets = defaultdict(list)
    for i, net in enumerate(nets):
        for c in net["components"]:
            if c in components:
                cell_nets[c].append(i)

    # Compute HPWL
    hpwl_per_net = []
    for net in nets:
        cells = [c for c in net["components"] if c in components]
        if len(cells) < 2:
            continue
        xs = [components[c]["x"] for c in cells]
        ys = [components[c]["y"] for c in cells]
        net_hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
        hpwl_per_net.append(net_hpwl)
    total_hpwl = sum(hpwl_per_net)

    # Power model: dynamic power scales with wirelength (more wire = more capacitance)
    # Static power scales with cell count
    # At 45nm, VDD=1.0V, freq=100MHz
    toggle_rate = 0.1  # average activity
    wire_cap_per_db = 0.1e-15  # F/db unit
    vdd = 1.0  # V
    freq = 100e6  # Hz

    dynamic_power = toggle_rate * wire_cap_per_db * total_hpwl * (vdd ** 2) * freq
    static_power = 1e-9 * len(components)  # 1 nW per cell
    total_power_w = dynamic_power + static_power
    return total_power_w * 1000  # convert to mW


def estimate_congestion(components: dict, nets: list, die: dict, grid_size: int = 50) -> dict:
    """
    Estimate routing congestion.
    Divide die into a grid. For each cell, count how many nets pass through.
    Return: max_congestion, mean_congestion, congestion_distribution.
    """
    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]
    cell_w = die_w / grid_size
    cell_h = die_h / grid_size

    # For each net, mark the grid cells it passes through
    grid_congestion = np.zeros((grid_size, grid_size), dtype=np.int32)

    for net in nets:
        cells = [c for c in net["components"] if c in components]
        if len(cells) < 2:
            continue
        # Bounding box
        xs = [components[c]["x"] for c in cells]
        ys = [components[c]["y"] for c in cells]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        # Mark cells in the bounding box
        gx_min = int((x_min - die["x1"]) / cell_w)
        gx_max = int((x_max - die["x1"]) / cell_w)
        gy_min = int((y_min - die["y1"]) / cell_h)
        gy_max = int((y_max - die["y1"]) / cell_h)
        gx_min = max(0, min(grid_size - 1, gx_min))
        gx_max = max(0, min(grid_size - 1, gx_max))
        gy_min = max(0, min(grid_size - 1, gy_min))
        gy_max = max(0, min(grid_size - 1, gy_max))
        grid_congestion[gx_min:gx_max+1, gy_min:gy_max+1] += 1

    return {
        "max_congestion": int(grid_congestion.max()),
        "mean_congestion": float(grid_congestion.mean()),
        "median_congestion": float(np.median(grid_congestion)),
        "std_congestion": float(grid_congestion.std()),
    }


def chip_features(chip: dict) -> dict:
    """Compute per-chip features for the multi-objective predictors."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]

    # Net count per cell
    cell_nets = defaultdict(int)
    net_sizes = []
    for net in nets:
        net_cells = [c for c in net["components"] if c in components]
        if len(net_cells) >= 2:
            net_sizes.append(len(net_cells))
            for c in net_cells:
                cell_nets[c] += 1

    return {
        "n_cells": len(components),
        "n_nets": len(nets),
        "avg_net_size": float(np.mean(net_sizes)) if net_sizes else 0.0,
        "max_net_size": int(max(net_sizes)) if net_sizes else 0,
        "avg_cell_degree": float(np.mean(list(cell_nets.values()))) if cell_nets else 0.0,
        "max_cell_degree": max(cell_nets.values()) if cell_nets else 0,
        "die_area": float((die["x2"] - die["x1"]) * (die["y2"] - die["y1"])),
        "die_aspect": float((die["x2"] - die["x1"]) / max(1, die["y2"] - die["y1"])),
        "hpwl": float(compute_hpwl(chip)["total_hpwl"]),
    }


def main():
    data_path = Path(__file__).parent / "data" / "ispd_training_data.json"
    save_path = Path(__file__).parent / "data" / "multiobj_training_data.json"

    print("=" * 60)
    print("  ChipMind — Multi-objective Training Data Generator")
    print("=" * 60)

    print(f"\nLoading: {data_path}")
    with open(data_path) as f:
        chips = json.load(f)
    print(f"  {len(chips)} chips")

    training_data = []
    start = time.time()

    for i, chip in enumerate(chips):
        components = chip["components"]
        nets = chip["nets"]
        die = chip["die"]

        # Compute 5 metrics
        hpwl = compute_hpwl(chip)["total_hpwl"]
        area = compute_area(components)
        timing = estimate_timing(components, nets)
        power = estimate_power(components, nets)
        cong = estimate_congestion(components, nets, die)
        feats = chip_features(chip)

        training_data.append({
            "name": chip["name"],
            "features": feats,
            "metrics": {
                "hpwl": hpwl,
                "area": area,
                "timing_ps": timing,
                "power_mw": power,
                **cong,
            },
        })

        if (i + 1) % 20 == 0 or i == 0:
            elapsed = time.time() - start
            print(f"  [{i+1}/{len(chips)}] HPWL={hpwl:,}  area={area:,.0f}  "
                  f"timing={timing:.1f}ps  power={power:.2f}mW  "
                  f"max_cong={cong['max_congestion']}  ({elapsed:.1f}s)", flush=True)

    with open(save_path, "w") as f:
        json.dump(training_data, f, indent=2)

    total_time = time.time() - start
    print(f"\n{'='*60}")
    print(f"  Generated {len(training_data)} samples in {total_time:.1f}s")
    print(f"  Saved to: {save_path}")
    print(f"\nMetric ranges:")
    h = [d["metrics"]["hpwl"] for d in training_data]
    t = [d["metrics"]["timing_ps"] for d in training_data]
    p = [d["metrics"]["power_mw"] for d in training_data]
    a = [d["metrics"]["area"] for d in training_data]
    c = [d["metrics"]["max_congestion"] for d in training_data]
    print(f"  HPWL:    {min(h):>12,}  -  {max(h):>12,}")
    print(f"  Timing:  {min(t):>12.1f}  -  {max(t):>12.1f} ps")
    print(f"  Power:   {min(p):>12.4f}  -  {max(p):>12.4f} mW")
    print(f"  Area:    {min(a):>12,.0f}  -  {max(a):>12,.0f}")
    print(f"  Cong:    {min(c):>12}  -  {max(c):>12}")


if __name__ == "__main__":
    main()
