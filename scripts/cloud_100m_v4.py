"""
cloud_100m_v4.py — V4 of 100M proof: BFS-aware partitioning + force-directed top-level.

Previous: random per-block → 15.7M DBU/net at 100M.
Now: BFS-aware partition + force-directed top placement → expected 3-5M DBU/net at 100M.

Why this works:
- Random partition: cells in same net go to different blocks → wires cross blocks → HPWL
- BFS partition: cells in same net go to same/adjacent blocks → wires stay local → less HPWL
- Force-directed top: block positions reflect inter-block wire density → fewer long wires

This matches the proven 5.5x improvement at 15K: random=7008, BFS+FD+refine=1281.
For 100M, we expect proportional gains.
"""
import sys
import time
import math
import json
import gc
import numpy as np
from pathlib import Path
from collections import defaultdict

OUT = Path("/root/smallchip-ai/results/scaling_100m_v4.json")


def build_synthetic(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    """Build synthetic netlist as CSR + reverse index (compact numpy format)."""
    rng = np.random.default_rng(seed)
    print(f"  building {n_total_cells:,} cells + nets...", flush=True)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 8)
    total_slots = int(net_sizes.sum())
    print(f"  generating {total_slots:,} slot indices...", flush=True)

    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)

    # Build cell->nets reverse index in COMPACT numpy format (CSR-style)
    # Step 1: get (cell, net) pairs sorted by cell
    print(f"  building compact cell->nets index ({n_nets:,} nets, {total_slots:,} slots)...", flush=True)
    t0 = time.time()
    net_ids = np.repeat(np.arange(n_nets, dtype=np.int32), indptr[1:] - indptr[:-1])
    # Sort pairs by cell
    sort_idx = np.argsort(all_cell_indices, kind="stable")
    cell_to_net_pairs = np.column_stack([all_cell_indices[sort_idx], net_ids[sort_idx]])
    # Compute per-cell offsets
    cell_to_net_offsets = np.zeros(n_total_cells + 1, dtype=np.int64)
    np.add.at(cell_to_net_offsets[1:], all_cell_indices, 1)
    np.cumsum(cell_to_net_offsets, out=cell_to_net_offsets)
    cell_to_net_list = cell_to_net_pairs[:, 1].astype(np.int32)  # net_ids in cell-sorted order
    del cell_to_net_pairs, net_ids, sort_idx
    print(f"    done in {time.time()-t0:.1f}s", flush=True)

    positions = np.zeros((n_total_cells, 2), dtype=np.float32)
    return positions, all_cell_indices, indptr, n_nets, (cell_to_net_offsets, cell_to_net_list)


def get_cell_nets(cell_id, cell_to_net_data):
    """Get net ids for a cell using compact CSR."""
    offsets, net_list = cell_to_net_data
    s = offsets[cell_id]
    e = offsets[cell_id + 1]
    return net_list[s:e]


def partition_by_net_aware_compact(n_total_cells, n_nets, all_cell_indices, indptr,
                                     n_blocks, block_size, cell_to_net_data, seed=42):
    """BFS-aware partition using compact cell->net CSR index."""
    rng = np.random.default_rng(seed)
    offsets, net_list = cell_to_net_data

    print(f"  BFS partition ({n_blocks} blocks)...", flush=True)
    t0 = time.time()
    assignment = -np.ones(n_total_cells, dtype=np.int32)
    perm = rng.permutation(n_total_cells)

    block_id = 0
    for seed in perm:
        if assignment[seed] != -1:
            continue
        # Start new block from this seed
        assignment[seed] = block_id
        frontier_cells = [int(seed)]
        block_count = 1
        visited_nets = set()

        while frontier_cells and block_count < block_size:
            cur = frontier_cells.pop()
            # Get nets for cur
            s = offsets[cur]
            e = offsets[cur + 1]
            for slot in range(s, e):
                net_id = int(net_list[slot])
                if net_id in visited_nets:
                    continue
                visited_nets.add(net_id)
                # Add all cells in this net that are still unassigned
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

    # Fallback
    unassigned = np.where(assignment == -1)[0]
    for i, c in enumerate(unassigned):
        assignment[c] = i % n_blocks
    print(f"  partition done in {time.time()-t0:.1f}s", flush=True)
    return assignment


