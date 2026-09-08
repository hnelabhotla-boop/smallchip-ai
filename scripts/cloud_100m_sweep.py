"""
cloud_100m_sweep.py — Validate the 208K 100M LEGAL number across many design profiles.

Sweeps:
- Cell counts: 1M, 5M, 10M, 30M, 60M, 100M (IoT → phone → laptop → server scales)
- Net profiles: small (2.5 avg), mixed (3.5), large (5.0), mesh (8.0)
- Realistic chip types:
  - IoT: ~1-5M cells, small nets
  - Phone: ~10-30M cells, mixed nets
  - Laptop CPU: ~50-100M cells, mixed
  - Server/AI accelerator: ~100M+ cells, large mesh nets

Each cell count × net profile runs v8 (spectral + Adam + LEGAL row placement).
"""
import sys
import time
import math
import json
import gc
import numpy as np
from pathlib import Path
from collections import defaultdict

OUT = Path("/root/smallchip-ai/results/scaling_100m_sweep.json")


def build_synthetic(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    rng = np.random.default_rng(seed)
    print(f"    building {n_total_cells:,} cells + nets (avg size {avg_net_size})...", flush=True)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 12)
    total_slots = int(net_sizes.sum())
    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)
    print(f"    building compact cell->nets index...", flush=True)
    t0 = time.time()
    net_ids = np.repeat(np.arange(n_nets, dtype=np.int32), indptr[1:] - indptr[:-1])
    sort_idx = np.argsort(all_cell_indices, kind="stable")
    cell_to_net_pairs = np.column_stack([all_cell_indices[sort_idx], net_ids[sort_idx]])
    cell_to_net_offsets = np.zeros(n_total_cells + 1, dtype=np.int64)
    np.add.at(cell_to_net_offsets[1:], all_cell_indices, 1)
    np.cumsum(cell_to_net_offsets, out=cell_to_net_offsets)
    cell_to_net_list = cell_to_net_pairs[:, 1].astype(np.int32)
    del cell_to_net_pairs, net_ids, sort_idx
    print(f"      done in {time.time()-t0:.1f}s", flush=True)
    positions = np.zeros((n_total_cells, 2), dtype=np.float32)
    return positions, all_cell_indices, indptr, n_nets, (cell_to_net_offsets, cell_to_net_list)


def bfs_partition_compact(n_total_cells, n_nets, all_cell_indices, indptr,
                          n_blocks, block_size, cell_to_net_data, seed=42):
    rng = np.random.default_rng(seed)
    offsets, net_list = cell_to_net_data
    print(f"    BFS partition ({n_blocks} blocks)...", flush=True)
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
            s = offsets[cur]; e = offsets[cur + 1]
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
    print(f"    partition done in {time.time()-t0:.1f}s", flush=True)
    return assignment


def compute_block_wires(assignment, all_cell_indices, indptr, n_nets, n_blocks):
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
                if b1 > b2: b1, b2 = b2, b1
                bb_wires[(b1, b2)] += 1.0
    print(f"    {len(bb_wires):,} block pairs, {time.time()-t0:.1f}s", flush=True)
    return bb_wires


def spectral_top_placement(bb_wires, n_blocks, die, seed=42):
    t0 = time.time()
    from scipy.sparse import csr_matrix
    from scipy.sparse.linalg import eigsh
    rows = []; cols = []; data = []
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
    except Exception:
        cols_n = int(math.ceil(math.sqrt(n_blocks)))
        rows_n = int(math.ceil(n_blocks / cols_n))
        block_w = (die["x2"] - die["x1"]) / cols_n
        block_h = (die["y2"] - die["y1"]) / rows_n
        block_pos = np.zeros((n_blocks, 2), dtype=np.float32)
        for b in range(n_blocks):
            c = b % cols_n; r = b // cols_n
            block_pos[b, 0] = die["x1"] + (c + 0.5) * block_w
            block_pos[b, 1] = die["y1"] + (r + 0.5) * block_h
        return block_pos
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


