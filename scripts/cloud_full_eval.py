"""
cloud_full_eval.py — Run every benchmark we have on the cloud in parallel.

Goals:
1. Verify GCD 99.7% / 370× with V3 (timing + power from OpenROAD)
2. Run 5K, 8K, 10K, 15K bigblue1 with V3 + smart legalizer
3. Re-run the 66-design held-out test on cloud
4. Run hierarchy on 5K, 10K, 15K bigblue1
5. Output all numbers as a single JSON

Uses multiprocessing to run benchmarks in parallel.
"""
import sys
import time
import json
import multiprocessing as mp
from pathlib import Path
from copy import deepcopy

REPO = Path("/root/smallchip-ai")
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/root/RLChip_ISEF/src")
import torch
from train_gat_placer_v3 import GATPlacerV3, predict
from chipmind.core.def_parser import parse_def
from chipmind.core.hpwl import compute_hpwl
from chipmind.ml.hierarchical_placer import hierarchical_placement
from chipmind.ml.legalize_v2 import snap_to_legal

V3_CKPT = REPO / "models/gat_v3_model_best.pt"
OUT = REPO / "results/cloud_full_eval.json"

DATA_DIR = REPO / "data"
DESIGNS = {
    "gcd": "gcd_nangate45.def",
    "5k": "bigblue1_5k_subset.def",
    "8k": "bigblue1_8k_subset.def",
    "10k": "bigblue1_10k_subset.def",
    "15k": "bigblue1_15k_subset.def",
}


def load_v3():
    model = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
    model.load_state_dict(torch.load(str(V3_CKPT), map_location="cpu", weights_only=True))
    model.eval()
    return model


def hpwl_dict(positions, nets):
    """Sum of per-net HPWL using dict-based positions.

    positions: dict name -> {"x": float, "y": float} or (x, y) tuple or (x, y) list
    """
    total = 0.0
    n_nets = 0
    for net in nets:
        comps = net["components"]
        if len(comps) < 2:
            continue
        xs, ys = [], []
        for c in comps:
            if c in positions:
                p = positions[c]
                if isinstance(p, dict):
                    xs.append(p["x"])
                    ys.append(p["y"])
                elif isinstance(p, (tuple, list)):
                    xs.append(p[0])
                    ys.append(p[1])
                else:
                    # numpy array
                    xs.append(float(p[0]))
                    ys.append(float(p[1]))
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
            n_nets += 1
    return total, total / max(1, n_nets)


def run_v3_on_design(name, def_path, v3):
    """Run V3 on a single design, return metrics."""
    t0 = time.time()
    try:
        chip = parse_def(str(def_path))
    except Exception as e:
        return {"name": name, "error": f"parse: {e}", "elapsed_s": time.time() - t0}

    n_cells = len(chip["components"])
    n_nets = len(chip["nets"])
    t1 = time.time()
    raw = predict(v3, chip)
    t_v3 = time.time() - t1

    # raw HPWL (before legal)
    raw_hpwl_total, raw_hpwl_per_net = hpwl_dict(raw, chip["nets"])

    # Try to legalize
    try:
        legal_pos = snap_to_legal(chip, raw)
        legal_hpwl_total, legal_hpwl_per_net = hpwl_dict(legal_pos, chip["nets"])
        leg_status = "ok"
    except Exception as e:
        legal_pos = raw
        legal_hpwl_total, legal_hpwl_per_net = raw_hpwl_total, raw_hpwl_per_net
        leg_status = f"err: {e}"

    return {
        "name": name,
        "n_cells": n_cells,
        "n_nets": n_nets,
        "v3_inference_s": t_v3,
        "raw_hpwl_dbu": raw_hpwl_total,
        "raw_per_net_dbu": raw_hpwl_per_net,
        "legal_hpwl_dbu": legal_hpwl_total,
        "legal_per_net_dbu": legal_hpwl_per_net,
        "legalize_status": leg_status,
        "elapsed_s": time.time() - t0,
    }


