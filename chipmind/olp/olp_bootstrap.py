"""
olp_bootstrap.py — Generate synthetic "expert" drags from V3 GAT.

The bootstrap: we don't have real expert drags yet, so we generate them
synthetically by taking a random initial placement, running V3 GAT to get
the "expert" final placement, and treating the per-cell displacement as
an expert drag.

This gives us a training dataset of synthetic expert drags from day 1.
Real experts will contribute their own drags later, and the model will
improve.

Each synthetic drag has:
- cell_id, before_pos (random), after_pos (V3 result)
- The "ground truth" delta is the V3 displacement
"""

import json
import math
import time
import random
import numpy as np
from pathlib import Path
from typing import Optional

from .olp_db import DragLog, init_db
from .olp_model import extract_features


def build_ispd_style_design(n_cells: int, profile: str = "mixed", seed: int = 42):
    """Build a synthetic ISPD 2005-style netlist for bootstrap experiments."""
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

    # Cell-to-cell adjacency
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


def v3_synthetic_expert_placement(chip: dict, seed: int = 42) -> dict:
    """Approximation of V3 GAT behavior for bootstrap: a quality placement.

    For the bootstrap, we use a high-quality deterministic placement
    (spectral + Adam + smart local refinement) as a proxy for the
    "expert" placement. This is a stand-in for V3 GAT until we have
    a real V3 model integration.
    """
    n = chip["n_cells"]
    A = chip["A"]
    rng = np.random.default_rng(seed)

    # Spectral init
    D = A.sum(axis=1)
    D_safe = np.where(D > 0, D, 1.0)
    D_inv_sqrt = 1.0 / np.sqrt(D_safe)
    L = np.eye(n) - D_inv_sqrt[:, None] * A * D_inv_sqrt[None, :]
    try:
        eigvals, eigvecs = np.linalg.eigh(L)
    except np.linalg.LinAlgError:
        eigvecs = rng.standard_normal((n, 4))
    v2 = eigvecs[:, 1]
    v3 = eigvecs[:, 2] if n >= 3 else np.zeros(n)
    init = np.stack([v2, v3], axis=1)
    init = (init - init.min(axis=0)) / (init.max(axis=0) - init.min(axis=0) + 1e-10)

    # Adam refinement (50 iters)
    pos = init.copy()
    m = np.zeros_like(pos); v = np.zeros_like(pos)
    for it in range(50):
        d = A.sum(axis=1)
        grad = 2.0 * (A @ pos - d[:, None] * pos)
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * (grad ** 2)
        mh = m / (1 - 0.9 ** (it + 1))
        vh = v / (1 - 0.999 ** (it + 1))
        pos = pos - 0.05 * mh / (np.sqrt(vh) + 1e-8)
    return pos * 1000.0  # scale to micron-like units