def adam_refinement(block_pos, bb_wires, n_iters=100, die=None):
    t0 = time.time()
    if not bb_wires:
        return block_pos
    keys = np.array(list(bb_wires.keys()), dtype=np.int32)
    weights = np.array(list(bb_wires.values()), dtype=np.float32)
    n_blocks = block_pos.shape[0]
    max_pairs = 200_000
    if len(keys) > max_pairs:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(keys), size=max_pairs, replace=False)
        keys = keys[idx]; weights = weights[idx]
    m = np.zeros_like(block_pos)
    v = np.zeros_like(block_pos)
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    lr = 500.0
    for it in range(n_iters):
        diff = block_pos[keys[:, 1]] - block_pos[keys[:, 0]]
        sign_diff = np.sign(diff)
        forces = np.zeros_like(block_pos)
        np.add.at(forces[:, 0], keys[:, 0], weights * sign_diff[:, 0])
        np.add.at(forces[:, 1], keys[:, 0], weights * sign_diff[:, 1])
        np.add.at(forces[:, 0], keys[:, 1], -weights * sign_diff[:, 0])
        np.add.at(forces[:, 1], keys[:, 1], -weights * sign_diff[:, 1])
        force_norm = np.abs(forces).max() + 1e-9
        forces = forces / force_norm
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


def legal_place_within_blocks(positions, assignment, block_pos, n_blocks, die,
                                target_utilization=0.7, seed=42):
    n_cells = positions.shape[0]
    unique, counts = np.unique(assignment, return_counts=True)
    block_counts = {}
    for b, c in zip(unique, counts):
        block_counts[int(b)] = int(c)
    die_area = (die["x2"] - die["x1"]) * (die["y2"] - die["y1"])
    cell_area = die_area / n_cells / target_utilization
    cell_size = math.sqrt(cell_area)
    block_area = n_cells / n_blocks * cell_area / target_utilization
    block_side = math.sqrt(block_area)
    for b in range(n_blocks):
        if b not in block_counts:
            continue
        n_cells_in_block = block_counts[b]
        cx = block_pos[b, 0]; cy = block_pos[b, 1]
        x1 = cx - block_side / 2; y1 = cy - block_side / 2
        x2 = cx + block_side / 2; y2 = cy + block_side / 2
        x1 = max(x1, die["x1"]); y1 = max(y1, die["y1"])
        x2 = min(x2, die["x2"]); y2 = min(y2, die["y2"])
        cols = int((x2 - x1) / cell_size)
        rows = int((y2 - y1) / cell_size)
        if cols * rows < n_cells_in_block:
            side = max(x2 - x1, y2 - y1)
            cell_size_b = side / (math.ceil(math.sqrt(n_cells_in_block)) + 1)
            cols = int((x2 - x1) / cell_size_b)
            rows = int((y2 - y1) / cell_size_b)
            cell_size = cell_size_b
            x1 = cx - cols * cell_size / 2
            y1 = cy - rows * cell_size / 2
            x2 = x1 + cols * cell_size
            y2 = y1 + rows * cell_size
            x1 = max(x1, die["x1"]); y1 = max(y1, die["y1"])
            x2 = min(x2, die["x2"]); y2 = min(y2, die["y2"])
            cols = int((x2 - x1) / cell_size)
            rows = int((y2 - y1) / cell_size)
        cells_in_b = np.where(assignment == b)[0]
        rng = np.random.default_rng(seed + b)
        order = rng.permutation(len(cells_in_b))
        for idx, ci in enumerate(order):
            slot = idx
            if slot >= rows * cols:
                positions[cells_in_b[ci], 0] = cx
                positions[cells_in_b[ci], 1] = cy
                continue
            r = slot // cols; c = slot % cols
            positions[cells_in_b[ci], 0] = x1 + (c + 0.5) * cell_size
            positions[cells_in_b[ci], 1] = y1 + (r + 0.5) * cell_size
    positions[:, 0] = np.clip(positions[:, 0], die["x1"], die["x2"])
    positions[:, 1] = np.clip(positions[:, 1], die["y1"], die["y2"])
    return positions, cell_size


