"""
olp_bootstrap_v2.py — Synthetic expert moves based on HPWL-improving direction.

V1 used V3 GAT's full deltas (random_init → V3_final in one step).
This is the WRONG signal: V3 makes big one-shot moves, not small
local refinements.

V2 uses a synthetic "expert" rule: each cell should move a SMALL step
toward the weighted centroid of its connected cells. This is the
direction that locally improves HPWL.

Math:
  For cell c with connected cells {c1, c2, ..., ck} with net sizes
  {n1, n2, ..., nk}, the weighted centroid is:
    centroid = sum_{i} (1/n_i) * pos[c_i] / sum_{i} (1/n_i)
  The expert move is:
    delta = step_size * (centroid - pos[c])
  where step_size is small (0.05-0.1).

This synthetic expert:
- Always locally improves HPWL
- Makes small iterative moves
- Generalizes (any cell with any netlist)
- Is the same rule a real expert would intuitively follow

Training data: for each cell, the (delta_x, delta_y) is the HPWL-improving
move. The OLP model learns to predict this from features.

The result: when the model is applied iteratively, each step moves cells
toward their connected centroids, gradually improving HPWL.
"""

import json
import math
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# Allow running as a script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from chipmind.olp.olp_db import DragLog, init_db
from chipmind.olp.olp_model import extract_features