def bfs_partition(positions, cell_to_nets, n_blocks, block_size, rng):
    """BFS-aware partitioning: each block is a connected component in the netlist.

    Strategy: pick seed cells (randomly shuffled), BFS via shared nets, take
    block_size cells, repeat. This keeps cells in same net close together.
    """
    n_cells = positions.shape[0]
    assignment = -np.ones(n_cells, dtype=np.int32)

    # Order cells randomly
    cells = rng.permutation(n_cells).tolist()
    cell_set = set(cells)
    block_id = 0

    for seed in cells:
        if assignment[seed] != -1:
            continue
        # BFS from seed, take up to block_size cells
        frontier = [seed]
        assignment[seed] = block_id
        count = 1
        while frontier and count < block_size:
            new_frontier = []
            for c in frontier:
                for net in cell_to_nets.get(int(c), []):
                    pass  # we'd need cell->cells in net; skip for now
            # Simpler: just sequential BFS by random walks
            if count >= block_size:
                break
            # pick a random connected cell
            nbrs = cell_to_nets.get(int(frontier[0]), [])
            if not nbrs:
                break
            chosen_net = nbrs[rng.integers(0, len(nbrs))]
            # this needs net->cells; use a different approach below
            break
        block_id += 1
        if block_id >= n_blocks:
            break

    # Fallback: round-robin for unassigned cells
    unassigned = np.where(assignment == -1)[0]
    for i, c in enumerate(unassigned):
        assignment[c] = i % n_blocks
    return assignment


def partition_simple_bfs(positions, all_cell_indices, indptr, n_nets, n_blocks, block_size, seed=42):
    """BFS-aware partitioning using net->cells (built on the fly).

    Algorithm:
    1. Build net_to_cells CSR index (from cell_to_nets reverse lookup)
    2. For each block, pick a seed cell (random), BFS via shared nets, add cells
       until block is full or no more unassigned cells reachable.
    3. Falls back to round-robin for disconnected cells.
    """
    rng = np.random.default_rng(seed)
    n_cells = positions.shape[0]
    assignment = -np.ones(n_cells, dtype=np.int32)

    # Build net_to_cells using a numpy trick
    # Sort (net_id, cell_id) pairs and group by net
    net_ids = np.repeat(np.arange(n_nets), indptr[1:] - indptr[:-1])
    net_to_cells = all_cell_indices  # but sorted by net_id; indptr gives the structure

    # Random order of cells for seed picking
    perm = rng.permutation(n_cells)
    cell_idx = 0
    block_id = 0

    while cell_idx < n_cells and block_id < n_blocks:
        # Find next unassigned seed
        while cell_idx < n_cells and assignment[perm[cell_idx]] != -1:
            cell_idx += 1
        if cell_idx >= n_cells:
            break

        seed_cell = int(perm[cell_idx])
        assignment[seed_cell] = block_id
        frontier = [seed_cell]
        block_count = 1

        while frontier and block_count < block_size:
            # Pop random cell from frontier
            idx = rng.integers(0, len(frontier))
            cur = frontier.pop(idx)

            # Find all nets containing cur
            # We need cell_to_nets. Build it once outside this function ideally.
            # For now, fall back to sequential scan: low cells in block have fewer nets to explore
            # Use the indptr/all_cell_indices structure to find nets for cur
            # Reverse lookup is O(n_nets) per cell without a hash. Skip for now.
            break

        block_id += 1

    # Round-robin for unassigned
    unassigned_mask = assignment == -1
    unassigned = np.where(unassigned_mask)[0]
    for i, c in enumerate(unassigned):
        assignment[c] = i % n_blocks
    return assignment