def run_hierarchy(name, def_path, v3, n_blocks, cells_per_block):
    t0 = time.time()
    try:
        chip = parse_def(str(def_path))
    except Exception as e:
        return {"name": name, "error": f"parse: {e}", "elapsed_s": time.time() - t0}

    n_cells = len(chip["components"])
    n_nets = len(chip["nets"])
    try:
        result = hierarchical_placement(
            chip,
            v3,
            n_blocks=n_blocks,
            cells_per_block=cells_per_block,
            top_method="force_directed",
            legal_method="snap",
            use_v3_per_block=True,
        )
        # result has: hpwl_total, hpwl_per_net, block_v3_times, total_time
        return {
            "name": name,
            "n_cells": n_cells,
            "n_nets": n_nets,
            "n_blocks": n_blocks,
            "hier_total_hpwl_dbu": result.get("total_hpwl", 0),
            "hier_per_net_dbu": result.get("hpwl_per_net", 0),
            "hier_total_time_s": result.get("total_time_s", 0),
            "block_v3_times_ms": result.get("block_v3_times_ms", []),
            "elapsed_s": time.time() - t0,
        }
    except Exception as e:
        return {"name": name, "error": f"hier: {e}", "elapsed_s": time.time() - t0}


def worker_v3(args):
    name, def_path = args
    v3 = load_v3()
    return run_v3_on_design(name, def_path, v3)


def worker_hier(args):
    name, def_path, n_blocks, cpp = args
    v3 = load_v3()
    return run_hierarchy(name, def_path, v3, n_blocks, cpp)


def main():
    print("=" * 60)
    print("  Cloud full evaluation — using all 8 cores")
    print("=" * 60)

    # Tasks
    v3_tasks = [(name, DATA_DIR / fn) for name, fn in DESIGNS.items()]
    hier_tasks = [
        ("hier_5k_3b", DATA_DIR / DESIGNS["5k"], 3, 5000),
        ("hier_10k_3b", DATA_DIR / DESIGNS["10k"], 3, 5000),
        ("hier_15k_3b", DATA_DIR / DESIGNS["15k"], 3, 5000),
    ]

    print(f"V3 tasks: {[t[0] for t in v3_tasks]}")
    print(f"Hier tasks: {[t[0] for t in hier_tasks]}")

    results = {"v3_results": [], "hier_results": []}

    # Run all in parallel
    all_tasks = [(("v3", t), t) for t in v3_tasks] + [(("hier", t), t) for t in hier_tasks]

    with mp.Pool(processes=min(8, len(all_tasks))) as pool:
        # Map v3 tasks
        print("Running V3 + hierarchy in parallel...")
        v3_results = pool.map(worker_v3, v3_tasks)
        for r in v3_results:
            print(f"  V3 {r.get('name')}: {r.get('n_cells', '?')} cells, "
                  f"raw HPWL = {r.get('raw_per_net_dbu', 0):,.0f} DBU/net, "
                  f"legal = {r.get('legal_per_net_dbu', 0):,.0f}, "
                  f"V3 time = {r.get('v3_inference_s', 0):.2f}s", flush=True)
            results["v3_results"].append(r)

        hier_results = pool.map(worker_hier, hier_tasks)
        for r in hier_results:
            print(f"  Hier {r.get('name')}: {r.get('n_blocks', '?')} blocks, "
                  f"HPWL = {r.get('hier_per_net_dbu', 0):,.0f} DBU/net, "
                  f"time = {r.get('hier_total_time_s', 0):.1f}s", flush=True)
            results["hier_results"].append(r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] {OUT}")
    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"V3 results: {len(results['v3_results'])}")
    print(f"Hier results: {len(results['hier_results'])}")
    # GCD check
    for r in results["v3_results"]:
        if r.get("name") == "gcd":
            print(f"\nGCD verification:")
            print(f"  cells: {r.get('n_cells')}")
            print(f"  raw HPWL: {r.get('raw_hpwl_dbu'):,.0f}")
            print(f"  legal HPWL: {r.get('legal_hpwl_dbu'):,.0f}")
            print(f"  expected: 10,775")


if __name__ == "__main__":
    main()
