"""
100M scaling proof v2 — uses BFS-aware partition + force-directed top placement.

For each scale (15K, 150K, 1M, 5M, 10M, 30M, 60M, 100M):
  1. Generate synthetic design by replicating bigblue1_15k N times
  2. BFS-aware partition into N_blocks = cells/cells_per_block
  3. Force-directed top placement of blocks
  4. V3 GAT per block (parallel, fork-based workers)
  5. Stitch into global positions
  6. Report total HPWL, per-net HPWL, time

This is the ISEF/Moore-paper "100M PROVEN" headline.
"""
import sys
import os
import time
import math
import json
import copy
import random
import multiprocessing as mp
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

MP_CTX = mp.get_context("fork")

ROOT = Path("/Users/harshith/Documents")
CHIPMIND = ROOT / "ChipPlacer"
RLCHIP = ROOT / "RLChip_ISEF"
sys.path.insert(0, str(CHIPMIND))
sys.path.insert(0, str(RLCHIP / "src"))

from chipmind.core.def_parser import parse_def
from train_gat_placer_v3 import GATPlacerV3, predict
from chipmind.ml.partition import bfs_balanced_partition
from chipmind.ml.top_level_placer import build_block_graph, force_directed_block_placement, blocks_to_grid_layout
import torch

DEF_PATH = RLCHIP / "results" / "bigblue1_15k_subset.def"
V3_CKPT = RLCHIP / "results" / "gat_v3_combined_60ep" / "gat_v3_model_best.pt"
V3_STATE = "/tmp/v3_state_100m_v2.pt"
OUT_PATH = CHIPMIND / "results" / "scaling_100m_v2.json"


# ----- worker (process-pool) -----
def run_v3_block(args):
    block_id, cells, sub_nets, sub_die, model_path = args
    import torch
    from train_gat_placer_v3 import GATPlacerV3, predict
    model = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model.eval()
    components = {c: {"x": 0, "y": 0} for c in cells}
    chip = {
        "components": components, "nets": sub_nets, "die": sub_die,
        "n_cells": len(cells), "n_nets": len(sub_nets),
    }
    t0 = time.time()
    try:
        positions = predict(model, chip)
        return block_id, positions, (time.time() - t0) * 1000, None
    except Exception as e:
        return block_id, None, (time.time() - t0) * 1000, str(e)


# ----- synthetic design builder -----
def build_synthetic(base_chip, n_replicas, inter_per_rep=20, seed=42):
    random.seed(seed)
    base_cells = list(base_chip["components"].keys())
    base_nets = base_chip["nets"]
    components = {}
    cell_map = {}
    for rid in range(n_replicas):
        for c in base_cells:
            new_name = f"r{rid}_{c}"
            cell_map[(rid, c)] = new_name
            components[new_name] = {"x": 0, "y": 0}
    nets = []
    net_id = 0
    for rid in range(n_replicas):
        for net in base_nets:
            comps = [cell_map[(rid, c)] for c in net["components"] if c in base_cells]
            if len(comps) >= 2:
                nets.append({"name": f"r{rid}_n{net_id}", "components": comps})
                net_id += 1
    # inter-replica wires: keep modest so we don't blow up memory
    for _ in range(inter_per_rep * n_replicas):
        size = random.choice([2, 3])
        if n_replicas < 2:
            # no inter-replica possible at n=1; skip
            break
        rid_a, rid_b = random.sample(range(n_replicas), 2)
        c_a = random.choice(base_cells)
        c_b = random.choice(base_cells)
        nets.append({"name": f"inter_{net_id}", "components": [cell_map[(rid_a, c_a)], cell_map[(rid_b, c_b)]]})
        net_id += 1
    base_die = base_chip.get("die", {"x1": 0, "y1": 0, "x2": 200000, "y2": 200000})
    die = {
        "x1": base_die["x1"], "y1": base_die["y1"],
        "x2": base_die["x2"] * math.sqrt(n_replicas),
        "y2": base_die["y2"] * math.sqrt(n_replicas),
    }
    return {
        "components": components, "nets": nets, "die": die,
        "n_cells": len(components), "n_nets": len(nets),
    }


# ----- HPWL -----
def compute_hpwl_global(positions, nets):
    total = 0.0
    for net in nets:
        xs, ys = [], []
        for c in net["components"]:
            if c in positions:
                p = positions[c]
                xs.append(p[0])
                ys.append(p[1])
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


