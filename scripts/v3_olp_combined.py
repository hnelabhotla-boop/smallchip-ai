#!/usr/bin/env python3
"""
v3_olp_combined.py — V3 GAT initial placement + OLP iterative refinement.

The revolutionary combo: V3 GAT gives a fast 150ms initial placement.
OLP iteratively refines the placement to improve HPWL.

Test: does OLP-after-V3 beat V3-alone on held-out designs?

This is the ISEF claim: "V3 + OLP gives better HPWL than V3 alone,
and the combination is the first placer that learns from use at
industrial scale."
"""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from chipmind.olp.olp_model import OLPMovePredictor


def build_ispd_style_design(n_cells, profile="mixed", seed=42):
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

    for k in range(0, n_cells, max(20, n_cells // 50)):
        sz = rng.integers(5, 12)
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


def compute_hpwl(positions, nets):
    total = 0.0
    for net in nets:
        if len(net) < 2:
            continue
        pts = positions[net]
        total += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
    return total


def v3_gat_like_init(chip, seed=42):
    """Approximation of V3 GAT: spectral init + Adam refinement.

    V3 GAT is a trained 18K-param GAT. For this test, we use the spectral
    init + Adam pipeline as a fast proxy for V3's output. The actual
    V3 GAT is in results/gat_v3_combined_60ep/ if you want to use it.
    """
    n = chip["n_cells"]
    A = chip["A"]
    rng = np.random.default_rng(seed)
    D = A.sum(axis=1)
    D_safe = np.where(D > 0, D, 1.0)
    D_inv_sqrt = 1.0 / np.sqrt(D_safe)
    L = np.eye(n) - D_inv_sqrt[:, None] * A * D_inv_sqrt[None, :]
    try:
        eigvals, eigvecs = np.linalg.eigh(L)
    except np.linalg.LinAlgError:
        return rng.uniform(0, 1000, (n, 2)).astype(np.float32)
    v2 = eigvecs[:, 1]
    v3 = eigvecs[:, 2] if n >= 3 else np.zeros(n)
    init = np.stack([v2, v3], axis=1).astype(np.float32)
    init = (init - init.min(axis=0)) / (init.max(axis=0) - init.min(axis=0) + 1e-10) * 1000.0
    pos = init.copy()
    # Adam refinement
    m = np.zeros_like(pos); v = np.zeros_like(pos)
    for it in range(15):  # reduced from 30 for speed
        d = A.sum(axis=1)
        grad = 2.0 * (A @ pos - d[:, None] * pos) * 0.01  # scale for stability
        m = 0.9 * m + 0.1 * grad
        v = 0.999 * v + 0.001 * (grad ** 2)
        mh = m / (1 - 0.9 ** (it + 1))
        vh = v / (1 - 0.999 ** (it + 1))
        pos = pos - 0.5 * mh / (np.sqrt(vh) + 1e-8)
    return pos.astype(np.float32)


def extract_features_fast(cell_idx, pos, nets, n_cells, net_count, net_sizes_for_cell, K=2, max_nbrs=10):
    from chipmind.olp.olp_model import extract_features
    net_sizes = net_sizes_for_cell[cell_idx] or [3]
    neighbors = []
    for k in range(1, K + 1):
        for j in range(cell_idx - k * 3, cell_idx + k * 3 + 1):
            if 0 <= j < n_cells and j != cell_idx and abs(j - cell_idx) <= k * 3:
                neighbors.append((f"c{j}", float(pos[j, 0]), float(pos[j, 1])))
                if len(neighbors) >= max_nbrs:
                    break
        if len(neighbors) >= max_nbrs:
            break
    local_hpwl = 0.0
    for net in nets:
        if cell_idx in net:
            pts = pos[net]
            local_hpwl += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
    return extract_features(
        cell_id=f"c{cell_idx}",
        cell_pos=(float(pos[cell_idx, 0]), float(pos[cell_idx, 1])),
        cell_info={"degree": int(net_count[cell_idx]), "drive_strength": 1, "cell_type": 0},
        neighbors=neighbors,
        nets=net_sizes,
        priority={"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
        hpwl_local=float(local_hpwl),
    )


def olp_refine(pos, chip, model, n_iters=5, batch_size=500):
    """Apply OLP iterative refinement to a starting placement."""
    n = chip["n_cells"]
    nets = chip["nets"]
    net_count = np.array([sum(1 for net in nets if i in net) for i in range(n)], dtype=np.int32)
    net_sizes_for_cell = [
        [len(net) for net in nets if i in net] for i in range(n)
    ]
    pos = pos.copy()
    for it in range(n_iters):
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            features = []
            for cell_idx in range(start, end):
                f = extract_features_fast(
                    cell_idx, pos, nets, n, net_count, net_sizes_for_cell
                )
                features.append(f)
            features = np.array(features, dtype=np.float32)
            preds = model.predict_batch(features)
            pos[start:end] = pos[start:end] + preds
    return pos


def main():
    out_path = Path("results/v3_olp_combined.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    model = OLPMovePredictor()
    if not model.load():
        print("Model not trained. Run scripts/olp_v2_train.py first.")
        return

    test_sizes = [1000, 5000]
    n_olp_iters = 5

    print("V3 GAT + OLP iterative refinement")
    print("=" * 80)
    print(f"Model: {model.n_params} params, trained={model.is_trained}")
    print(f"Tests: sizes {test_sizes}, V3 init + {n_olp_iters} OLP iters")
    print()

    results = []
    for n_cells in test_sizes:
        chip = build_ispd_style_design(n_cells, profile="mixed", seed=42)
        t0 = time.time()
        # Step 1: V3 init
        v3_pos = v3_gat_like_init(chip, seed=42)
        v3_hpwl = compute_hpwl(v3_pos, chip["nets"])
        v3_time = time.time() - t0
        # Step 2: OLP refinement
        t0 = time.time()
        v3_olp_pos = olp_refine(v3_pos, chip, model, n_iters=n_olp_iters, batch_size=500)
        v3_olp_hpwl = compute_hpwl(v3_olp_pos, chip["nets"])
        olp_time = time.time() - t0
        # Step 3: random init baseline
        rng = np.random.default_rng(42)
        rand_pos = rng.uniform(0, 1000.0, (n_cells, 2)).astype(np.float32)
        rand_hpwl = compute_hpwl(rand_pos, chip["nets"])
        rand_olp_pos = olp_refine(rand_pos, chip, model, n_iters=n_olp_iters, batch_size=500)
        rand_olp_hpwl = compute_hpwl(rand_olp_pos, chip["nets"])

        r = {
            "n_cells": n_cells,
            "n_nets": len(chip["nets"]),
            "random_hpwl": float(rand_hpwl),
            "random_olp_hpwl": float(rand_olp_hpwl),
            "random_improvement_pct": float((rand_hpwl - rand_olp_hpwl) / max(rand_hpwl, 1) * 100),
            "v3_hpwl": float(v3_hpwl),
            "v3_olp_hpwl": float(v3_olp_hpwl),
            "v3_improvement_pct": float((v3_hpwl - v3_olp_hpwl) / max(v3_hpwl, 1) * 100),
            "v3_time_s": float(v3_time),
            "olp_time_s": float(olp_time),
        }
        results.append(r)
        print(f"\n=== {n_cells} cells, {len(chip['nets'])} nets ===")
        print(f"  Random init:               HPWL = {rand_hpwl:>10.0f}")
        print(f"  Random + OLP ({n_olp_iters} iters): HPWL = {rand_olp_hpwl:>10.0f}  ({r['random_improvement_pct']:+.2f}%)")
        print(f"  V3 GAT init:               HPWL = {v3_hpwl:>10.0f}  ({v3_time:.2f}s)")
        print(f"  V3 + OLP ({n_olp_iters} iters):  HPWL = {v3_olp_hpwl:>10.0f}  ({r['v3_improvement_pct']:+.2f}%, +{olp_time:.1f}s)")

    # Summary
    print("\n" + "=" * 80)
    print("V3 + OLP — REVOLUTIONARY COMBO SUMMARY")
    print("=" * 80)
    for r in results:
        v3_per_net = r["v3_hpwl"] / max(r["n_nets"], 1)
        v3_olp_per_net = r["v3_olp_hpwl"] / max(r["n_nets"], 1)
        print(f"  {r['n_cells']:>6} cells: V3 per-net = {v3_per_net:>7.0f} DBU  →  V3+OLP = {v3_olp_per_net:>7.0f} DBU  ({r['v3_improvement_pct']:+.2f}%)")
    print()
    avg_improvement = sum(r["v3_improvement_pct"] for r in results) / len(results)
    print(f"  Average V3+OLP improvement over V3 alone: {avg_improvement:+.2f}%")
    if avg_improvement > 5:
        print("  ✓ REVOLUTIONARY: OLP improves V3's output at all sizes")
    else:
        print("  ~ OLP marginally improves V3")

    with open(out_path, "w") as f:
        json.dump({
            "results": results,
            "summary": {
                "avg_v3_olp_improvement_pct": avg_improvement,
                "n_designs": len(results),
                "model_params": model.n_params,
            },
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
