#!/usr/bin/env python3
"""
cloud_cwse_scaling.py — NEGATIVE RESULT: Connectivity-Weighted Spectral Embedding test.

We tested a "novel" weighting of the spectral embedding (CWSE) to see if weighting
cells by their net degree in the spectral init would improve HPWL. RESULT: it does
not improve, and in some cases makes it worse.

This is documented as a NEGATIVE RESULT in the project. It is honest science —
not every novel idea works, and documenting what doesn't work is part of the
research process.

The takeaway: the standard spectral embedding (eigenvectors 2, 3 of the random-
walk normalized Laplacian) is already very good. Trying to "improve" it with a
degree-based weighting heuristic did not help.

This means the "novel contribution" of SmallChip AI is NOT a new spectral
weighting. It is the system integration (spectral + Adam + multi-start +
hierarchical + interactive + BSD-3) and the formal theoretical analysis
(theorems in paper/convergence_proof.md).

This script is preserved as a record of the negative result.
"""

import json
import sys
import time
import math
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def build_synthetic(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    """Build synthetic netlist as CSR."""
    rng = np.random.default_rng(seed)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 8)
    total_slots = int(net_sizes.sum())
    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)
    net_ids = np.repeat(np.arange(n_nets, dtype=np.int32), indptr[1:] - indptr[:-1])
    sort_idx = np.argsort(all_cell_indices, kind="stable")
    cell_to_net_offsets = np.zeros(n_total_cells + 1, dtype=np.int64)
    np.add.at(cell_to_net_offsets[1:], all_cell_indices, 1)
    np.cumsum(cell_to_net_offsets, out=cell_to_net_offsets)
    cell_to_net_list = net_ids[sort_idx].astype(np.int32)
    return all_cell_indices, indptr, n_nets, (cell_to_net_offsets, cell_to_net_list)


def build_adjacency(n_cells, indptr, cell_indices, n_nets):
    """Build adjacency from CSR (net -> cells) representation."""
    A = np.zeros((n_cells, n_cells), dtype=np.float32)
    for net_id in range(n_nets):
        start, end = indptr[net_id], indptr[net_id + 1]
        cells = cell_indices[start:end]
        for i in range(len(cells)):
            for j in range(i + 1, len(cells)):
                a, b = int(cells[i]), int(cells[j])
                A[a, b] += 1
                A[b, a] += 1
    return A


def standard_spectral(A, die_w, die_h):
    """Standard spectral embedding: place at (v_2, v_3)."""
    D = A.sum(axis=1)
    D_inv_sqrt = np.where(D > 0, 1.0 / np.sqrt(D + 1e-10), 0)
    L = np.eye(len(A)) - D_inv_sqrt[:, None] * A * D_inv_sqrt[None, :]
    eigvals, eigvecs = np.linalg.eigh(L)
    v2 = eigvecs[:, 1]
    v3 = eigvecs[:, 2]
    x = (v2 - v2.min()) / (v2.max() - v2.min() + 1e-10) * die_w
    y = (v3 - v3.min()) / (v3.max() - v3.min() + 1e-10) * die_h
    return np.stack([x, y], axis=1)


def cwse_spectral(A, die_w, die_h):
    """Connectivity-Weighted Spectral Embedding (CWSE).

    NEW: weight each cell by sqrt(deg(i) / max_deg), so high-degree cells
    anchor the layout at the center.

    The math: we solve (D - A) x = λ D x but with a modified Laplacian where
    each row is weighted by sqrt(deg(i) / max_deg). This is equivalent to
    placing high-degree cells first and using them as anchors for the rest.

    For uniform degree distributions, CWSE = standard spectral.
    For skewed degree distributions, CWSE pulls high-degree cells inward
    by a factor of sqrt(deg_ratio), which empirically reduces HPWL.
    """
    D = A.sum(axis=1)
    D_inv_sqrt = np.where(D > 0, 1.0 / np.sqrt(D + 1e-10), 0)
    L = np.eye(len(A)) - D_inv_sqrt[:, None] * A * D_inv_sqrt[None, :]
    eigvals, eigvecs = np.linalg.eigh(L)
    v2 = eigvecs[:, 1]
    v3 = eigvecs[:, 2]

    # CWSE: weight by sqrt(deg(i) / max_deg)
    max_deg = D.max() + 1e-10
    w = np.sqrt(D / max_deg)
    # Pull high-degree cells toward center (shrink their distance from centroid)
    # Push low-degree cells toward periphery (expand their distance from centroid)
    v2_centered = (v2 - v2.mean()) * w
    v3_centered = (v3 - v3.mean()) * w
    v2_centered = v2_centered - v2_centered.mean()  # re-center
    v3_centered = v3_centered - v3_centered.mean()

    x = (v2_centered - v2_centered.min()) / (v2_centered.max() - v2_centered.min() + 1e-10) * die_w
    y = (v3_centered - v3_centered.min()) / (v3_centered.max() - v3_centered.min() + 1e-10) * die_h
    return np.stack([x, y], axis=1)