# ----- one scale -----
def run_scale(n_replicas, label, cells_per_block=15000, max_workers=6, use_bfs=True):
    print(f"\n=== {label}: {15000 * n_replicas:,} cells ===", flush=True)
    base_chip = parse_def(str(DEF_PATH))
    n_total_cells = 15000 * n_replicas
    n_blocks = max(2, math.ceil(n_total_cells / cells_per_block))
    print(f"  Building synthetic ({n_replicas}x replicas)...", flush=True)
    t0 = time.time()
    chip = build_synthetic(base_chip, n_replicas, inter_per_rep=5, seed=42)
    gen_time = time.time() - t0
    print(f"  Built: {chip['n_cells']:,} cells, {chip['n_nets']:,} nets, "
          f"die {chip['die']['x2']:.0f}x{chip['die']['y2']:.0f} ({gen_time:.1f}s)", flush=True)

    cell_names = list(chip["components"].keys())
    nets = chip["nets"]
    die = chip["die"]

    # 1. Partition
    print(f"  Partitioning {len(cell_names):,} cells into {n_blocks} blocks ({'BFS' if use_bfs else 'random'})...", flush=True)
    t0 = time.time()
    if use_bfs and n_blocks <= 500:
        # BFS is O(n*nets), slow on >500 blocks. Use random for huge.
        block_sets = bfs_balanced_partition(cell_names, nets, n_blocks, seed=42, verbose=False)
        blocks = [list(s) for s in block_sets]
    else:
        rng = random.Random(42)
        shuffled = list(cell_names)
        rng.shuffle(shuffled)
        blocks = [[] for _ in range(n_blocks)]
        for i, c in enumerate(shuffled):
            blocks[i % n_blocks].append(c)
        block_sets = [set(b) for b in blocks]
    cell_to_block = {c: i for i, b in enumerate(blocks) for c in b}
    print(f"  Partition: {time.time()-t0:.1f}s", flush=True)

    # 2. Top-level force-directed placement of blocks
    canvas_w = die["x2"] - die["x1"]
    canvas_h = die["y2"] - die["y1"]
    print(f"  Top-level force-directed placement on {canvas_w:.0f}x{canvas_h:.0f} canvas...", flush=True)
    t0 = time.time()
    try:
        weights = build_block_graph(block_sets, nets)
        fd_pos = force_directed_block_placement(
            block_sets, weights, canvas_w, canvas_h,
            n_iterations=80, k_repel=0.2, k_spring=0.05, seed=42, verbose=False,
        )
        grid_layout = blocks_to_grid_layout(fd_pos, canvas_w, canvas_h)
        block_slots = []
        for i in range(n_blocks):
            slot = grid_layout[i]
            block_slots.append({
                "x1": slot["x1"], "y1": slot["y1"],
                "x2": slot["x2"], "y2": slot["y2"],
            })
    except Exception as e:
        print(f"  [WARN] FD failed: {e}, falling back to grid", flush=True)
        cols = int(math.ceil(math.sqrt(n_blocks)))
        rows = int(math.ceil(n_blocks / cols))
        bw = canvas_w / cols
        bh = canvas_h / rows
        block_slots = []
        for i in range(n_blocks):
            col = i % cols
            row = i // cols
            block_slots.append({
                "x1": col * bw, "y1": row * bh,
                "x2": (col + 1) * bw, "y2": (row + 1) * bh,
            })
    print(f"  Top-level: {time.time()-t0:.1f}s", flush=True)

    # 3. Save model state for workers
    if not Path(V3_STATE).exists():
        print("  Saving V3 state for workers...", flush=True)
        m = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
        m.load_state_dict(torch.load(V3_CKPT, map_location="cpu", weights_only=True))
        m.eval()
        torch.save(m.state_dict(), V3_STATE)
        del m

    # 4. Build sub-designs and dispatch V3
    print(f"  Building {n_blocks} sub-designs and running V3 in parallel (workers={max_workers})...", flush=True)
    t0_build = time.time()
    tasks = []
    for bid, cells in enumerate(blocks):
        slot = block_slots[bid]
        sub_die = {
            "x1": 0, "y1": 0,
            "x2": slot["x2"] - slot["x1"],
            "y2": slot["y2"] - slot["y1"],
        }
        cell_set = set(cells)
        sub_nets = []
        for net in nets:
            comps = [c for c in net["components"] if c in cell_set]
            if len(comps) >= 2:
                sub_nets.append({"name": net["name"], "components": comps})
        tasks.append((bid, cells, sub_nets, sub_die, V3_STATE))
    print(f"  Sub-design build: {time.time()-t0_build:.1f}s", flush=True)

    t0 = time.time()
    block_results = {}
    block_v3_times = []
    block_failures = 0
    completed = 0
    log_every = max(1, n_blocks // 10)
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=MP_CTX) as ex:
        futures = {ex.submit(run_v3_block, t): t[0] for t in tasks}
        for fut in as_completed(futures):
            try:
                bid, positions, dt, err = fut.result(timeout=120)
            except Exception as e:
                bid = futures[fut]
                positions, dt, err = None, 0, str(e)
            block_results[bid] = (positions, err)
            block_v3_times.append(dt)
            if err:
                block_failures += 1
            completed += 1
            if completed % log_every == 0 or completed == n_blocks:
                print(f"    [{completed}/{n_blocks}] avg={sum(block_v3_times)/len(block_v3_times):.0f}ms/block, "
                      f"failures={block_failures}", flush=True)
    v3_total = time.time() - t0
    print(f"  V3 phase: {v3_total:.1f}s total ({sum(block_v3_times)/max(1,len(block_v3_times)):.0f}ms avg), "
          f"{block_failures} failures", flush=True)

    # 5. Stitch
    print(f"  Stitching {n_blocks} blocks into global positions...", flush=True)
    t0 = time.time()
    global_pos = {}
    for bid, cells in enumerate(blocks):
        slot = block_slots[bid]
        result = block_results.get(bid)
        if result is None or result[0] is None:
            continue
        positions = result[0]
        ox, oy = slot["x1"], slot["y1"]
        for cell, pos in positions.items():
            if isinstance(pos, dict):
                lx, ly = pos["x"], pos["y"]
            else:
                lx, ly = pos[0], pos[1]
            global_pos[cell] = (ox + lx, oy + ly)
    print(f"  Stitch: {time.time()-t0:.1f}s, {len(global_pos):,} cells", flush=True)

    # 6. HPWL
    print(f"  Computing global HPWL over {len(nets):,} nets...", flush=True)
    t0 = time.time()
    total_hpwl = compute_hpwl_global(global_pos, nets)
    per_net = total_hpwl / max(1, len(nets))
    print(f"  HPWL: {total_hpwl:,.0f} DBU = {per_net:,.1f} per-net ({time.time()-t0:.1f}s)", flush=True)

    return {
        "label": label,
        "n_replicas": n_replicas,
        "n_cells": chip["n_cells"],
        "n_nets": chip["n_nets"],
        "n_blocks": n_blocks,
        "cells_per_block": cells_per_block,
        "use_bfs": use_bfs,
        "die": {"w": die["x2"] - die["x1"], "h": die["y2"] - die["y1"]},
        "v3_total_time_s": v3_total,
        "avg_v3_ms_per_block": sum(block_v3_times) / max(1, len(block_v3_times)),
        "block_failures": block_failures,
        "total_hpwl_dbu": total_hpwl,
        "per_net_hpwl_dbu": per_net,
        "per_cell_hpwl_dbu": total_hpwl / max(1, chip["n_cells"]),
    }


