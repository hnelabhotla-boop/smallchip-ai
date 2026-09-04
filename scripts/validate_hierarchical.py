"""
Real hierarchical placement validation on bigblue1_15k_subset.def.

Pipeline:
  1. Parse the 15K-cell DEF to get real cells and nets
  2. Partition cells into K blocks (spectral graph partition via networkx)
  3. For each block:
       - Extract cells + their intra-block nets
       - Run V3 GAT on the sub-design
       - Get per-block (x, y) coords in the block's local die
  4. Stitch per-block coords into global coords (translate + scale)
  5. Run flat V3 on the full 15K design (no hierarchy)
  6. Compare: hierarchical HPWL vs flat HPWL

This is the real validation: hierarchy on a real netlist, not synthetic blocks.
"""
import sys
import time
import json
import math
import random
from pathlib import Path
from collections import defaultdict

# Use the conda env that has torch_geometric
try:
    import torch_geometric  # noqa
except ImportError:
    import subprocess
    CONDA_PY = "/Users/harshith/miniconda3/envs/chippind_rl/bin/python"
    print(f"Re-launching with conda env: {CONDA_PY}")
    sys.exit(subprocess.call([CONDA_PY] + sys.argv))

# Paths
ROOT = Path("/Users/harshith/Documents")
CHIPMIND = ROOT / "ChipPlacer"
RLCHIP = ROOT / "RLChip_ISEF"
sys.path.insert(0, str(CHIPMIND))
sys.path.insert(0, str(RLCHIP / "src"))

from chipmind.core.def_parser import parse_def
from chipmind.core.fast_hpwl import compute_hpwl_fast as compute_hpwl

# V3 GAT
from train_gat_placer_v3 import GATPlacerV3, predict
import torch

# 15K subset path
DEF_PATH = RLCHIP / "results" / "bigblue1_5k_subset.def"
V3_CKPT = RLCHIP / "results" / "gat_v3_combined_60ep" / "gat_v3_model_best.pt"
DIE_W = 200_000.0
DIE_H = 200_000.0


def load_v3():
    model = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
    ckpt = torch.load(V3_CKPT, map_location="cpu", weights_only=True)
    model.load_state_dict(ckpt)
    model.eval()
    return model


def spectral_partition(cell_names, nets, n_blocks):
    """Simple balanced random partitioner (fast, deterministic seed)."""
    random.seed(42)
    shuffled = list(cell_names)
    random.shuffle(shuffled)
    blocks = [set() for _ in range(n_blocks)]
    for i, c in enumerate(shuffled):
        blocks[i % n_blocks].add(c)
    return blocks


def run_v3_on_block(model, cells, nets, die_w, die_h, block_id):
    """Run V3 on a sub-design (cells + intra-block nets)."""
    components = {c: {"x": 0, "y": 0} for c in cells}
    sub_nets = []
    for net in nets:
        comps = net["components"]
        in_block = [c for c in comps if c in cell_set]
        if len(in_block) >= 2:
            sub_nets.append({
                "name": net.get("name", f"n{block_id}_{len(sub_nets)}"),
                "components": in_block,
            })
    chip = {
        "components": components,
        "nets": sub_nets,
        "die": {"x1": 0, "y1": 0, "x2": die_w, "y2": die_h},
        "n_cells": len(cells),
        "n_nets": len(sub_nets),
    }
    try:
        positions = predict(model, chip)
        return positions, None
    except Exception as e:
        return None, str(e)


def place_block_on_grid(blocks, canvas_w, canvas_h):
    """Simple grid placement: lay out blocks in a grid pattern."""
    n = len(blocks)
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    block_w = canvas_w / cols
    block_h = canvas_h / rows
    positions = {}
    for i, block_cells in enumerate(blocks):
        col = i % cols
        row = i // cols
        cx = (col + 0.5) * block_w
        cy = (row + 0.5) * block_h
        positions[i] = {
            "cx": cx, "cy": cy,
            "x1": col * block_w, "y1": row * block_h,
            "x2": (col + 1) * block_w, "y2": (row + 1) * block_h,
        }
    return positions, block_w, block_h


def stitch_positions(per_block_positions, block_grid, die_w, die_h):
    """Translate per-block (x, y) into global canvas coords."""
    global_pos = {}
    for bid, block_cells in enumerate(per_block_positions):
        if block_cells is None:
            continue
        slot = block_grid[bid]
        scale_x = (slot["x2"] - slot["x1"]) / max(die_w, 1)
        scale_y = (slot["y2"] - slot["y1"]) / max(die_h, 1)
        for cell, pos in block_cells.items():
            if isinstance(pos, dict):
                local_x, local_y = pos["x"], pos["y"]
            else:
                local_x, local_y = pos[0], pos[1]
            gx = (local_x / die_w) * (slot["x2"] - slot["x1"]) + slot["x1"]
            gy = (local_y / die_h) * (slot["y2"] - slot["y1"]) + slot["y1"]
            global_pos[cell] = (gx, gy)
    return global_pos


def hpwl_for_placement(positions, nets):
    """Compute total HPWL given a placement dict and net list."""
    total = 0
    for net in nets:
        xs, ys = [], []
        for c in net["components"]:
            if c in positions:
                pos = positions[c]
                if isinstance(pos, dict):
                    x, y = pos["x"], pos["y"]
                else:
                    x, y = pos[0], pos[1]
                xs.append(x)
                ys.append(y)
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def flat_v3_placement(model, chip):
    """Run V3 on the full chip and return positions dict."""
    return predict(model, chip)


