#!/usr/bin/env python3
"""
olp_iterative_ablation.py — Test OLP over multiple iterations.

The single-move ablation showed +0.60% improvement. That's because
real improvement needs many small moves. This test applies OLP N times
and measures if it compounds.

Test conditions:
- 0 iters: random initial
- 5 iters random: 5 random small moves per cell
- 5 iters OLP: 5 OLP-suggested moves per cell, with features re-extracted each iter
- 10 iters OLP: 10 OLP-suggested moves
- 20 iters OLP: 20 OLP-suggested moves

If OLP compounds, the gap between "N iters random" and "N iters OLP"
should grow with N.
"""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from chipmind.olp.olp_model import OLPMovePredictor, extract_features
from chipmind.olp.olp_bootstrap import build_ispd_style_design


def compute_hpwl(positions, nets):
    total = 0.0
    for net in nets:
        if len(net) < 2:
            continue
        pts = positions[net]
        x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
        y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
        total += (x_max - x_min) + (y_max - y_min)
    return total


def extract_features_for_pos(cell_idx, pos, nets, n_cells, net_count, net_sizes_for_cell):
    """Extract features using CURRENT positions (so we can iterate)."""
    net_sizes = net_sizes_for_cell[cell_idx]
    if not net_sizes:
        net_sizes = [3]
    # K-hop neighbors by cell index distance (cheap approximation)
    neighbors = []
    for k in range(1, 3):
        for j in range(max(0, cell_idx - k * 5), min(n_cells, cell_idx + k * 5 + 1)):
            if j != cell_idx and abs(j - cell_idx) <= k * 5:
                neighbors.append((f"c{j}", float(pos[j, 0]), float(pos[j, 1])))
    local_hpwl = 0
    for net in nets:
        if cell_idx in net:
            pts = pos[net]
            local_hpwl += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
    f = extract_features(
        cell_id=f"c{cell_idx}",
        cell_pos=(float(pos[cell_idx, 0]), float(pos[cell_idx, 1])),
        cell_info={"degree": int(net_count[cell_idx]), "drive_strength": 1, "cell_type": 0},
        neighbors=neighbors,
        nets=net_sizes,
        priority={"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
        hpwl_local=float(local_hpwl),
    )
    return f


def iterative_test(chip, model, n_iters_list, die=1000.0, seed=42, move_scale=2.0):
    """Run iterative refinement with OLP and random for each n_iters.

    move_scale: max move per iter as fraction of die (default 2% = 20 units on 1000-unit die).
    This caps each move to prevent the explosion seen with uncapped predictions.
    """
    n = chip["n_cells"]
    nets = chip["nets"]
    rng = np.random.default_rng(seed)

    pos0 = rng.uniform(0, die, (n, 2)).astype(np.float32)

    net_count = np.array([sum(1 for net in nets if i in net) for i in range(n)])
    net_sizes_for_cell = [
        [len(net) for net in nets if i in net] for i in range(n)
    ]

    results = {"iters": n_iters_list, "olp": [], "random": []}

    for n_iters in n_iters_list:
        # OLP iterative with capped moves
        pos_olp = pos0.copy()
        for it in range(n_iters):
            features = np.array([
                extract_features_for_pos(i, pos_olp, nets, n, net_count, net_sizes_for_cell)
                for i in range(n)
            ], dtype=np.float32)
            if model.is_trained:
                preds = model.predict_batch(features)  # (N, 2)
                # Cap each predicted move to ±move_scale% of die
                cap = die * move_scale / 100.0
                preds = np.clip(preds, -cap, cap)
                pos_olp = pos_olp + preds
            else:
                break
        hpwl_olp = compute_hpwl(pos_olp, nets)
        results["olp"].append(float(hpwl_olp))

        # Random iterative with same move cap
        pos_rand = pos0.copy()
        for it in range(n_iters):
            for i in range(n):
                pos_rand[i] += rng.normal(0, die * move_scale / 100.0, 2).astype(np.float32)
        hpwl_rand = compute_hpwl(pos_rand, nets)
        results["random"].append(float(hpwl_rand))

    results["no_move"] = float(compute_hpwl(pos0, nets))
    return results


def main():
    out_path = Path("results/olp_iterative_ablation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    model = OLPMovePredictor()
    if not model.load():
        print("Model not trained. Run POST /api/olp/bootstrap first.")
        return

    test_designs = [
        (200, "io", 2000),
        (300, "phone", 2001),
        (400, "mixed", 2002),
    ]
    n_iters_list = [0, 5, 10, 20]

    print("OLP Iterative Ablation — does it compound?")
    print("=" * 80)
    print(f"Model: {model.n_params} params, trained={model.is_trained}")
    print(f"Tests: {len(test_designs)} designs × {len(n_iters_list)} iteration counts")
    print()

    all_results = []
    for n_cells, profile, seed in test_designs:
        chip = build_ispd_style_design(n_cells, profile=profile, seed=seed)
        r = iterative_test(chip, model, n_iters_list, die=1000.0, seed=seed)
        r["design"] = f"{n_cells}_{profile}_{seed}"
        r["n_cells"] = n_cells
        all_results.append(r)
        # Print
        print(f"\n{r['design']}:")
        print(f"  iters:    {n_iters_list}")
        print(f"  OLP:      {[f'{x:.0f}' for x in r['olp']]}")
        print(f"  Random:   {[f'{x:.0f}' for x in r['random']]}")
        # Compute gap
        gaps = [(rand - olp) / rand * 100 for olp, rand in zip(r["olp"], r["random"])]
        print(f"  Gap:      {[f'{g:+.2f}%' for g in gaps]}")

    # Summary: does OLP compound?
    print("\n" + "=" * 80)
    print("COMPOUNDING ANALYSIS")
    print("=" * 80)
    for i, n_iters in enumerate(n_iters_list):
        gaps = [
            (r["random"][i] - r["olp"][i]) / max(r["random"][i], 1) * 100
            for r in all_results
        ]
        avg_gap = sum(gaps) / len(gaps)
        print(f"  {n_iters:>3} iters: avg OLP-vs-random gap = {avg_gap:+.2f}%")

    # Verdict
    gap_0 = 0.0
    gap_20 = sum(
        (r["random"][-1] - r["olp"][-1]) / max(r["random"][-1], 1) * 100
        for r in all_results
    ) / len(all_results)
    if gap_20 > gap_0 + 1.0:
        verdict = "✓ OLP COMPOUNDS: gap grows with iterations"
    elif gap_20 > 0:
        verdict = "~ OLP HELPS MARGINALLY: gap is small but positive"
    else:
        verdict = "✗ OLP DOES NOT COMPOUND"
    print(f"\n  {verdict}")

    with open(out_path, "w") as f:
        json.dump({
            "results": all_results,
            "n_iters_list": n_iters_list,
            "verdict": verdict,
            "model_params": model.n_params,
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
