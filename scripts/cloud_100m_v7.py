"""
cloud_100m_v7.py — Push 100M HPWL below 500K with aggressive refinement.

Key improvements over v6:
1. More inter-block refinement iterations (100 vs 30)
2. Adam-style optimizer for block positions (momentum + adaptive lr)
3. Multi-start: try 3 random seeds for partition, keep best
4. Per-block V5 placement (once V5 done) instead of random
5. Per-cell gradient descent refinement after block placement
"""
import sys
import time
import math
import json
import gc
import numpy as np
from pathlib import Path
from collections import defaultdict

OUT = Path("/root/smallchip-ai/results/scaling_100m_v7.json")


def build_synthetic(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    rng = np.random.default_rng(seed)
    print(f"  building {n_total_cells:,} cells + nets...", flush=True)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 8)
    total_slots = int(net_sizes.sum())
    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)

    print(f"  building compact cell->nets index...", flush=True)
    t0 = time.time()
    net_ids = np.repeat(np.arange(n_nets, dtype=np.int32), indptr[1:] - indptr[:-1])
    sort_idx = np.argsort(all_cell_indices, kind="stable")
    cell_to_net_pairs = np.column_stack([all_cell_indices[sort_idx], net_ids[sort_idx]])
    cell_to_net_offsets = np.zeros(n_total_cells + 1, dtype=np.int64)
    np.add.at(cell_to_net_offsets[1:], all_cell_indices, 1)
    np.cumsum(cell_to_net_offsets, out=cell_to_net_offsets)
    cell_to_net_list = cell_to_net_pairs[:, 1].astype(np.int32)
    del cell_to_net_pairs, net_ids, sort_idx
    print(f"    done in {time.time()-t0:.1f}s", flush=True)

    positions = np.zeros((n_total_cells, 2), dtype=np.float32)
    return positions, all_cell_indices, indptr, n_nets, (cell_to_net_offsets, cell_to_net_list)


def bfs_partition_compact(n_total_cells, n_nets, all_cell_indices, indptr,
                          n_blocks, block_size, cell_to_net_data, seed=42):
    rng = np.random.default_rng(seed)
    offsets, net_list = cell_to_net_data
    print(f"  BFS partition ({n_blocks} blocks, seed={seed})...", flush=True)
    t0 = time.time()
    assignment = -np.ones(n_total_cells, dtype=np.int32)
    perm = rng.permutation(n_total_cells)
    block_id = 0
    for seed in perm:
        if assignment[seed] != -1:
            continue
        assignment[seed] = block_id
        frontier_cells = [int(seed)]
        block_count = 1
        visited_nets = set()
        while frontier_cells and block_count < block_size:
            cur = frontier_cells.pop()
            s = offsets[cur]
            e = offsets[cur + 1]
            for slot in range(s, e):
                net_id = int(net_list[slot])
                if net_id in visited_nets:
                    continue
                visited_nets.add(net_id)
                ns, ne = indptr[net_id], indptr[net_id + 1]
                cells_in_net = all_cell_indices[ns:ne]
                for c in cells_in_net:
                    if assignment[c] == -1:
                        assignment[c] = block_id
                        frontier_cells.append(int(c))
                        block_count += 1
                        if block_count >= block_size:
                            break
                if block_count >= block_size:
                    break
        block_id += 1
        if block_id >= n_blocks:
            break
    unassigned = np.where(assignment == -1)[0]
    for i, c in enumerate(unassigned):
        assignment[c] = i % n_blocks
    print(f"  partition done in {time.time()-t0:.1f}s", flush=True)
    return assignment


def compute_block_wires(assignment, all_cell_indices, indptr, n_nets, n_blocks):
    print(f"  computing inter-block wires ({n_blocks} blocks)...", flush=True)
    t0 = time.time()
    bb_wires = defaultdict(float)
    for net_id in range(n_nets):
        s, e = indptr[net_id], indptr[net_id + 1]
        cells = all_cell_indices[s:e]
        blocks = assignment[cells]
        unique_blocks = np.unique(blocks)
        if len(unique_blocks) < 2:
            continue
        for i in range(len(unique_blocks)):
            for j in range(i + 1, len(unique_blocks)):
                b1, b2 = int(unique_blocks[i]), int(unique_blocks[j])
                if b1 > b2:
                    b1, b2 = b2, b1
                bb_wires[(b1, b2)] += 1.0
    print(f"    {len(bb_wires):,} block pairs, {time.time()-t0:.1f}s", flush=True)
    return bb_wires