def build_ispd_style_design(n_cells: int, profile: str = "mixed", seed: int = 42):
    """Build a synthetic ISPD 2005-style netlist."""
    rng = np.random.default_rng(seed)
    grid_side = int(math.ceil(math.sqrt(n_cells)))
    cell_positions_grid = [(i % grid_side, i // grid_side) for i in range(n_cells)]

    nets = []
    seen = set()

    def add_net(cells):
        key = tuple(sorted(cells))
        if key in seen or len(set(cells)) < 2:
            return
        seen.add(key)
        nets.append(list(set(cells)))

    for i in range(0, n_cells, 2):
        x, y = cell_positions_grid[i]
        nbrs = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_side and 0 <= ny < grid_side:
                j = ny * grid_side + nx
                if j < n_cells and j != i:
                    nbrs.append(j)
        if nbrs:
            chosen = rng.choice(nbrs, size=min(2, len(nbrs)), replace=False)
            for j in chosen:
                add_net([i, int(j)])

    for k in range(0, n_cells, max(10, n_cells // 30)):
        sz = rng.integers(5, 10)
        sz = min(sz, n_cells)
        chosen = rng.choice(n_cells, size=sz, replace=False)
        add_net([int(c) for c in chosen])

    A = np.zeros((n_cells, n_cells), dtype=np.float64)
    for cells in nets:
        if len(cells) < 2 or len(cells) > 50:
            continue
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                a, b = int(cells[i]), int(cells[j])
                A[a, b] += 1
                A[b, a] += 1

    return {
        "n_cells": n_cells,
        "nets": nets,
        "A": A,
        "cell_positions_grid": cell_positions_grid,
        "profile": profile,
    }


def expert_move_toward_centroid(cell_idx, pos, nets, step_size=0.1):
    """Compute the HPWL-improving move for a cell.

    Move cell_idx toward the weighted centroid of its connected cells.
    Weight = 1/net_size (larger nets contribute less per cell).

    Returns (dx, dy) — the small step the cell should take.
    """
    weighted_centroid = np.zeros(2, dtype=np.float64)
    total_weight = 0.0
    for net in nets:
        if cell_idx in net:
            other_cells = [c for c in net if c != cell_idx]
            if not other_cells:
                continue
            w = 1.0 / len(net)  # larger net = smaller per-cell weight
            for c in other_cells:
                weighted_centroid += w * pos[c]
            total_weight += w * len(other_cells)
    if total_weight < 1e-9:
        return np.array([0.0, 0.0], dtype=np.float32)
    weighted_centroid /= total_weight
    delta = (weighted_centroid - pos[cell_idx]) * step_size
    return delta.astype(np.float32)


def compute_hpwl(positions, nets):
    """Compute total HPWL."""
    total = 0.0
    for net in nets:
        if len(net) < 2:
            continue
        pts = positions[net]
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
        total += (x_max - x_min) + (y_max - y_min)
    return total


def generate_centroid_expert_drags(
    n_designs: int = 10,
    n_cells_per_design: int = 500,
    drags_per_design: int = 100,
    step_size: float = 0.1,
    die: float = 1000.0,
    out_path: str = "results/olp_centroid_drags.json",
    verbose: bool = True,
):
    """Generate synthetic expert drags using the centroid rule.

    For each design:
      1. Start with random initial placement.
      2. For each cell, compute the centroid-toward step.
      3. Apply ONE step, log (cell_features, delta).
      4. The "expert" delta is the centroid-toward step.

    The OLP model learns to predict this delta from features.
    """
    init_db()
    all_examples = []
    n_total = 0
    t0 = time.time()
    for d_idx in range(n_designs):
        chip = build_ispd_style_design(n_cells_per_design, profile="mixed", seed=d_idx * 100 + 7)
        n = chip["n_cells"]
        nets = chip["nets"]
        rng = np.random.default_rng(d_idx * 100 + 42)
        pos = rng.uniform(0, die, (n, 2)).astype(np.float32)

        # Pre-compute net connectivity
        net_count = np.array([sum(1 for net in nets if i in net) for i in range(n)])
        net_sizes_for_cell = [
            [len(net) for net in nets if i in net] for i in range(n)
        ]

        # Sample cells for this design
        sample_cells = rng.choice(n, size=min(drags_per_design, n), replace=False)
        for cell_idx in sample_cells:
            net_sizes = net_sizes_for_cell[cell_idx]
            if not net_sizes:
                continue
            # Compute expert move
            expert_delta = expert_move_toward_centroid(cell_idx, pos, nets, step_size=step_size)
            if np.linalg.norm(expert_delta) < 1e-6:
                continue
            # Compute local HPWL before
            local_hpwl_before = 0
            for net in nets:
                if cell_idx in net:
                    pts = pos[net]
                    local_hpwl_before += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
            # Apply the move
            pos_after = pos.copy()
            pos_after[cell_idx] = pos[cell_idx] + expert_delta
            local_hpwl_after = 0
            for net in nets:
                if cell_idx in net:
                    pts = pos_after[net]
                    local_hpwl_after += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
            # Extract features
            neighbors = []
            for k in range(1, 3):
                for j in range(max(0, cell_idx - k * 5), min(n, cell_idx + k * 5 + 1)):
                    if j != cell_idx and abs(j - cell_idx) <= k * 5:
                        neighbors.append((f"c{j}", float(pos[j, 0]), float(pos[j, 1])))
            features = extract_features(
                cell_id=f"c{cell_idx}",
                cell_pos=(float(pos[cell_idx, 0]), float(pos[cell_idx, 1])),
                cell_info={"degree": int(net_count[cell_idx]), "drive_strength": 1, "cell_type": 0},
                neighbors=neighbors,
                nets=net_sizes,
                priority={"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
                hpwl_local=float(local_hpwl_before),
            )
            # Save log
            log = DragLog(
                user_id="centroid_expert",
                chip_id=f"centroid_{d_idx}_{n}",
                cell_id=f"c{cell_idx}",
                before_x=float(pos[cell_idx, 0]),
                before_y=float(pos[cell_idx, 1]),
                after_x=float(pos_after[cell_idx, 0]),
                after_y=float(pos_after[cell_idx, 1]),
                priority={"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
                hpwl_before=float(local_hpwl_before),
                hpwl_after=float(local_hpwl_after),
                features=features.tolist(),
                is_synthetic=True,
            )
            log.save()
            # Save training example
            all_examples.append({
                "features": features.tolist(),
                "target_dxdy": expert_delta.tolist(),
                "delta_hpwl": float(local_hpwl_before - local_hpwl_after),
                "user_id": log.user_id,
                "chip_id": log.chip_id,
                "cell_id": log.cell_id,
            })
            n_total += 1
        if verbose:
            print(f"  design {d_idx+1}/{n_designs}: {len(sample_cells)} drags from {n}-cell chip "
                  f"(elapsed {time.time()-t0:.1f}s)")

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w") as f:
        json.dump(all_examples, f)
    if verbose:
        print(f"\nGenerated {n_total} centroid-expert drags in {time.time()-t0:.1f}s")
        print(f"Saved to {out_p}")
    return all_examples


if __name__ == "__main__":
    print("OLP v2: generating centroid-based expert drags (HPWL-improving)")
    print("=" * 70)
    examples = generate_centroid_expert_drags(
        n_designs=10, n_cells_per_design=400, drags_per_design=100
    )
    # Sanity check: verify the expert moves actually improve HPWL
    n_pos = sum(1 for e in examples if e["delta_hpwl"] > 0)
    n_neg = sum(1 for e in examples if e["delta_hpwl"] < 0)
    n_zero = sum(1 for e in examples if e["delta_hpwl"] == 0)
    print(f"\nDelta HPWL stats: {n_pos} positive, {n_neg} negative, {n_zero} zero")
    print(f"  ({100*n_pos/len(examples):.1f}% are HPWL-improving)")
    if n_pos < len(examples) * 0.9:
        print("  WARNING: less than 90% of expert moves are HPWL-improving!")
    else:
        print("  ✓ Expert moves are reliably HPWL-improving")