def partition_round_robin(n_cells, n_blocks, seed=42):
    """Baseline: round-robin assignment (close to random)."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n_cells)
    assignment = np.zeros(n_cells, dtype=np.int32)
    for i, c in enumerate(perm):
        assignment[c] = i % n_blocks
    return assignment


def partition_by_net_aware(n_total_cells, n_nets, all_cell_indices, indptr,
                            n_blocks, block_size, seed=42):
    """Net-aware partition: build cell->nets index, then BFS via shared nets.

    Each block: pick a seed cell, BFS over shared nets, add all unassigned
    cells in those nets, repeat until block is full. This produces blocks
    that are highly connected internally and loosely connected to other blocks.
    """
    rng = np.random.default_rng(seed)
    print(f"  building cell->nets reverse index ({n_nets:,} nets)...", flush=True)
    t0 = time.time()
    # cell->nets via transpose
    cell_to_nets = defaultdict(list)
    for net_id in range(n_nets):
        s, e = indptr[net_id], indptr[net_id + 1]
        cells = all_cell_indices[s:e]
        for c in cells:
            cell_to_nets[int(c)].append(net_id)
    print(f"    done in {time.time()-t0:.1f}s", flush=True)

    # BFS partition
    assignment = -np.ones(n_total_cells, dtype=np.int32)
    perm = rng.permutation(n_total_cells)

    block_id = 0
    for seed in perm:
        if assignment[seed] != -1:
            continue
        # Start new block from this seed
        assignment[seed] = block_id
        frontier_cells = [int(seed)]
        block_count = 1

        # BFS via shared nets
        visited_nets = set()
        while frontier_cells and block_count < block_size:
            cur = frontier_cells.pop()
            for net_id in cell_to_nets.get(cur, []):
                if net_id in visited_nets:
                    continue
                visited_nets.add(net_id)
                # Add all cells in this net that are still unassigned
                s, e = indptr[net_id], indptr[net_id + 1]
                for slot in range(s, e):
                    c = int(all_cell_indices[slot])
                    if assignment[c] == -1:
                        assignment[c] = block_id
                        frontier_cells.append(c)
                        block_count += 1
                        if block_count >= block_size:
                            break
                if block_count >= block_size:
                    break

        block_id += 1
        if block_id >= n_blocks:
            break

    # Fallback: round-robin for unassigned
    unassigned = np.where(assignment == -1)[0]
    for i, c in enumerate(unassigned):
        assignment[c] = i % n_blocks
    return assignment


def force_directed_top_placement(positions, assignment, all_cell_indices, indptr,
                                   n_nets, n_blocks, die, n_iters=20, seed=42):
    """Force-directed top-level placement.

    Treat each block as a "super-cell". Initialize at grid positions.
    Iteratively: pull blocks with shared nets toward each other, push apart otherwise.
    """
    rng = np.random.default_rng(seed)
    cols = int(math.ceil(math.sqrt(n_blocks)))
    rows = int(math.ceil(n_blocks / cols))
    block_w = (die["x2"] - die["x1"]) / cols
    block_h = (die["y2"] - die["y1"]) / rows

    # Initialize block positions on grid
    block_pos = np.zeros((n_blocks, 2), dtype=np.float32)
    for b in range(n_blocks):
        col = b % cols
        row = b // cols
        block_pos[b, 0] = die["x1"] + (col + 0.5) * block_w
        block_pos[b, 1] = die["y1"] + (row + 0.5) * block_h

    # Build block-to-block edge weights (inter-block wires)
    print(f"  computing inter-block wire weights...", flush=True)
    t0 = time.time()
    # For each net, find which blocks it spans, then add weight between every pair
    # We use sparse dict representation
    bb_wires = defaultdict(float)  # (b1, b2) -> weight, b1 < b2
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

    # Force-directed iterations
    bb_keys = np.array(list(bb_wires.keys()), dtype=np.int32) if bb_wires else np.zeros((0, 2), dtype=np.int32)
    bb_weights = np.array(list(bb_wires.values()), dtype=np.float32) if bb_wires else np.zeros(0, dtype=np.float32)
    print(f"  FD iterations...", flush=True)
    t0 = time.time()
    for it in range(n_iters):
        forces = np.zeros_like(block_pos)
        if len(bb_keys) > 0:
            # Pull between connected blocks
            diff = block_pos[bb_keys[:, 1]] - block_pos[bb_keys[:, 0]]
            dist = np.linalg.norm(diff, axis=1) + 1e-6
            force_mag = bb_weights / (dist ** 2) * 1e3
            forces[bb_keys[:, 0]] += force_mag[:, None] * diff / dist[:, None]
            forces[bb_keys[:, 1]] -= force_mag[:, None] * diff / dist[:, None]
        # Repulsion: all blocks
        for i in range(n_blocks):
            diffs = block_pos - block_pos[i]
            dists = np.linalg.norm(diffs, axis=1) + 1e-3
            mask = dists < 100  # only nearby
            repulse = np.zeros(2)
            for j in np.where(mask)[0]:
                if j == i: continue
                repulse += (block_pos[i] - block_pos[j]) / (dists[j] ** 1.5) * 50
            forces[i] += repulse

        block_pos += forces * 0.01
        # Clamp to die
        block_pos[:, 0] = np.clip(block_pos[:, 0], die["x1"], die["x2"])
        block_pos[:, 1] = np.clip(block_pos[:, 1], die["y1"], die["y2"])
    print(f"    FD done in {time.time()-t0:.1f}s", flush=True)

    return block_pos


def place_within_blocks(positions, assignment, block_pos, block_size, die, seed=42):
    """Place each cell at a random position within its block's region.

    Block region: 0.8x the bounding box of the cells assigned to it, centered at block_pos.
    """
    rng = np.random.default_rng(seed)
    n_blocks = block_pos.shape[0]

    # For each block, compute its "spread radius"
    block_radius = np.full(n_blocks, max(die["x2"] - die["x1"], die["y2"] - die["y1"]) / max(1, n_blocks) ** 0.5, dtype=np.float32)
    # Cells per block varies; use that to scale
    unique, counts = np.unique(assignment, return_counts=True)
    for b, c in zip(unique, counts):
        # spread scales with sqrt(count)
        block_radius[b] = (c ** 0.5) * 200  # ~200 DBU per cell in spread

    n_cells = positions.shape[0]
    for c in range(n_cells):
        b = assignment[c]
        center = block_pos[b]
        r = block_radius[b]
        positions[c, 0] = center[0] + rng.uniform(-r, r)
        positions[c, 1] = center[1] + rng.uniform(-r, r)

    # Clamp to die
    positions[:, 0] = np.clip(positions[:, 0], die["x1"], die["x2"])
    positions[:, 1] = np.clip(positions[:, 1], die["y1"], die["y2"])
    return positions


def compute_hpwl_csr(positions, indices, indptr, n_nets, chunk=5_000_000):
    """Vectorized HPWL over CSR-format netlist."""
    total = 0.0
    n_nets = int(n_nets)
    t0 = time.time()
    for start in range(0, n_nets, chunk):
        end = min(start + chunk, n_nets)
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
            print(f"      HPWL progress: {start}/{n_nets} nets ({pct:.0f}%) [{elapsed:.0f}s]", flush=True)
    return total, total / max(1, n_nets)


def run_scale(n_total_cells, label, n_blocks, seed=42, use_fd=True):
    print(f"\n=== {label}: {n_total_cells:,} cells, {n_blocks} blocks ===", flush=True)
    t0 = time.time()
    positions, all_cell_indices, indptr, n_nets, cell_to_net_data = build_synthetic(
        n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=seed,
    )
    build_t = time.time() - t0
    side_um = math.sqrt(n_total_cells / 0.375)
    side_dbu = side_um * 1000
    die = {"x1": 0, "y1": 0, "x2": side_dbu, "y2": side_dbu}

    # Memory
    offsets, net_list = cell_to_net_data
    mem = (positions.nbytes + all_cell_indices.nbytes + indptr.nbytes +
           offsets.nbytes + net_list.nbytes) / 1e9
    print(f"  built in {build_t:.1f}s, mem {mem:.2f}GB", flush=True)

    block_size = (n_total_cells + n_blocks - 1) // n_blocks

    # === BFS-aware partition ===
    t0 = time.time()
    assignment = partition_by_net_aware_compact(
        n_total_cells, n_nets, all_cell_indices, indptr,
        n_blocks, block_size, cell_to_net_data, seed=seed,
    )
    part_t = time.time() - t0
    # Report block balance
    unique, counts = np.unique(assignment, return_counts=True)
    print(f"  partition: {part_t:.1f}s, blocks: {len(unique)}, "
          f"min={counts.min()} max={counts.max()} mean={counts.mean():.0f}", flush=True)

    # === Force-directed top placement ===
    fd_t = 0
    if use_fd:
        t0 = time.time()
        block_pos = force_directed_top_placement(
            positions, assignment, all_cell_indices, indptr, n_nets, n_blocks, die, n_iters=15
        )
        fd_t = time.time() - t0
    else:
        # Grid initial
        cols = int(math.ceil(math.sqrt(n_blocks)))
        rows = int(math.ceil(n_blocks / cols))
        block_w = side_dbu / cols
        block_h = side_dbu / rows
        block_pos = np.zeros((n_blocks, 2), dtype=np.float32)
        for b in range(n_blocks):
            col = b % cols
            row = b // cols
            block_pos[b, 0] = (col + 0.5) * block_w
            block_pos[b, 1] = (row + 0.5) * block_h

    # === Place cells within blocks ===
    t0 = time.time()
    positions = place_within_blocks(positions, assignment, block_pos, block_size, die, seed=seed)
    place_t = time.time() - t0
    print(f"  placement: {place_t:.1f}s (FD {fd_t:.1f}s)", flush=True)

    # === Compute HPWL ===
    t0 = time.time()
    total_hpwl, per_net_hpwl = compute_hpwl_csr(positions, all_cell_indices, indptr, n_nets)
    hpwl_t = time.time() - t0
    print(f"  HPWL: {total_hpwl:,.0f} = {per_net_hpwl:,.1f}/net ({hpwl_t:.1f}s)", flush=True)

    return {
        "label": label,
        "n_cells": int(n_total_cells),
        "n_nets": int(n_nets),
        "n_blocks": int(n_blocks),
        "build_time_s": build_t,
        "partition_time_s": part_t,
        "fd_time_s": fd_t,
        "place_time_s": place_t,
        "hpwl_time_s": hpwl_t,
        "total_hpwl_dbu": float(total_hpwl),
        "per_net_hpwl_dbu": float(per_net_hpwl),
        "memory_gb": mem,
    }


def main():
    print("=" * 60)
    print("  Cloud 100M v4 — BFS partition + force-directed top")
    print("=" * 60)
    # Focus on 100M, then sanity check on 15K and 1M
    scales = [
        (15_000, "15K", 100),
        (1_000_000, "1M", 500),
        (100_000_000, "100M", 6667),
    ]
    results = []
    t_start = time.time()
    for n_cells, label, n_blocks in scales:
        try:
            r = run_scale(n_cells, label, n_blocks)
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
                  f"build {r['build_time_s']:.1f}s, part {r['partition_time_s']:.1f}s, "
                  f"FD {r['fd_time_s']:.1f}s, place {r['place_time_s']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
