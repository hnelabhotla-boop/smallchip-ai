"""
eval_v4_5k.py — Load V4 (GATv2 12-feature) and evaluate HPWL on the 5K subset.
Compare to V3 baseline (243,545 DBU at cell_w=6+ plateau; 355,545 at cell_w=2.0).

Inputs: results/gat_v4_model_best.pt (just downloaded from cloud)
        data/benchmarks/bigblue1_5k_subset.def
Outputs: results/v4_eval_5k.json
"""
import sys
import json
import time
from pathlib import Path

import torch
from torch_geometric.data import Data

# V4 trainer module
SRC = Path("/Users/harshith/Documents/RLChip_ISEF/src")
sys.path.insert(0, str(SRC))
sys.path.insert(0, "/Users/harshith/Documents/ChipPlacer")

from train_gat_placer_v4_rebalanced import (
    GATPlacerV4, chip_to_data_v4, tanh_to_die
)
from chipmind.core.def_parser import parse_def
from chipmind.ml.detailed_placer import detailed_placement  # noqa

MODEL_PATH = "/Users/harshith/Documents/ChipPlacer/results/gat_v4_model_best.pt"
DEF_5K = "/Users/harshith/Documents/ChipPlacer/web/examples/bigblue1_5k_subset.def"


def die_to_chip(die_w, die_h):
    return {"x1": 0, "y1": 0, "x2": die_w, "y2": die_h}


def chip_to_v4_input(chip):
    """Convert a chip dict (DEF/LEF style) to V4 input."""
    # chip_to_data_v4 returns (x, edge_index, y, indexed_nets, die, name_to_idx)
    return chip_to_data_v4(chip, randomize_input=False)


def predict_v4(model, chip, cell_w_um=2.0):
    """Run V4 forward + detailed_placer. Returns HPWL (DBU)."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    die_w_dbu = die["x2"] - die["x1"]
    die_h_dbu = die["y2"] - die["y1"]

    # Build V4 input
    x, edge_index, y, indexed_nets, _, name_to_idx = chip_to_v4_input(chip)
    data = Data(x=x, edge_index=edge_index)
    model.eval()
    with torch.no_grad():
        tanh_pos = model(data)  # [N, 2] in [-1, 1]
    pos_dbu = tanh_to_die(tanh_pos, die)  # [N, 2] in DBU
    positions_dbu = pos_dbu.cpu().numpy()

    # Build components dict for detailed_placer
    cell_names = list(components.keys())
    components_d = {}
    for i, name in enumerate(cell_names):
        components_d[name] = {"x": float(positions_dbu[i, 0]), "y": float(positions_dbu[i, 1])}

    # Detailed placement (legalize + greedy swap/shift)
    detailed = detailed_placement(
        components_d,
        nets,
        die,
        cell_w_um=cell_w_um,
        cell_h_um=cell_w_um,
        n_iterations=2,
        verbose=False,
    )

    # Compute HPWL on detailed result
    hpwl_total = 0
    n_nets_counted = 0
    for net in nets:
        xs, ys = [], []
        for cname in net["components"]:
            if cname in detailed:
                xs.append(detailed[cname]["x"])
                ys.append(detailed[cname]["y"])
        if len(xs) >= 2:
            hpwl_total += (max(xs) - min(xs)) + (max(ys) - min(ys))
            n_nets_counted += 1
    return hpwl_total, hpwl_total / max(1, n_nets_counted)


def main():
    print("=" * 60)
    print("V4 eval on 5K subset")
    print("=" * 60)

    # Load design (DEF only — no LEF needed)
    design = parse_def(DEF_5K)
    print(f"Loaded: {len(design['components'])} cells, {len(design['nets'])} nets, "
          f"die {design['die']['x2']-design['die']['x1']} x {design['die']['y2']-design['die']['y1']} DBU")

    # Load V4
    ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    print(f"Loaded V4 ckpt: keys={list(ckpt.keys())[:5]}")
    # Inspect args to confirm arch
    if "args" in ckpt:
        a = ckpt["args"]
        print(f"  arch: hidden={a.get('hidden')} num_layers={a.get('num_layers')} heads={a.get('heads')}")
    hidden = ckpt.get("args", {}).get("hidden", 96)
    num_layers = ckpt.get("args", {}).get("num_layers", 3)
    heads = ckpt.get("args", {}).get("heads", 4)
    model = GATPlacerV4(in_dim=12, hidden=hidden, out_dim=2, num_layers=num_layers, heads=heads, dropout=0.0)
    model.load_state_dict(ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"V4 model: {n_params:,} params")

    # Run at multiple cell_w values
    results = {}
    for cell_w_um in [1.0, 2.0, 3.0, 4.0, 6.0]:
        t0 = time.time()
        total_hpwl, per_net_hpwl = predict_v4(model, design, cell_w_um=cell_w_um)
        dt = time.time() - t0
        results[f"cell_w_{cell_w_um}um"] = {
            "total_hpwl_dbu": int(total_hpwl),
            "per_net_hpwl_dbu": float(per_net_hpwl),
            "per_net_hpwl_um": float(per_net_hpwl) / 1000.0,
            "wall_s": round(dt, 2),
        }
        print(f"  cell_w={cell_w_um}µm → {per_net_hpwl:.1f} DBU/net ({per_net_hpwl/1000:.2f} µm/net) | {dt:.1f}s")

    # Save
    out = {
        "model": "V4 (GATv2 rebalanced, 12-feat, 96 hidden, 3 layers, 4 heads, 72K params)",
        "design": "5K subset of bigblue1",
        "n_cells": len(design["components"]),
        "n_nets": len(design["nets"]),
        "results_by_cell_w": results,
        "v3_baseline_for_comparison": {
            "cell_w_2.0um": "243,545 DBU/net (plateau)",
            "cell_w_6.0um+": "243,545 DBU/net",
        },
    }
    out_path = "/Users/harshith/Documents/ChipPlacer/results/v4_eval_5k.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
