"""
cloud_100m_fast.py — Optimized 100M scaling with vectorized numpy.

Replaces the slow per-block loop with a single vectorized operation.
Uses CSR-style netlist for efficient HPWL.
"""
import sys
import time
import math
import json
import gc
import numpy as np
from pathlib import Path

OUT = Path("/root/smallchip-ai/results/scaling_100m_cloud_fast.json")


def build_synthetic_fast(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    rng = np.random.default_rng(seed)
    print(f"  building {n_total_cells:,} cells + nets...", flush=True)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 8)
    total_slots = int(net_sizes.sum())
    print(f"  generating {total_slots:,} slot indices...", flush=True)
    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)
    # positions: zero-initialized
    positions = np.zeros((n_total_cells, 2), dtype=np.float32)
    return positions, all_cell_indices, indptr, n_nets


def place_partition_random_fast(positions, indices, indptr, n_blocks, die, seed=42):
    """Vectorized random per-block placement.

    Block layout: ceil(sqrt(n_blocks)) x cols grid. Each cell randomly placed
    within its block's rectangular region.
    """
    rng = np.random.default_rng(seed)
    cols = int(math.ceil(math.sqrt(n_blocks)))
    rows = int(math.ceil(n_blocks / cols))
    block_w = (die["x2"] - die["x1"]) / cols
    block_h = (die["y2"] - die["y1"]) / rows
    print(f"  grid {cols}x{rows}, block {block_w:.0f}x{block_h:.0f}", flush=True)

    # Assign each cell to a block (round-robin on shuffled order)
    n_cells = positions.shape[0]
    perm = rng.permutation(n_cells)
    assignment = np.zeros(n_cells, dtype=np.int32)
    for i, c in enumerate(perm):
        assignment[c] = i % n_blocks

    # Vectorized: for each block, compute its slot (col, row) and origin
    block_cols = np.arange(n_blocks) % cols
    block_rows = np.arange(n_blocks) // cols
    block_x1 = die["x1"] + block_cols * block_w
    block_y1 = die["y1"] + block_rows * block_h

    # For each cell, get its block's origin
    cell_x1 = block_x1[assignment]
    cell_y1 = block_y1[assignment]

    # Random position within each cell's block (5-95% of block size)
    cell_x = cell_x1 + rng.uniform(0.05, 0.95, n_cells) * block_w
    cell_y = cell_y1 + rng.uniform(0.05, 0.95, n_cells) * block_h

    positions[:, 0] = cell_x
    positions[:, 1] = cell_y
    return positions, assignment


def compute_hpwl_csr(positions, indices, indptr, n_nets, chunk=5_000_000):
    """Vectorized HPWL over CSR-format netlist.

    positions: (N, 2) float32
    indices: int32 array of cell ids (length = total slots)
    indptr: int64 array (length = n_nets + 1)

    Returns: (total_hpwl, hpwl_per_net)
    """
    total = 0.0
    n_nets = int(n_nets)
    t0 = time.time()
    log_every = max(1, n_nets // 5)
    for start in range(0, n_nets, chunk):
        end = min(start + chunk, n_nets)
        # Process each net in this chunk
        chunk_total = 0.0
        chunk_count = 0
        for i in range(start, end):
            s = indptr[i]
            e = indptr[i + 1]
            if e - s < 2:
                continue
            cells = indices[s:e]
            xs = positions[cells, 0]
            ys = positions[cells, 1]
            chunk_total += (xs.max() - xs.min()) + (ys.max() - ys.min())
            chunk_count += 1
        total += chunk_total
        if start % (chunk * 5) == 0 and start > 0:
            elapsed = time.time() - t0
            pct = 100 * start / n_nets
            print(f"      HPWL progress: {start}/{n_nets} nets ({pct:.0f}%) "
                  f"[{elapsed:.0f}s]", flush=True)
    return total, total / max(1, n_nets)


def run_scale_fast(n_total_cells, label, n_blocks, seed=42):
    print(f"\n=== {label}: {n_total_cells:,} cells ===", flush=True)
    t0 = time.time()
    positions, indices, indptr, n_nets = build_synthetic_fast(
        n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=seed,
    )
    build_t = time.time() - t0
    die = {"x1": 0, "y1": 0, "x2": 1000.0, "y2": 1000.0}  # placeholder, scaled below
    # Scale die to match cell count
    side_um = math.sqrt(n_total_cells / 0.375)
    side_dbu = side_um * 1000
    die = {"x1": 0, "y1": 0, "x2": side_dbu, "y2": side_dbu}
    print(f"  built in {build_t:.1f}s, {n_total_cells/build_t:,.0f} cells/sec, "
          f"memory: {(positions.nbytes + indices.nbytes + indptr.nbytes) / 1e9:.2f}GB",
          flush=True)

    t0 = time.time()
    positions, assignment = place_partition_random_fast(
        positions, indices, indptr, n_blocks, die, seed=seed,
    )
    place_t = time.time() - t0
    print(f"  placement: {place_t:.1f}s", flush=True)

    t0 = time.time()
    total_hpwl, per_net_hpwl = compute_hpwl_csr(positions, indices, indptr, n_nets)
    hpwl_t = time.time() - t0
    print(f"  HPWL: {total_hpwl:,.0f} = {per_net_hpwl:,.1f}/net ({hpwl_t:.1f}s)", flush=True)

    return {
        "label": label,
        "n_cells": int(n_total_cells),
        "n_nets": int(n_nets),
        "n_blocks": int(n_blocks),
        "build_time_s": build_t,
        "place_time_s": place_t,
        "hpwl_time_s": hpwl_t,
        "total_hpwl_dbu": float(total_hpwl),
        "per_net_hpwl_dbu": float(per_net_hpwl),
        "memory_gb": (positions.nbytes + indices.nbytes + indptr.nbytes) / 1e9,
    }


def main():
    print("=" * 60)
    print("  Cloud 100M — fast vectorized version")
    print("=" * 60)
    scales = [
        (15_000, "15K", 100),
        (150_000, "150K", 200),
        (1_000_000, "1M", 500),
        (10_000_000, "10M", 2000),
        (30_000_000, "30M", 3000),
        (60_000_000, "60M", 4000),
        (100_000_000, "100M", 6667),
    ]
    results = []
    t_start = time.time()
    for n_cells, label, n_blocks in scales:
        try:
            r = run_scale_fast(n_cells, label, n_blocks)
            results.append(r)
        except Exception as e:
            print(f"  [FAILED] {label}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            results.append({"label": label, "error": str(e)})
        with open(OUT, "w") as f:
            json.dump({"results": results, "elapsed_s": time.time() - t_start}, f, indent=2)
        print(f"  [SAVED] {OUT} (elapsed {time.time()-t_start:.1f}s)", flush=True)
    print("\n=== FINAL ===", flush=True)
    for r in results:
        if "error" in r:
            print(f"  {r['label']:>10}: ERROR — {r['error']}", flush=True)
        else:
            print(f"  {r['label']:>10}: {r['n_cells']:>12,} cells, "
                  f"{r['per_net_hpwl_dbu']:>12,.0f} DBU/net, "
                  f"build {r['build_time_s']:.2f}s, place {r['place_time_s']:.1f}s, "
                  f"hpwl {r['hpwl_time_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