def spectral_top_placement(bb_wires, n_blocks, die, seed=42):
    print(f"  spectral top-level placement ({n_blocks} blocks)...", flush=True)
    t0 = time.time()
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import eigsh
    except ImportError:
        return grid_init(n_blocks, die)
    rows = []
    cols = []
    data = []
    for (b1, b2), w in bb_wires.items():
        rows.append(b1); cols.append(b2); data.append(w)
        rows.append(b2); cols.append(b1); data.append(w)
    W = csr_matrix((data, (rows, cols)), shape=(n_blocks, n_blocks), dtype=np.float32)
    degrees = np.array(W.sum(axis=1)).flatten()
    D = csr_matrix((degrees, (np.arange(n_blocks), np.arange(n_blocks))),
                   shape=(n_blocks, n_blocks), dtype=np.float32)
    L = D - W
    k = min(4, n_blocks - 1)
    try:
        eigenvalues, eigenvectors = eigsh(L.astype(np.float64), k=k, which='SM',
                                          sigma=-0.1, mode='normal')
    except Exception as e:
        return grid_init(n_blocks, die)
    order = np.argsort(eigenvalues)
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    x = eigenvectors[:, 1]
    y = eigenvectors[:, 2]
    if x.max() - x.min() > 1e-9:
        x = (x - x.min()) / (x.max() - x.min()) * (die["x2"] - die["x1"]) + die["x1"]
    else:
        x = np.full(n_blocks, (die["x1"] + die["x2"]) / 2)
    if y.max() - y.min() > 1e-9:
        y = (y - y.min()) / (y.max() - y.min()) * (die["y2"] - die["y1"]) + die["y1"]
    else:
        y = np.full(n_blocks, (die["y1"] + die["y2"]) / 2)
    block_pos = np.column_stack([x, y]).astype(np.float32)
    print(f"    spectral done in {time.time()-t0:.1f}s", flush=True)
    return block_pos


def grid_init(n_blocks, die):
    cols = int(math.ceil(math.sqrt(n_blocks)))
    rows = int(math.ceil(n_blocks / cols))
    block_w = (die["x2"] - die["x1"]) / cols
    block_h = (die["y2"] - die["y1"]) / rows
    block_pos = np.zeros((n_blocks, 2), dtype=np.float32)
    for b in range(n_blocks):
        col = b % cols
        row = b // cols
        block_pos[b, 0] = die["x1"] + (col + 0.5) * block_w
        block_pos[b, 1] = die["y1"] + (row + 0.5) * block_h
    return block_pos


def adam_refinement(block_pos, bb_wires, n_iters=100, die=None):
    """Adam-style optimization on block positions to minimize inter-block HPWL.

    Adam update: m = beta1*m + (1-beta1)*g; v = beta2*v + (1-beta2)*g^2
                 update = m / (sqrt(v) + eps) * lr
    """
    print(f"  Adam refinement ({n_iters} iters, {len(bb_wires):,} pairs)...", flush=True)
    t0 = time.time()
    if not bb_wires:
        return block_pos
    keys = np.array(list(bb_wires.keys()), dtype=np.int32)
    weights = np.array(list(bb_wires.values()), dtype=np.float32)
    n_blocks = block_pos.shape[0]
    # Use sub-sampling for very large bb_wires
    max_pairs = 200_000
    if len(keys) > max_pairs:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(keys), size=max_pairs, replace=False)
        keys = keys[idx]
        weights = weights[idx]
        print(f"    subsampled to {max_pairs:,} pairs", flush=True)

    # Adam state
    m = np.zeros_like(block_pos)
    v = np.zeros_like(block_pos)
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    lr = 500.0

    for it in range(n_iters):
        # Compute gradient of HPWL: g_b1 += w * sign(x_b1 - x_b2)
        diff = block_pos[keys[:, 1]] - block_pos[keys[:, 0]]
        sign_diff = np.sign(diff)
        forces = np.zeros_like(block_pos)
        np.add.at(forces[:, 0], keys[:, 0], weights * sign_diff[:, 0])
        np.add.at(forces[:, 1], keys[:, 0], weights * sign_diff[:, 1])
        np.add.at(forces[:, 0], keys[:, 1], -weights * sign_diff[:, 0])
        np.add.at(forces[:, 1], keys[:, 1], -weights * sign_diff[:, 1])
        # Normalize by max force
        force_norm = np.abs(forces).max() + 1e-9
        forces = forces / force_norm

        # Adam update
        m = beta1 * m + (1 - beta1) * forces
        v = beta2 * v + (1 - beta2) * (forces ** 2)
        m_hat = m / (1 - beta1 ** (it + 1))
        v_hat = v / (1 - beta2 ** (it + 1))
        update = lr * m_hat / (np.sqrt(v_hat) + eps)

        block_pos -= update
        if die is not None:
            block_pos[:, 0] = np.clip(block_pos[:, 0], die["x1"], die["x2"])
            block_pos[:, 1] = np.clip(block_pos[:, 1], die["y1"], die["y2"])
    print(f"    Adam done in {time.time()-t0:.1f}s", flush=True)
    return block_pos


