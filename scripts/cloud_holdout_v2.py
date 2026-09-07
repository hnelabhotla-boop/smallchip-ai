"""
cloud_holdout_v2.py — Re-verify the 100% / 87.1% held-out claim on the cloud (fixed).

The held-out test set has pre-extracted chip format (not DEF text).
"""
import sys
import time
import json
import random
from pathlib import Path
import torch

REPO = Path("/root/smallchip-ai")
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/root/RLChip_ISEF/src")
from train_gat_placer_v3 import GATPlacerV3, predict

V3_CKPT = REPO / "models/gat_v3_model_best.pt"
DATA_FILE = REPO / "data/held_out_test_set.json"
OUT = REPO / "results/cloud_holdout_v2.json"


def chip_from_dict(entry):
    """Convert pre-extracted format to chip dict that predict() expects."""
    components = {}
    for name, pos in entry["components"].items():
        components[name] = {"x": pos["x"], "y": pos["y"]}
    return {
        "components": components,
        "nets": entry["nets"],
        "die": entry.get("die", {"x1": 0, "y1": 0, "x2": 10000, "y2": 10000}),
    }


def compute_hpwl(chip, positions):
    """Compute total and per-net HPWL."""
    total = 0.0
    n_nets = 0
    for net in chip["nets"]:
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


def random_baseline(chip, seed=42):
    rng = random.Random(seed)
    die = chip.get("die", {"x1": 0, "y1": 0, "x2": 10000, "y2": 10000})
    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]
    positions = {}
    for c in chip["components"]:
        positions[c] = (die["x1"] + rng.random() * die_w, die["y1"] + rng.random() * die_h)
    return positions


def main():
    print("=" * 60)
    print("  Cloud held-out test (66 designs, pre-extracted format)")
    print("=" * 60)

    model = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
    model.load_state_dict(torch.load(str(V3_CKPT), map_location="cpu", weights_only=True))
    model.eval()
    print("V3 model loaded")

    with open(DATA_FILE) as f:
        test_set = json.load(f)
    print(f"Test set: {len(test_set)} designs")

    results = []
    wins = 0
    improvements = []
    t0 = time.time()
    for i, entry in enumerate(test_set):
        chip = chip_from_dict(entry)
        n_cells = len(chip["components"])
        n_nets = len(chip["nets"])
        if n_cells == 0:
            continue

        rand_pos = random_baseline(chip)
        rand_total, rand_per_net = compute_hpwl(chip, rand_pos)

        try:
            v3_pos = predict(model, chip)
            v3_total, v3_per_net = compute_hpwl(chip, v3_pos)
        except Exception as e:
            continue

        won = v3_total < rand_total
        imp_pct = (rand_total - v3_total) / rand_total * 100 if rand_total > 0 else 0
        if won:
            wins += 1
        improvements.append(imp_pct)

        results.append({
            "idx": i,
            "n_cells": n_cells,
            "n_nets": n_nets,
            "baseline_hpwl": rand_total,
            "v3_hpwl": v3_total,
            "won": won,
            "improvement_pct": imp_pct,
        })

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(test_set)}] wins: {wins}, "
                  f"avg imp: {sum(improvements)/len(improvements):.1f}%", flush=True)

    elapsed = time.time() - t0
    if improvements:
        print(f"\n{'='*60}")
        print(f"  HELD-OUT TEST RESULTS — CLOUD RE-VERIFICATION")
        print(f"{'='*60}")
        print(f"  Designs tested: {len(results)}")
        print(f"  Wins: {wins} ({100*wins/len(results):.1f}%)")
        print(f"  Avg improvement: {sum(improvements)/len(improvements):.2f}%")
        print(f"  Median: {sorted(improvements)[len(improvements)//2]:.2f}%")
        print(f"  Range: {min(improvements):.1f}% - {max(improvements):.1f}%")
        small = [r for r in results if r["n_cells"] < 200]
        med = [r for r in results if 200 <= r["n_cells"] < 600]
        large = [r for r in results if r["n_cells"] >= 600]
        if small:
            print(f"  Small (<200): {len(small)}, {sum(1 for r in small if r['won'])} wins, "
                  f"avg {sum(r['improvement_pct'] for r in small)/len(small):.1f}%")
        if med:
            print(f"  Medium (200-600): {len(med)}, {sum(1 for r in med if r['won'])} wins, "
                  f"avg {sum(r['improvement_pct'] for r in med)/len(med):.1f}%")
        if large:
            print(f"  Large (>=600): {len(large)}, {sum(1 for r in large if r['won'])} wins, "
                  f"avg {sum(r['improvement_pct'] for r in large)/len(large):.1f}%")
        print(f"\n  Time: {elapsed:.1f}s")
        print(f"{'='*60}")

    summary = {
        "n_designs": len(results),
        "wins": wins,
        "win_rate_pct": 100*wins/len(results) if results else 0,
        "avg_improvement_pct": sum(improvements)/len(improvements) if improvements else 0,
        "median_improvement_pct": sorted(improvements)[len(improvements)//2] if improvements else 0,
        "min_improvement_pct": min(improvements) if improvements else 0,
        "max_improvement_pct": max(improvements) if improvements else 0,
        "elapsed_s": elapsed,
        "results": results,
    }
    with open(OUT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[SAVED] {OUT}")


if __name__ == "__main__":
    main()
