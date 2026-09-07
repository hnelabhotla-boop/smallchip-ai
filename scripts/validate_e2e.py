"""
scripts/validate_e2e.py — End-to-end validation of SmallChip AI.

Runs the full pipeline on all 4 example chips and produces a clean
report with honest numbers. This is the test we use before any
external claim (professor email, ISEF paper, judge demo).

Usage:
    python scripts/validate_e2e.py
    python scripts/validate_e2e.py --output report.json
"""
import sys
import json
import time
import argparse
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, "/Users/harshith/Documents/RLChip_ISEF/src")

from chipmind.core.def_lef_loader import load_design
from chipmind.ml.detailed_placer import detailed_placement
from train_gat_placer_v3 import GATPlacerV3, predict
import torch


def compute_hpwl(components: dict, nets: list) -> float:
    """Compute total HPWL across all nets."""
    total = 0
    for net in nets:
        cs = net.get("components", []) if isinstance(net, dict) else net
        xs, ys = [], []
        for c in cs:
            if c in components:
                comp = components[c]
                if isinstance(comp, dict):
                    xs.append(float(comp.get("x", 0)))
                    ys.append(float(comp.get("y", 0)))
                else:
                    xs.append(float(comp[0]))
                    ys.append(float(comp[1]))
        if xs and ys:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def random_baseline_hpwl(chip, seed=42) -> float:
    """Random placement HPWL — our 'without AI' baseline."""
    import random
    random.seed(seed)
    die = chip["die"]
    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]
    comps = {
        c: {
            "x": die["x1"] + random.random() * die_w,
            "y": die["y1"] + random.random() * die_h,
        }
        for c in chip["components"]
    }
    return compute_hpwl(comps, chip["nets"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="validation_report.json")
    parser.add_argument("--examples-dir", default="/Users/harshith/Documents/ChipPlacer/web/examples")
    args = parser.parse_args()

    # Load V3
    model = GATPlacerV3()
    model.load_state_dict(torch.load(
        "/Users/harshith/Documents/RLChip_ISEF/results/gat_v3_combined_60ep/gat_v3_model_best.pt",
        map_location="cpu",
    ))
    model.eval()
    print("V3 model loaded")

    examples = ["gcd_734cells.def", "bigblue1_5k_subset.def",
                "bigblue1_8k_subset.def", "bigblue1_15k_subset.def"]

    results = []

    for fname in examples:
        print(f"\n--- {fname} ---")
        src = Path(args.examples_dir) / fname
        if not src.exists():
            print(f"  NOT FOUND: {src}")
            continue

        with tempfile.NamedTemporaryFile(suffix=".def", delete=False) as t:
            shutil.copy(src, t.name)
            tmp_path = t.name
        chip = load_design(tmp_path)
        Path(tmp_path).unlink()

        n_cells = len(chip.get("components", {}))
        n_nets = len(chip.get("nets", []))
        die = chip["die"]
        die_w_db = die["x2"] - die["x1"]
        die_h_db = die["y2"] - die["y1"]
        # Convert DBU to microns (1 DBU = 0.001 µm typically, 1000 DBU = 1µm)
        die_w_um = die_w_db / 1000
        die_h_um = die_h_db / 1000

        # Random baseline
        random_hpwl = random_baseline_hpwl(chip)

        # V3 raw
        t0 = time.time()
        v3_result = predict(model, chip)
        v3_time = (time.time() - t0) * 1000
        v3_hpwl = compute_hpwl(v3_result, chip["nets"])

        # Detailed placement
        t0 = time.time()
        detailed = detailed_placement(
            v3_result, chip["nets"], die, n_iterations=2, verbose=False,
        )
        detailed_time = (time.time() - t0) * 1000
        detailed_hpwl = compute_hpwl(detailed, chip["nets"])

        # Per-cell, per-net in microns
        # (DBU is 1/1000 of a µm in Nangate45)
        v3_per_net_um = v3_hpwl / n_nets / 1000
        detailed_per_net_um = detailed_hpwl / n_nets / 1000
        random_per_net_um = random_hpwl / n_nets / 1000

        # Improvement vs random
        v3_improvement = (random_hpwl - v3_hpwl) / random_hpwl * 100 if random_hpwl > 0 else 0
        detailed_improvement = (random_hpwl - detailed_hpwl) / random_hpwl * 100 if random_hpwl > 0 else 0
        detailed_vs_v3 = (v3_hpwl - detailed_hpwl) / v3_hpwl * 100 if v3_hpwl > 0 else 0

        result = {
            "file": fname,
            "n_cells": n_cells,
            "n_nets": n_nets,
            "die_um": {"w": round(die_w_um, 2), "h": round(die_h_um, 2)},
            "random_hpwl_per_net_um": round(random_per_net_um, 1),
            "v3_hpwl_per_net_um": round(v3_per_net_um, 1),
            "detailed_hpwl_per_net_um": round(detailed_per_net_um, 1),
            "v3_improvement_vs_random_pct": round(v3_improvement, 1),
            "detailed_improvement_vs_random_pct": round(detailed_improvement, 1),
            "detailed_improvement_vs_v3_pct": round(detailed_vs_v3, 1),
            "v3_time_ms": round(v3_time, 1),
            "detailed_time_ms": round(detailed_time, 1),
            "total_time_ms": round(v3_time + detailed_time, 1),
            "win_vs_random": v3_hpwl < random_hpwl,
            "v3_better_than_detailed": v3_hpwl < detailed_hpwl,
        }
        results.append(result)
        print(f"  Random:        {random_per_net_um:>6.1f} µm/net")
        print(f"  V3 raw:        {v3_per_net_um:>6.1f} µm/net  ({v3_time:.0f}ms)")
        print(f"  V3 + detailed: {detailed_per_net_um:>6.1f} µm/net  (+{detailed_time:.0f}ms)")
        print(f"  Improvement:   {detailed_improvement:>6.1f}% vs random")

    # Summary
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": "SmallChip AI v3 (GAT, 18K params, 60 epochs)",
        "examples_tested": len(results),
        "all_win_vs_random": all(r["win_vs_random"] for r in results),
        "per_net_hpwl_summary": {
            "min": min(r["detailed_hpwl_per_net_um"] for r in results),
            "max": max(r["detailed_hpwl_per_net_um"] for r in results),
            "monotonically_decreasing": all(
                results[i]["detailed_hpwl_per_net_um"] >= results[i+1]["detailed_hpwl_per_net_um"]
                for i in range(len(results)-1)
            ),
        },
        "results": results,
    }

    Path(args.output).write_text(json.dumps(summary, indent=2))
    print(f"\n=== Summary ===")
    print(f"Examples tested: {summary['examples_tested']}")
    print(f"All win vs random: {summary['all_win_vs_random']}")
    print(f"Per-net range: {summary['per_net_hpwl_summary']['min']}-{summary['per_net_hpwl_summary']['max']} µm")
    print(f"Monotonically decreasing: {summary['per_net_hpwl_summary']['monotonically_decreasing']}")
    print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