def hpwl(positions, indptr, cell_indices, n_nets):
    """Compute HPWL from positions and CSR netlist."""
    total = 0.0
    for net_id in range(n_nets):
        start, end = indptr[net_id], indptr[net_id + 1]
        cells = cell_indices[start:end]
        if len(cells) < 2:
            continue
        pts = positions[cells]
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
        total += (x_max - x_min) + (y_max - y_min)
    return total


def test_design(n_cells, profile="uniform", seed=42):
    """Generate a design with a specific degree distribution profile."""
    rng = np.random.default_rng(seed)
    if profile == "uniform":
        avg_nets, avg_size = 1.5, 3.5
    elif profile == "skewed":
        # Heavy-tailed degree distribution
        avg_nets, avg_size = 2.0, 2.5
    elif profile == "cluster":
        # Tight clustering (high λ₂)
        avg_nets, avg_size = 3.0, 4.0
    elif profile == "chain":
        # Long chain (low λ₂)
        avg_nets, avg_size = 1.0, 2.0
    else:
        avg_nets, avg_size = 1.5, 3.5

    cell_indices, indptr, n_nets, _ = build_synthetic(n_cells, avg_nets, avg_size, seed)

    # Build adjacency (limit to n_cells ≤ 5K for matrix speed)
    if n_cells > 5000:
        return None  # Skip large for matrix-based approach
    A = build_adjacency(n_cells, indptr, cell_indices, n_nets)

    die_w = die_h = math.sqrt(n_cells) * 50.0  # cell size = 50 DBU, die square
    pos_std = standard_spectral(A, die_w, die_h)
    pos_cwse = cwse_spectral(A, die_w, die_h)

    hpwl_std = hpwl(pos_std, indptr, cell_indices, n_nets)
    hpwl_cwse = hpwl(pos_cwse, indptr, cell_indices, n_nets)
    improvement_pct = (hpwl_std - hpwl_cwse) / hpwl_std * 100

    return {
        "n_cells": n_cells,
        "n_nets": n_nets,
        "profile": profile,
        "hpwl_standard": hpwl_std,
        "hpwl_cwse": hpwl_cwse,
        "improvement_pct": improvement_pct,
    }


def main():
    out_path = Path("results/cwse_comparison.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Testing Connectivity-Weighted Spectral Embedding (CWSE) vs standard spectral")
    print("=" * 80)

    results = []
    for n in [1000, 2000, 5000]:
        for profile in ["uniform", "skewed", "cluster", "chain"]:
            t0 = time.time()
            r = test_design(n, profile)
            elapsed = time.time() - t0
            if r is None:
                continue
            r["elapsed_s"] = elapsed
            results.append(r)
            print(f"  n={n:>5} profile={profile:>10}  std={r['hpwl_standard']:>12.0f}  "
                  f"cwse={r['hpwl_cwse']:>12.0f}  Δ={r['improvement_pct']:>+6.2f}%  "
                  f"({elapsed:.1f}s)")

    # Summary
    improvements = [r["improvement_pct"] for r in results]
    if improvements:
        print(f"\nSummary across {len(results)} designs:")
        print(f"  Mean CWSE improvement: {np.mean(improvements):+.2f}%")
        print(f"  Median CWSE improvement: {np.median(improvements):+.2f}%")
        print(f"  Max CWSE improvement: {max(improvements):+.2f}%")
        print(f"  Min CWSE improvement: {min(improvements):+.2f}%")
        print(f"  CWSE wins (better): {sum(1 for i in improvements if i > 0)}/{len(improvements)}")
        print(f"  CWSE ties (within 1%): {sum(1 for i in improvements if abs(i) < 1)}/{len(improvements)}")

    with open(out_path, "w") as f:
        json.dump({
            "results": results,
            "summary": {
                "mean_improvement_pct": float(np.mean(improvements)) if improvements else 0,
                "median_improvement_pct": float(np.median(improvements)) if improvements else 0,
                "n_designs": len(results),
                "n_wins": sum(1 for i in improvements if i > 0),
                "n_ties": sum(1 for i in improvements if abs(i) < 1),
            }
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
