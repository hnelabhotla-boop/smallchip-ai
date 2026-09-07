"""
placement_100m_demo.py — Local 100M cell demo for the interactive UI.

Generates a synthetic 100M cell netlist, runs BFS-aware partition + force-directed
top placement, returns a 200x200 heatmap (cell density per bin) and metrics.
"""
import sys
import time
import math
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from threading import Lock

# Make chipmind importable
sys.path.insert(0, str(Path(__file__).parent.parent))


def build_synthetic(n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=42):
    rng = np.random.default_rng(seed)
    n_nets = int(n_total_cells * avg_nets_per_cell / avg_net_size)
    net_sizes = np.clip(rng.normal(avg_net_size, 0.8, n_nets).astype(int), 2, 8)
    total_slots = int(net_sizes.sum())
    all_cell_indices = rng.integers(0, n_total_cells, size=total_slots, dtype=np.int32)
    indptr = np.zeros(n_nets + 1, dtype=np.int64)
    indptr[1:] = np.cumsum(net_sizes)

    # Compact cell->nets CSR
    net_ids = np.repeat(np.arange(n_nets, dtype=np.int32), indptr[1:] - indptr[:-1])
    sort_idx = np.argsort(all_cell_indices, kind="stable")
    cell_to_net_offsets = np.zeros(n_total_cells + 1, dtype=np.int64)
    np.add.at(cell_to_net_offsets[1:], all_cell_indices, 1)
    np.cumsum(cell_to_net_offsets, out=cell_to_net_offsets)
    cell_to_net_list = net_ids[sort_idx].astype(np.int32)
    del net_ids, sort_idx
    positions = np.zeros((n_total_cells, 2), dtype=np.float32)
    return positions, all_cell_indices, indptr, n_nets, (cell_to_net_offsets, cell_to_net_list)


def bfs_partition(n_total_cells, n_nets, all_cell_indices, indptr, n_blocks, block_size, cell_to_net_data, seed=42):
    rng = np.random.default_rng(seed)
    offsets, net_list = cell_to_net_data
    assignment = -np.ones(n_total_cells, dtype=np.int32)
    perm = rng.permutation(n_total_cells)
    block_id = 0
    for seed_cell in perm:
        if assignment[seed_cell] != -1:
            continue
        assignment[seed_cell] = block_id
        frontier = [int(seed_cell)]
        block_count = 1
        visited_nets = set()
        while frontier and block_count < block_size:
            cur = frontier.pop()
            s = offsets[cur]; e = offsets[cur + 1]
            for slot in range(s, e):
                net_id = int(net_list[slot])
                if net_id in visited_nets:
                    continue
                visited_nets.add(net_id)
                ns, ne = indptr[net_id], indptr[net_id + 1]
                for c in all_cell_indices[ns:ne]:
                    if assignment[c] == -1:
                        assignment[c] = block_id
                        frontier.append(int(c))
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
    return assignment


def place_partition_random(positions, assignment, block_pos, die, seed=42):
    """Place each cell at a position within its block's region."""
    rng = np.random.default_rng(seed)
    n_blocks = block_pos.shape[0]
    n_cells = positions.shape[0]
    cols = int(math.ceil(math.sqrt(n_blocks)))
    rows = int(math.ceil(n_blocks / cols))
    block_w = (die["x2"] - die["x1"]) / cols
    block_h = (die["y2"] - die["y1"]) / rows

    for b in range(n_blocks):
        col = b % cols
        row = b // cols
        block_x1 = die["x1"] + col * block_w
        block_y1 = die["y1"] + row * block_h
        cell_indices = np.where(assignment == b)[0]
        if len(cell_indices) == 0:
            continue
        count = len(cell_indices)
        side = int(math.ceil(math.sqrt(count)))
        for i, c in enumerate(cell_indices):
            ix = i % side
            iy = i // side
            positions[c, 0] = block_x1 + (ix + 0.5) * (block_w / side)
            positions[c, 1] = block_y1 + (iy + 0.5) * (block_h / side)

    return positions


def compute_heatmap(positions, die, grid_size=200):
    """Compute cell density per bin (200x200 default)."""
    gx = np.clip(((positions[:, 0] - die["x1"]) / (die["x2"] - die["x1"]) * grid_size).astype(np.int32), 0, grid_size - 1)
    gy = np.clip(((positions[:, 1] - die["y1"]) / (die["y2"] - die["y1"]) * grid_size).astype(np.int32), 0, grid_size - 1)
    bins = gx * grid_size + gy
    counts = np.bincount(bins, minlength=grid_size * grid_size)
    return counts.reshape(grid_size, grid_size).astype(np.int32)


def compute_hpwl_fast(positions, all_cell_indices, indptr, n_nets, sample_nets=2_000_000):
    """Compute HPWL using only a sample of nets (for speed)."""
    rng = np.random.default_rng(123)
    if n_nets > sample_nets:
        net_ids = rng.choice(n_nets, sample_nets, replace=False)
    else:
        net_ids = np.arange(n_nets)
    total = 0.0
    count = 0
    for net_id in net_ids:
        s, e = indptr[net_id], indptr[net_id + 1]
        if e - s < 2:
            continue
        cells = all_cell_indices[s:e]
        xs = positions[cells, 0]
        ys = positions[cells, 1]
        total += (xs.max() - xs.min()) + (ys.max() - ys.min())
        count += 1
    return total, total / max(1, count)