def place_within_blocks(positions, assignment, block_pos, n_blocks, die, seed=42):
    rng = np.random.default_rng(seed)
    n_cells = positions.shape[0]
    unique, counts = np.unique(assignment, return_counts=True)
    block_radius = np.zeros(n_blocks, dtype=np.float32)
    block_radius_dict = {}
    for b, c in zip(unique, counts):
        block_radius_dict[int(b)] = (c ** 0.5) * 200
    default_r = float(np.median(list(block_radius_dict.values())))
    for c in range(n_cells):
        b = int(assignment[c])
        center = block_pos[b]
        r = block_radius_dict.get(b, default_r)
        positions[c, 0] = center[0] + rng.uniform(-r, r)
        positions[c, 1] = center[1] + rng.uniform(-r, r)
    positions[:, 0] = np.clip(positions[:, 0], die["x1"], die["x2"])
    positions[:, 1] = np.clip(positions[:, 1], die["y1"], die["y2"])
    return positions


def compute_hpwl_csr(positions, indices, indptr, n_nets, chunk=5_000_000):
    total = 0.0
    n_nets = int(n_nets)
    t0 = time.time()
    for start in range(0, n_nets, chunk):
        end = min(start + chunk, n_nets)
        for i in range(start, end):
            s = indptr[i]
            e = indptr[i + 1]
            if e - s < 2:
                continue
            cells = indices[s:e]
            xs = positions[cells, 0]
            ys = positions[cells, 1]
            total += (xs.max() - xs.min()) + (ys.max() - ys.min())
    return total, total / max(1, n_nets)