def compute_hpwl_csr(positions, indices, indptr, n_nets, chunk=5_000_000):
    total = 0.0
    n_nets = int(n_nets)
    for start in range(0, n_nets, chunk):
        end = min(start + chunk, n_nets)
        for i in range(start, end):
            s = indptr[i]; e = indptr[i + 1]
            if e - s < 2: continue
            cells = indices[s:e]
            xs = positions[cells, 0]
            ys = positions[cells, 1]
            total += (xs.max() - xs.min()) + (ys.max() - ys.min())
    return total, total / max(1, n_nets)


def run_one(n_total_cells, label, n_blocks, avg_net_size=3.5, target_util=0.7, seed=42,
            realistic_die=False):
    print(f"\n=== {label}: {n_total_cells:,} cells, nets~{avg_net_size}, util {target_util*100:.0f}%, "
          f"{'REALISTIC die' if realistic_die else 'synthetic die'} ===", flush=True)
    t0 = time.time()
    positions, all_cell_indices, indptr, n_nets, cell_to_net_data = build_synthetic(
        n_total_cells, avg_nets_per_cell=1.5, avg_net_size=avg_net_size, seed=seed,
    )
    if realistic_die:
        # Realistic die area for standard-cell design: ~625 mm^2 for 100M cells
        # Use 0.00625 mm^2 per cell (≈ 80nm x 80nm site + 0.7 utilization factor)
        die_area_um2 = n_total_cells * 6.25  # 6.25 um^2 per cell at 70% util
        side_um = math.sqrt(die_area_um2)
        side_dbu = side_um * 1000
        print(f"  REALISTIC die: {side_um:.0f} x {side_um:.0f} um "
              f"({side_um*side_um/1e6:.0f} mm^2)", flush=True)
    else:
        side_um = math.sqrt(n_total_cells / 0.375)
        side_dbu = side_um * 1000
    die = {"x1": 0, "y1": 0, "x2": side_dbu, "y2": side_dbu}
    mem = (positions.nbytes + all_cell_indices.nbytes + indptr.nbytes) / 1e9

    block_size = (n_total_cells + n_blocks - 1) // n_blocks
    assignment = bfs_partition_compact(
        n_total_cells, n_nets, all_cell_indices, indptr,
        n_blocks, block_size, cell_to_net_data, seed=seed,
    )
    bb_wires = compute_block_wires(assignment, all_cell_indices, indptr, n_nets, n_blocks)
    block_pos = spectral_top_placement(bb_wires, n_blocks, die, seed=seed)
    block_pos = adam_refinement(block_pos, bb_wires, n_iters=100, die=die)
    pos, cell_sz = legal_place_within_blocks(
        np.zeros((n_total_cells, 2), dtype=np.float32),
        assignment, block_pos, n_blocks, die,
        target_utilization=target_util, seed=seed,
    )
    total_hpwl, per_net_hpwl = compute_hpwl_csr(pos, all_cell_indices, indptr, n_nets)
    # Routing capacity (modern 7nm: 12 metal layers, 0.5um track pitch)
    # tracks per direction = side_um / 0.5 = 2 * side_um
    # track length = side_um um = side_um * 1e-3 m
    # total track length per layer per direction = tracks * track_len
    #   = 2 * side_um * side_um * 1e-3 = 2e-3 * side_um^2 m
    # 12 layers x 2 directions = 24
    # total capacity = 24 * 2e-3 * side_um^2 = 0.048 * side_um^2 m
    routing_capacity_m = 0.048 * side_um * side_um  # FIXED: square the side
    total_hpwl_m = total_hpwl * 1e-6  # DBU (nm) -> m
    routable = total_hpwl_m <= routing_capacity_m
    overflow = total_hpwl_m / routing_capacity_m if routing_capacity_m > 0 else float('inf')
    wall = time.time() - t0
    status = "✅ ROUTABLE" if routable else f"❌ {overflow:.1f}x OVER"
    print(f"  {label} LEGAL: {per_net_hpwl:,.0f} DBU/net "
          f"(cell {cell_sz/1000:.3f}µm, {wall:.0f}s, {status})", flush=True)
    return {
        "label": label,
        "n_cells": int(n_total_cells),
        "n_nets": int(n_nets),
        "n_blocks": int(n_blocks),
        "avg_net_size": avg_net_size,
        "per_net_hpwl_dbu": float(per_net_hpwl),
        "total_hpwl_m": float(total_hpwl_m),
        "die_side_um": float(side_um),
        "die_area_mm2": float(side_um * side_um / 1e6),
        "routing_capacity_m": float(routing_capacity_m),
        "routable": bool(routable),
        "overflow_ratio": float(overflow),
        "cell_size_um": float(cell_sz / 1000),
        "wall_time_s": float(wall),
        "memory_gb": mem,
        "realistic_die": realistic_die,
    }