# Global state for the demo job
_demo_state = {
    "status": "idle",  # idle, building, partitioning, placing, done, error
    "progress": 0.0,
    "result": None,
    "error": None,
    "started_at": None,
    "elapsed_s": 0.0,
}
_state_lock = Lock()


def run_100m_demo(n_total_cells=10_000_000, n_blocks=2000, seed=42, use_bfs=True):
    """Run the 100M demo. Updates _demo_state as it goes.

    For 100M cells, use_bfs=False (random partition, much faster) to fit in
    the live demo time budget. For 10M and below, use_bfs=True.
    """
    global _demo_state
    try:
        with _state_lock:
            _demo_state = {
                "status": "building", "progress": 0.05, "result": None, "error": None,
                "started_at": time.time(), "elapsed_s": 0.0,
            }

        t0 = time.time()
        # Build
        positions, all_cell_indices, indptr, n_nets, cell_to_net_data = build_synthetic(
            n_total_cells, avg_nets_per_cell=1.5, avg_net_size=3.5, seed=seed
        )
        offsets, net_list = cell_to_net_data
        mem = (positions.nbytes + all_cell_indices.nbytes + indptr.nbytes +
               offsets.nbytes + net_list.nbytes) / 1e9
        build_t = time.time() - t0
        with _state_lock:
            _demo_state["status"] = "partitioning"
            _demo_state["progress"] = 0.30

        # Partition
        t0 = time.time()
        block_size = (n_total_cells + n_blocks - 1) // n_blocks
        if use_bfs and n_total_cells <= 50_000_000:
            assignment = bfs_partition(
                n_total_cells, n_nets, all_cell_indices, indptr,
                n_blocks, block_size, cell_to_net_data, seed=seed
            )
        else:
            # Random round-robin (fast for 100M)
            rng = np.random.default_rng(seed)
            assignment = rng.integers(0, n_blocks, size=n_total_cells, dtype=np.int32)
        part_t = time.time() - t0
        with _state_lock:
            _demo_state["status"] = "placing"
            _demo_state["progress"] = 0.65

        # Place (random within blocks)
        t0 = time.time()
        side_um = math.sqrt(n_total_cells / 0.375)
        side_dbu = side_um * 1000
        die = {"x1": 0, "y1": 0, "x2": side_dbu, "y2": side_dbu}
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
        positions = place_partition_random(positions, assignment, block_pos, die, seed=seed)
        place_t = time.time() - t0
        with _state_lock:
            _demo_state["status"] = "computing"
            _demo_state["progress"] = 0.85

        # Compute HPWL on sample (fast for 100M)
        t0 = time.time()
        sample_nets = 2_000_000 if n_total_cells <= 50_000_000 else 500_000
        total_hpwl, per_net_hpwl = compute_hpwl_fast(positions, all_cell_indices, indptr, n_nets, sample_nets=sample_nets)
        hpwl_t = time.time() - t0

        # Compute heatmap
        t0 = time.time()
        heatmap = compute_heatmap(positions, die, grid_size=200)
        heatmap_t = time.time() - t0

        total_t = build_t + part_t + place_t + hpwl_t + heatmap_t

        result = {
            "n_cells": int(n_total_cells),
            "n_nets": int(n_nets),
            "n_blocks": int(n_blocks),
            "used_bfs": use_bfs and n_total_cells <= 50_000_000,
            "per_net_hpwl_dbu": float(per_net_hpwl),
            "total_hpwl_dbu_estimate": float(total_hpwl * (n_nets / sample_nets)),
            "build_time_s": build_t,
            "partition_time_s": part_t,
            "place_time_s": place_t,
            "hpwl_time_s": hpwl_t,
            "heatmap_time_s": heatmap_t,
            "total_time_s": total_t,
            "die_size_um": side_um,
            "memory_gb": mem,
            "heatmap": heatmap.flatten().tolist(),
            "heatmap_size": 200,
        }

        with _state_lock:
            _demo_state["status"] = "done"
            _demo_state["progress"] = 1.0
            _demo_state["result"] = result
            _demo_state["elapsed_s"] = time.time() - _demo_state["started_at"]
        return result
    except Exception as e:
        with _state_lock:
            _demo_state["status"] = "error"
            _demo_state["error"] = str(e)
        raise


def get_demo_status():
    with _state_lock:
        s = dict(_demo_state)
    if s["started_at"] and s["status"] != "done":
        s["elapsed_s"] = time.time() - s["started_at"]
    return s


def start_demo_async(n_total_cells=10_000_000, n_blocks=2000, seed=42, use_bfs=True):
    """Start the demo in a background thread."""
    import threading
    if get_demo_status()["status"] in ("building", "partitioning", "placing", "computing"):
        return False, "demo already running"
    t = threading.Thread(target=run_100m_demo, args=(n_total_cells, n_blocks, seed, use_bfs), daemon=True)
    t.start()
    return True, "started"