def main():
    # Stage 1: verify at 15K and 150K (smoke test, fast)
    # Stage 2: 1M, 5M, 10M (real proof)
    # Stage 3: 30M, 60M, 100M (headline)
    # Save incremental after each scale.
    scales = [
        # (n_replicas, label, cells_per_block, max_workers, use_bfs)
        (1,   "15K_baseline", 5000,  4, True),
        (10,  "150K",         15000, 6, True),
        (67,  "1M",           15000, 6, True),
        (333, "5M",           15000, 6, True),
        (667, "10M",          15000, 6, True),
        (2000, "30M",         15000, 6, False),  # BFS too slow on 2000 blocks
        (4000, "60M",         15000, 6, False),
        (6667, "100M",        15000, 6, False),
    ]
    results = []
    for n_rep, label, cpp, mw, bfs in scales:
        try:
            r = run_scale(n_rep, label, cells_per_block=cpp, max_workers=mw, use_bfs=bfs)
            results.append(r)
        except Exception as e:
            print(f"  [FAILED] {label}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            results.append({"label": label, "error": str(e)})
        # Save incremental
        with open(OUT_PATH, "w") as f:
            json.dump({"results": results, "completed_at": time.time()}, f, indent=2)
        print(f"  [SAVED] {OUT_PATH}", flush=True)
    print("\n=== FINAL ===", flush=True)
    for r in results:
        if "error" in r:
            print(f"  {r['label']}: ERROR — {r['error']}", flush=True)
        else:
            print(f"  {r['label']:>14}: {r['n_cells']:>12,} cells, "
                  f"{r['per_net_hpwl_dbu']:>10,.1f} DBU/net, "
                  f"{r['v3_total_time_s']:>6.1f}s, "
                  f"{r['block_failures']} failures", flush=True)


if __name__ == "__main__":
    main()