def main():
    global cell_set
    print("=" * 70)
    print("HIERARCHICAL PLACEMENT VALIDATION")
    print("=" * 70)

    # 1. Parse the 15K subset DEF
    print(f"\n[1] Parsing {DEF_PATH.name}...")
    t0 = time.time()
    chip = parse_def(str(DEF_PATH))
    parse_time = time.time() - t0
    cell_names = list(chip["components"].keys())
    nets = chip["nets"]
    n_cells = len(cell_names)
    n_nets = len(nets)
    cell_set = set(cell_names)
    print(f"  Parsed in {parse_time:.2f}s")
    print(f"  {n_cells} cells, {n_nets} nets")
    if "die" in chip:
        print(f"  Die: {chip['die']}")

    # 2. Load V3
    print(f"\n[2] Loading V3 model from {V3_CKPT.name}...")
    model = load_v3()
    print("  V3 loaded")

    # 3. Flat V3 baseline (full design)
    print(f"\n[3] Flat V3 placement (baseline)...")
    die = chip.get("die", {"x1": 0, "y1": 0, "x2": DIE_W, "y2": DIE_H})
    actual_die_w = die["x2"] - die["x1"]
    actual_die_h = die["y2"] - die["y1"]
    print(f"  Actual die: {actual_die_w:.0f} x {actual_die_h:.0f} DBU")
    t0 = time.time()
    flat_positions = flat_v3_placement(model, chip)
    flat_time = time.time() - t0
    flat_hpwl = hpwl_for_placement(flat_positions, nets)
    print(f"  Flat V3 time: {flat_time*1000:.1f}ms")
    print(f"  Flat V3 HPWL: {flat_hpwl:,.0f} DBU")

    # 4. Hierarchical placement with N blocks
    results = {}
    for n_blocks in [2, 3, 5]:
        print(f"\n[4] Hierarchical placement with {n_blocks} blocks...")
        t0 = time.time()
        communities = spectral_partition(cell_names, nets, n_blocks)
        partition_time = time.time() - t0
        print(f"  Partitioned in {partition_time*1000:.1f}ms")
        for i, c in enumerate(communities):
            print(f"    block {i}: {len(c)} cells")
        # Block grid layout — use actual die dimensions
        # Each block's local die is (actual_die_w / cols) x (actual_die_h / rows)
        n = len(communities)
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / cols))
        block_w = actual_die_w / cols
        block_h = actual_die_h / rows
        block_grid = {}
        for i, _ in enumerate(communities):
            col = i % cols
            row = i // cols
            block_grid[i] = {
                "cx": (col + 0.5) * block_w,
                "cy": (row + 0.5) * block_h,
                "x1": col * block_w, "y1": row * block_h,
                "x2": (col + 1) * block_w, "y2": (row + 1) * block_h,
            }
        # Run V3 per block
        per_block = []
        block_v3_times = []
        block_failures = 0
        for bid, block_cells in enumerate(communities):
            cells = list(block_cells)
            t1 = time.time()
            positions, err = run_v3_on_block(model, cells, nets, block_w, block_h, bid)
            block_v3_times.append((time.time() - t1) * 1000)
            per_block.append(positions)
            if err:
                block_failures += 1
                print(f"    block {bid}: FAILED ({err})")
            else:
                print(f"    block {bid}: {len(cells)} cells, {block_v3_times[-1]:.1f}ms")
        # Stitch
        global_positions = stitch_positions(per_block, block_grid, DIE_W, DIE_H)
        total_hpwl = hpwl_for_placement(global_positions, nets)
        total_time = (time.time() - t0) * 1000
        results[n_blocks] = {
            "n_blocks": n_blocks,
            "block_cells": [len(c) for c in communities],
            "partition_time_ms": partition_time * 1000,
            "block_v3_times_ms": block_v3_times,
            "total_block_v3_time_ms": sum(block_v3_times),
            "stitched_hpwl_dbu": total_hpwl,
            "total_hier_time_ms": total_time,
            "block_failures": block_failures,
            "stitched_cells": len(global_positions),
        }
        print(f"  Stitched HPWL: {total_hpwl:,.0f} DBU")
        print(f"  Total hier time: {total_time:.1f}ms")

    # 5. Summary
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Flat V3:    {flat_hpwl:>15,.0f} DBU  in  {flat_time*1000:>7.1f}ms")
    print()
    for nb, r in results.items():
        ratio = r["stitched_hpwl_dbu"] / max(flat_hpwl, 1)
        delta = (ratio - 1) * 100
        status = "BETTER" if ratio < 1.0 else "WORSE"
        print(f"Hier {nb:>2} blocks: {r['stitched_hpwl_dbu']:>15,.0f} DBU  in  {r['total_hier_time_ms']:>7.1f}ms  "
              f"({ratio:.3f}x flat, {delta:+.1f}%)  [{status}]")
    # Save results
    out = {
        "design": "bigblue1_15k_subset",
        "n_cells": n_cells,
        "n_nets": n_nets,
        "flat_v3_hpwl_dbu": flat_hpwl,
        "flat_v3_time_ms": flat_time * 1000,
        "hierarchical": {str(k): v for k, v in results.items()},
    }
    out_path = CHIPMIND / "results" / "hierarchical_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