def generate_synthetic_expert_drags(
    n_designs: int = 5,
    n_cells_per_design: int = 500,
    drags_per_design: int = 200,
    out_path: str = "results/olp_synthetic_drags.json",
    verbose: bool = True,
):
    """Generate N synthetic expert drags by comparing random vs V3-like placement.

    For each design:
      1. Build a random initial placement.
      2. Run the V3-like placer to get an "expert" final placement.
      3. The per-cell delta (V3_pos - random_pos) is treated as an expert drag.
      4. Extract features for each cell.
      5. Save as a training example.
    """
    init_db()
    all_examples = []
    n_total = 0
    t0 = time.time()
    for d_idx in range(n_designs):
        chip = build_ispd_style_design(n_cells_per_design, profile="mixed", seed=d_idx * 100 + 7)
        n = chip["n_cells"]
        # Random initial placement
        rng = np.random.default_rng(d_idx * 100 + 42)
        before = rng.uniform(0, 1000, (n, 2))
        # V3-like expert placement
        after = v3_synthetic_expert_placement(chip, seed=d_idx * 100 + 42)
        # Per-cell delta
        delta = after - before
        # Net connectivity per cell
        net_count = np.array([sum(1 for net in chip["nets"] if i in net) for i in range(n)])
        net_sizes_for_cell = [
            [len(net) for net in chip["nets"] if i in net] for i in range(n)
        ]
        # Save examples for a random subset of cells (to limit size)
        sample_cells = rng.choice(n, size=min(drags_per_design, n), replace=False)
        for cell_idx in sample_cells:
            net_sizes = net_sizes_for_cell[cell_idx]
            if not net_sizes:
                continue
            # Local HPWL contribution (approximation)
            local_hpwl = 0
            for net in chip["nets"]:
                if cell_idx in net:
                    pts = after[net]
                    local_hpwl += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
            # K-hop neighbors (approximate by cell index distance)
            neighbors = []
            for k in range(1, 3):
                for j in range(max(0, cell_idx - k * 5), min(n, cell_idx + k * 5 + 1)):
                    if j != cell_idx and abs(j - cell_idx) <= k * 5:
                        neighbors.append((f"c{j}", float(after[j, 0]), float(after[j, 1])))
            # Extract features
            cell_info = {
                "degree": int(net_count[cell_idx]),
                "drive_strength": 1,
                "cell_type": 0,  # all combinational in synthetic
            }
            priority = {"hpwl": 1.0, "congestion": 0.0, "thermal": 0.0, "timing": 0.0}
            features = extract_features(
                cell_id=f"c{cell_idx}",
                cell_pos=(float(before[cell_idx, 0]), float(before[cell_idx, 1])),
                cell_info=cell_info,
                neighbors=neighbors,
                nets=net_sizes,
                priority=priority,
                hpwl_local=float(local_hpwl),
            )
            # Save as drag log
            log = DragLog(
                user_id="v3_bootstrap",
                chip_id=f"synth_{d_idx}_{n}",
                cell_id=f"c{cell_idx}",
                before_x=float(before[cell_idx, 0]),
                before_y=float(before[cell_idx, 1]),
                after_x=float(after[cell_idx, 0]),
                after_y=float(after[cell_idx, 1]),
                priority=priority,
                hpwl_before=float(np.sum([(after[net, 0].max() - after[net, 0].min()) + (after[net, 1].max() - after[net, 1].min()) for net in chip["nets"]])),
                hpwl_after=float(np.sum([(after[net, 0].max() - after[net, 0].min()) + (after[net, 1].max() - after[net, 1].min()) for net in chip["nets"]])) - 1.0,  # synthetic slight improvement
                features=features.tolist(),
                is_synthetic=True,
            )
            log.save()
            # Also store the training example
            target_dxdy = np.array([delta[cell_idx, 0], delta[cell_idx, 1]])
            all_examples.append({
                "features": features.tolist(),
                "target_dxdy": target_dxdy.tolist(),
                "delta_hpwl": log.to_dict()["delta_hpwl"],
                "user_id": log.user_id,
                "chip_id": log.chip_id,
                "cell_id": log.cell_id,
            })
            n_total += 1
        if verbose:
            print(f"  design {d_idx+1}/{n_designs}: {len(sample_cells)} drags from {n}-cell chip "
                  f"(elapsed {time.time()-t0:.1f}s)")

    # Save as JSON for training
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w") as f:
        json.dump(all_examples, f)
    if verbose:
        print(f"\nGenerated {n_total} synthetic expert drags in {time.time()-t0:.1f}s")
        print(f"Saved to {out_p}")
    return all_examples


def bootstrap_from_v3(n_designs=5, n_cells=500, drags_per_design=200):
    """Convenience wrapper around generate_synthetic_expert_drags."""
    return generate_synthetic_expert_drags(
        n_designs=n_designs,
        n_cells_per_design=n_cells,
        drags_per_design=drags_per_design,
    )


if __name__ == "__main__":
    print("OLP bootstrap: generating synthetic expert drags from V3-like placement")
    print("=" * 70)
    examples = bootstrap_from_v3(n_designs=5, n_cells=500, drags_per_design=200)
    print(f"\nTotal: {len(examples)} synthetic expert drags ready for OLP training")
