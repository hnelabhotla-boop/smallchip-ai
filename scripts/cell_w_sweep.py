"""
Cell width sweep: try multiple cell widths and pick the best per design.

The detailed_scaling test showed cell_w=0.30 / 0.50 / 0.76 / 1.00 all give
different results. The best cell_w depends on the design. This script
runs the sweep for all 4 sizes and reports the best.
"""
import json
import sys
import time
from pathlib import Path

REPO = Path("/Users/harshith/Documents/RLChip_ISEF")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, "/Users/harshith/Documents/ChipPlacer")

from chipmind.core.def_parser import parse_def
from chipmind.core.hpwl import compute_hpwl
from train_gat_placer_v3 import GATPlacerV3, predict as v3_predict
from chipmind.ml.detailed_placer import detailed_placement

import torch

V3 = REPO / "results/gat_v3_combined_60ep/gat_v3_model_best.pt"
OUT_PATH = Path("/Users/harshith/Documents/ChipPlacer/results/cell_w_sweep.json")

SIZES = [
    ("5k", REPO / "results/bigblue1_5k_subset.def"),
    ("8k", REPO / "results/bigblue1_8k_subset.def"),
    ("10k", REPO / "results/bigblue1_10k_subset.def"),
    ("15k", REPO / "results/bigblue1_15k_subset.def"),
]

CELL_WIDTHS = [0.30, 0.50, 0.76, 1.00]
N_SEEDS = 3  # V3 seeds

print("Loading V3...")
ckpt = torch.load(V3, map_location="cpu", weights_only=False)
m = GATPlacerV3(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
m.load_state_dict(ckpt)
m.eval()
print(f"  loaded {sum(p.numel() for p in m.parameters()):,} params\n")

results = {"v3_model": str(V3), "runs": []}

for label, def_path in SIZES:
    print(f"\n{'='*60}\n{label.upper()}\n{'='*60}")
    parsed = parse_def(str(def_path))
    die = parsed["die"]
    n_cells = len(parsed["components"])
    n_nets = len(parsed["nets"])
    print(f"  die: {die}, cells: {n_cells}, nets: {n_nets}")

    # Run V3 with multiple seeds, pick best
    print("Running V3 with N_SEEDS seeds...")
    best_v3 = None
    best_v3_hpwl = float("inf")
    seed_results = []
    for seed in range(N_SEEDS):
        chip_copy = {
            "die": parsed["die"],
            "components": {c: dict(p) for c, p in parsed["components"].items()},
            "nets": parsed["nets"],
        }
        if seed > 0:
            import random
            rng = random.Random(seed)
            for c in chip_copy["components"]:
                chip_copy["components"][c] = {
                    "x": rng.randint(die["x1"], die["x2"]),
                    "y": rng.randint(die["y1"], die["y2"]),
                }
        v3_out = v3_predict(m, chip_copy)
        v3_hpwl = compute_hpwl({"die": die, "components": v3_out, "nets": parsed["nets"]})["total_hpwl"]
        seed_results.append({"seed": seed, "v3_hpwl": v3_hpwl})
        if v3_hpwl < best_v3_hpwl:
            best_v3_hpwl = v3_hpwl
            best_v3 = v3_out
    print(f"  Best V3 seed: HPWL = {best_v3_hpwl:,.0f} (seeds: {[r['v3_hpwl'] for r in seed_results]})")
    raw = best_v3_hpwl

    label_results = {
        "label": label,
        "n_cells": n_cells,
        "n_nets": n_nets,
        "v3_raw_hpwl_dbu": raw,
        "seed_results": seed_results,
        "cell_width_results": [],
    }

    for cw in CELL_WIDTHS:
        t0 = time.time()
        result = detailed_placement(best_v3, parsed["nets"], die, cell_w_um=cw, cell_h_um=1.4, n_iterations=3, verbose=False)
        elapsed = time.time() - t0
        hpwl = compute_hpwl({"die": die, "components": result, "nets": parsed["nets"]})["total_hpwl"]
        per_net = hpwl / n_nets
        per_cell = hpwl / n_cells
        print(f"  cell_w={cw}um: {hpwl:,.0f} DBU (per_net {per_net:.0f}, {elapsed:.1f}s)")
        label_results["cell_width_results"].append({
            "cell_w_um": cw,
            "legal_hpwl_dbu": hpwl,
            "per_net_dbu": per_net,
            "per_cell_dbu": per_cell,
            "elapsed_sec": elapsed,
        })

    best = min(label_results["cell_width_results"], key=lambda r: r["legal_hpwl_dbu"])
    label_results["best"] = best
    print(f"\n  BEST for {label}: {best['legal_hpwl_dbu']:,.0f} DBU at cell_w={best['cell_w_um']}um")
    results["runs"].append(label_results)

    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

print("\n\n" + "="*60)
print("CELL-WIDTH SWEEP SUMMARY")
print("="*60)
print(f"{'Size':<6} {'Cells':<7} {'Nets':<7} {'Raw HPWL':<15} {'Best Legal':<15} {'Per-Net':<10} {'Per-Cell':<10} {'Best cell_w':<10}")
for r in results["runs"]:
    b = r["best"]
    print(f"{r['label']:<6} {r['n_cells']:<7} {r['n_nets']:<7} {r['v3_raw_hpwl_dbu']:<15,.0f} {b['legal_hpwl_dbu']:<15,.0f} {b['per_net_dbu']:<10.0f} {b['per_cell_dbu']:<10.0f} {b['cell_w_um']:<10}um")
print(f"\nSaved to {OUT_PATH}")