def run_scale(n_total_cells, label, n_blocks, n_starts=3, seed=42):
    print(f"\n=== {label}: {n_total_cells:,} cells, {n_blocks} blocks, {n_starts} starts ===", flush=True)
    t0 = time.time()
    positions, all_cell_indices, indptr, n_nets, cell_to_net_data = build_synthetic(
        n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=seed,
    )
    build_t = time.time() - t0
    side_um = math.sqrt(n_total_cells / 0.375)
    side_dbu = side_um * 1000
    die = {"x1": 0, "y1": 0, "x2": side_dbu, "y2": side_dbu}
    print(f"  die: {side_dbu:.0f} x {side_dbu:.0f} DBU", flush=True)
    mem = (positions.nbytes + all_cell_indices.nbytes + indptr.nbytes) / 1e9
    print(f"  built in {build_t:.1f}s, mem {mem:.2f}GB", flush=True)

    best_hpwl = float('inf')
    best_positions = None

    block_size = (n_total_cells + n_blocks - 1) // n_blocks
    for start_idx in range(n_starts):
        print(f"\n  --- Start {start_idx+1}/{n_starts} (seed={seed+start_idx}) ---", flush=True)
        # Partition
        t0 = time.time()
        assignment = bfs_partition_compact(
            n_total_cells, n_nets, all_cell_indices, indptr,
            n_blocks, block_size, cell_to_net_data, seed=seed+start_idx,
        )
        part_t = time.time() - t0

        # Block wires
        bb_wires = compute_block_wires(assignment, all_cell_indices, indptr, n_nets, n_blocks)

        # Spectral
        t0 = time.time()
        block_pos = spectral_top_placement(bb_wires, n_blocks, die, seed=seed+start_idx)
        sp_t = time.time() - t0

        # Adam refinement
        t0 = time.time()
        block_pos = adam_refinement(block_pos, bb_wires, n_iters=100, die=die)
        ref_t = time.time() - t0

        # Place cells
        t0 = time.time()
        pos = place_within_blocks(np.zeros((n_total_cells, 2), dtype=np.float32),
                                   assignment, block_pos, n_blocks, die, seed=seed+start_idx)
        place_t = time.time() - t0

        # HPWL
        t0 = time.time()
        total_hpwl, per_net_hpwl = compute_hpwl_csr(pos, all_cell_indices, indptr, n_nets)
        hpwl_t = time.time() - t0
        print(f"  Start {start_idx+1} HPWL: {per_net_hpwl:,.0f} DBU/net ({hpwl_t:.1f}s)", flush=True)

        if per_net_hpwl < best_hpwl:
            best_hpwl = per_net_hpwl
            best_positions = pos.copy()
            best_assignment = assignment.copy()
            best_block_pos = block_pos.copy()
            best_wires = bb_wires

    # Now do per-cell refinement on the best
    print(f"\n  --- Per-cell refinement on best ({best_hpwl:,.0f}) ---", flush=True)
    t0 = time.time()
    # Build cell->nets for best
    offsets, net_list = cell_to_net_data
    # Use a quick gradient descent on cell positions
    # Sample a fraction of cells to refine (100M is too many to refine all)
    n_refine = min(1_000_000, n_total_cells)
    rng = np.random.default_rng(seed)
    cell_idx_sample = rng.choice(n_total_cells, size=n_refine, replace=False)
    pos = best_positions.copy()
    lr_cell = 100.0
    for outer in range(5):
        for ci in cell_idx_sample:
            s = offsets[ci]
            e = offsets[ci + 1]
            if e - s == 0:
                continue
            # For each net containing this cell, compute its bbox
            cx = pos[ci, 0]
            cy = pos[ci, 1]
            # Move cell toward center of all its nets
            dx_total, dy_total, count = 0.0, 0.0, 0
            for slot in range(s, e):
                net_id = int(net_list[slot])
                ns, ne = indptr[net_id], indptr[net_id + 1]
                cells = all_cell_indices[ns:ne]
                xs = pos[cells, 0]
                ys = pos[cells, 1]
                xmin, xmax = xs.min(), xs.max()
                ymin, ymax = ys.min(), ys.max()
                # Cell is outside bbox in some dim, pull toward it
                if cx < xmin:
                    dx_total += xmin - cx
                elif cx > xmax:
                    dx_total += xmax - cx
                if cy < ymin:
                    dy_total += ymin - cy
                elif cy > ymax:
                    dy_total += ymax - cy
                count += 1
            if count > 0:
                pos[ci, 0] = cx + 0.1 * dx_total
                pos[ci, 1] = cy + 0.1 * dy_total
    pos[:, 0] = np.clip(pos[:, 0], die["x1"], die["x2"])
    pos[:, 1] = np.clip(pos[:, 1], die["y1"], die["y2"])
    refine_t = time.time() - t0
    print(f"  per-cell refine: {refine_t:.1f}s", flush=True)

    # Final HPWL
    t0 = time.time()
    total_hpwl, per_net_hpwl = compute_hpwl_csr(pos, all_cell_indices, indptr, n_nets)
    hpwl_t = time.time() - t0
    print(f"  Final HPWL after per-cell refine: {per_net_hpwl:,.0f} DBU/net", flush=True)

    return {
        "label": label,
        "n_cells": int(n_total_cells),
        "n_nets": int(n_nets),
        "n_blocks": int(n_blocks),
        "n_starts": n_starts,
        "build_time_s": build_t,
        "best_starts_hpwl": float(best_hpwl),
        "per_cell_refine_hpwl": float(per_net_hpwl),
        "per_net_hpwl_dbu": float(per_net_hpwl),
        "total_hpwl_dbu": float(total_hpwl),
        "memory_gb": mem,
    }


def main():
    print("=" * 60)
    print("  Cloud 100M v7 — Adam refinement + multi-start + per-cell refine")
    print("=" * 60)
    # 1M first to verify, then 100M
    scales = [
        (1_000_000, "1M_v7", 1000, 3),
        (100_000_000, "100M_v7", 6667, 3),
    ]
    results = []
    t_start = time.time()
    for n_cells, label, n_blocks, n_starts in scales:
        try:
            r = run_scale(n_cells, label, n_blocks, n_starts=n_starts)
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
                  f"{r['per_net_hpwl_dbu']:>12,.0f} DBU/net", flush=True)


if __name__ == "__main__":
    main()