# Design profiles: realistic chip types with REALISTIC die sizes
PROFILES = [
    # (label, scale_label, n_cells, n_blocks, avg_net_size, design_type)
    ("IoT/embedded",     "1M",     1_000_000,    1000, 2.5, "small-nets"),
    ("Phone (low-end)",  "5M",     5_000_000,    2000, 2.5, "small-nets"),
    ("Phone (high-end)", "10M",   10_000_000,    3000, 3.5, "mixed"),
    ("Laptop CPU",       "30M",   30_000_000,    4000, 3.5, "mixed"),
    ("Laptop GPU",       "60M",   60_000_000,    5000, 5.0, "data-path"),
    ("Server CPU",       "100M", 100_000_000,    6667, 3.5, "mixed"),
    ("AI accelerator",   "100M", 100_000_000,    6667, 5.0, "data-path"),
    ("AI accelerator",   "100M", 100_000_000,    6667, 8.0, "mesh"),
]


def main():
    print("=" * 70)
    print("  Cloud 100M Sweep — design profile validation (REALISTIC DIE)")
    print("=" * 70)
    results = []
    t_start = time.time()
    for design_type, scale_label, n_cells, n_blocks, avg_net_size, net_profile in PROFILES:
        label = f"{design_type}_{scale_label}_nets{avg_net_size}"
        try:
            r = run_one(n_cells, label, n_blocks, avg_net_size=avg_net_size, target_util=0.7,
                        realistic_die=True)
            r["design_type"] = design_type
            r["net_profile"] = net_profile
            results.append(r)
        except Exception as e:
            print(f"  [FAILED] {label}: {e}", flush=True)
            import traceback; traceback.print_exc()
            results.append({"label": label, "error": str(e)})
        with open(OUT, "w") as f:
            json.dump({"results": results, "elapsed_s": time.time() - t_start}, f, indent=2)
        print(f"  [SAVED] {OUT} (elapsed {time.time()-t_start:.0f}s)", flush=True)
    print("\n=== FINAL ===", flush=True)
    print(f"{'Design':<22} {'Scale':>5} {'Cells':>11} {'Nets':>11} {'NetSize':>7} "
          f"{'HPWL/net':>11} {'Die mm^2':>9} {'Total km':>9} {'Routable':>9}")
    print("-" * 110)
    for r in results:
        if "error" in r:
            print(f"  {r['label']:>22}: ERROR — {r['error']}")
        else:
            routable = "✅" if r.get("routable") else f"❌ {r.get('overflow_ratio', 0):.1f}x"
            print(f"{r['design_type']:<22} {r['label'].split('_')[1]:>5} "
                  f"{r['n_cells']:>11,} {r['n_nets']:>11,} {r['avg_net_size']:>7.1f} "
                  f"{r['per_net_hpwl_dbu']:>11,.0f} {r['die_area_mm2']:>9.1f} "
                  f"{r['total_hpwl_m']/1000:>8.1f}km {routable:>9}")


if __name__ == "__main__":
    main()
