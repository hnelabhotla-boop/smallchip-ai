"""
cloud_v3_best.py — V3 + smart_legalize + detailed_placer on real bigblue1 designs.

This gives us the BEST possible numbers (with cell_w=2 detailed placer) to compare
with the random per-block 100M result.

Each design runs in parallel on different cores.
"""
import sys
import time
import json
import multiprocessing as mp
from pathlib import Path

REPO = Path("/root/smallchip-ai")
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/root/RLChip_ISEF/src")
import torch
from train_gat_placer_v3 import GATPlacerV3, predict
from chipmind.core.def_parser import parse_def
from chipmind.ml.legalize_v2 import snap_to_legal
from chipmind.ml.detailed_placer import detailed_placement

V3_CKPT = REPO / "models/gat_v3_model_best.pt"
OUT = REPO / "results/cloud_v3_best.json"
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


def compute_hpwl_dict(positions, nets):
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
                    xs.append(p["x"]); ys.append(p["y"])
                else:
                    xs.append(p[0]); ys.append(p[1])
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
            n_nets += 1
    return total, total / max(1, n_nets)


def positions_from_dict_to_list(positions):
    """Convert {name: (x, y)} to {name: (x, y)} (no change for tuple form)."""
    return {c: (p["x"] if isinstance(p, dict) else p[0],
                p["y"] if isinstance(p, dict) else p[1])
            for c, p in positions.items()}


def run_v3_best(name, def_path, v3, cell_w=2.0):
    """Run V3 + smart_legalize + detailed_placer on a design."""
    t0 = time.time()
    try:
        chip = parse_def(str(def_path))
    except Exception as e:
        return {"name": name, "error": f"parse: {e}", "elapsed_s": time.time() - t0}

    n_cells = len(chip["components"])
    n_nets = len(chip["nets"])
    die = chip.get("die", {"x1": 0, "y1": 0, "x2": 10000, "y2": 10000})

    # 1. V3 forward pass
    t1 = time.time()
    raw = predict(v3, chip)
    t_v3 = time.time() - t1

    # 2. Smart legalize
    t1 = time.time()
    try:
        legal = snap_to_legal(chip, raw)
        t_legal = time.time() - t1
        legal_hpwl_total, legal_hpwl_per_net = compute_hpwl_dict(legal, chip["nets"])
    except Exception as e:
        legal = raw
        t_legal = 0
        legal_hpwl_total, legal_hpwl_per_net = compute_hpwl_dict(legal, chip["nets"])

    # 3. Detailed placer (cell_w)
    t1 = time.time()
    try:
        die_w = die["x2"] - die["x1"]
        die_h = die["y2"] - die["y1"]
        # detailed_placement wants (components, nets, die)
        components = {c: {"x": p[0] if not isinstance(p, dict) else p["x"],
                          "y": p[1] if not isinstance(p, dict) else p["y"]}
                      for c, p in legal.items()}
        detailed_components = detailed_placement(
            components, chip["nets"], die, cell_w=cell_w,
        )
        # Convert back to {name: (x, y)} format
        detailed_pos = {c: (p["x"] if isinstance(p, dict) else p[0],
                             p["y"] if isinstance(p, dict) else p[1])
                        for c, p in detailed_components.items()}
        t_detail = time.time() - t1
        detail_hpwl_total, detail_hpwl_per_net = compute_hpwl_dict(detailed_pos, chip["nets"])
    except Exception as e:
        detailed_pos = legal
        t_detail = 0
        detail_hpwl_total, detail_hpwl_per_net = legal_hpwl_total, legal_hpwl_per_net
        detail_status = f"err: {e}"
    else:
        detail_status = "ok"

    return {
        "name": name,
        "n_cells": n_cells,
        "n_nets": n_nets,
        "v3_inference_s": t_v3,
        "smart_legalize_s": t_legal,
        "detailed_placement_s": t_detail,
        "raw_hpwl_per_net": compute_hpwl_dict(raw, chip["nets"])[1],
        "legal_hpwl_per_net": legal_hpwl_per_net,
        "best_hpwl_per_net": detail_hpwl_per_net,
        "best_hpwl_total": detail_hpwl_total,
        "cell_w_um": cell_w,
        "elapsed_s": time.time() - t0,
    }


def worker(args):
    name, def_path, cell_w = args
    v3 = load_v3()
    return run_v3_best(name, def_path, v3, cell_w=cell_w)


def main():
    print("=" * 60)
    print("  Cloud V3 + smart_legalize + detailed_placer (best numbers)")
    print("=" * 60)

    # Run all 5 in parallel
    tasks = [(name, DATA_DIR / fn, 2.0) for name, fn in DESIGNS.items()]

    print(f"Tasks: {[t[0] for t in tasks]}")
    print(f"Running in parallel (8 cores)...")

    with mp.Pool(processes=min(8, len(tasks))) as pool:
        results = pool.map(worker, tasks)

    for r in results:
        if "error" in r:
            print(f"  {r['name']:>8}: ERROR — {r['error']}", flush=True)
        else:
            print(f"  {r['name']:>8}: {r['n_cells']:>6} cells, "
                  f"raw={r['raw_hpwl_per_net']:>10,.0f} → "
                  f"legal={r['legal_hpwl_per_net']:>10,.0f} → "
                  f"**BEST={r['best_hpwl_per_net']:>10,.0f}** DBU/net, "
                  f"total {r['elapsed_s']:.1f}s", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"results": results}, f, indent=2)
    print(f"\n[SAVED] {OUT}")
    print("=" * 60)
    print("  GCD check (expected 10,775 with cell_w=2):")
    for r in results:
        if r.get("name") == "gcd":
            print(f"    best = {r['best_hpwl_per_net']:,.0f} per-net, "
                  f"{r['best_hpwl_total']:,.0f} total")


if __name__ == "__main__":
    main()
