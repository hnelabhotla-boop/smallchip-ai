#!/usr/bin/env python3
"""
olp_ablation.py — Ablation study for OLP.

Tests three conditions on held-out ISPD-style designs:
1. NO MOVE: random initial placement, no refinement
2. RANDOM MOVE: random initial, then 1 random drag per cell
3. OLP MOVE: random initial, then 1 OLP-suggested drag per cell

Metric: total HPWL on held-out designs. Lower is better.

If OLP MOVE < RANDOM MOVE, the model has learned something useful.
If OLP MOVE ≈ RANDOM MOVE, the model didn't learn.

This is the most important validation: does OLP actually help?
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


def random_initial(n_cells, die=1000.0, seed=42):
    rng = np.random.default_rng(seed)
    return rng.uniform(0, die, (n_cells, 2)).astype(np.float32)


def ablation_one_design(chip, model, die=1000.0, seed=42):
    """Run the 3 conditions on a single design. Return dict of HPWLs."""
    n = chip["n_cells"]
    nets = chip["nets"]
    pos0 = random_initial(n, die=die, seed=seed)
    rng = np.random.default_rng(seed * 7 + 13)

    # Extract features for all cells (using initial pos)
    net_count = np.array([sum(1 for net in nets if i in net) for i in range(n)])
    net_sizes_for_cell = [
        [len(net) for net in nets if i in net] for i in range(n)
    ]

    # Pre-compute features per cell
    features = []
    for cell_idx in range(n):
        net_sizes = net_sizes_for_cell[cell_idx]
        if not net_sizes:
            net_sizes = [3]  # default
        # K-hop neighbors (cell index distance proxy)
        neighbors = []
        for k in range(1, 3):
            for j in range(max(0, cell_idx - k * 5), min(n, cell_idx + k * 5 + 1)):
                if j != cell_idx and abs(j - cell_idx) <= k * 5:
                    neighbors.append((f"c{j}", float(pos0[j, 0]), float(pos0[j, 1])))
        # Local HPWL
        local_hpwl = 0
        for net in nets:
            if cell_idx in net:
                pts = pos0[net]
                local_hpwl += (pts[:, 0].max() - pts[:, 0].min()) + (pts[:, 1].max() - pts[:, 1].min())
        f = extract_features(
            cell_id=f"c{cell_idx}",
            cell_pos=(float(pos0[cell_idx, 0]), float(pos0[cell_idx, 1])),
            cell_info={"degree": int(net_count[cell_idx]), "drive_strength": 1, "cell_type": 0},
            neighbors=neighbors,
            nets=net_sizes,
            priority={"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
            hpwl_local=float(local_hpwl),
        )
        features.append(f)
    features = np.array(features, dtype=np.float32)

    # Condition 1: NO MOVE (just the random initial)
    hpwl_no_move = compute_hpwl(pos0, nets)

    # Condition 2: RANDOM MOVE
    pos_random = pos0.copy()
    for i in range(n):
        # Random move: small displacement in random direction
        pos_random[i] += rng.normal(0, die * 0.05, 2).astype(np.float32)
    hpwl_random = compute_hpwl(pos_random, nets)

    # Condition 3: OLP-SUGGESTED MOVE
    pos_olp = pos0.copy()
    if model.is_trained:
        preds = model.predict_batch(features)  # (N, 2)
    else:
        # Untrained: zero move
        preds = np.zeros((n, 2), dtype=np.float32)
    pos_olp = pos0 + preds
    hpwl_olp = compute_hpwl(pos_olp, nets)

    return {
        "no_move": float(hpwl_no_move),
        "random_move": float(hpwl_random),
        "olp_move": float(hpwl_olp),
        "olp_improvement_vs_random_pct": float((hpwl_random - hpwl_olp) / max(hpwl_random, 1) * 100),
        "olp_improvement_vs_no_move_pct": float((hpwl_no_move - hpwl_olp) / max(hpwl_no_move, 1) * 100),
    }


def main():
    out_path = Path("results/olp_ablation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the trained model
    model = OLPMovePredictor()
    if not model.load():
        print("Model not trained. Run POST /api/olp/bootstrap first.")
        return

    # Test on N held-out designs (different seeds from training)
    test_designs = [
        (200, "io", 1000),  # n_cells, profile, seed
        (300, "phone", 1001),
        (400, "cpu", 1002),
        (500, "mixed", 1003),
        (300, "gpu", 1004),
        (200, "mixed", 1005),
        (400, "phone", 1006),
    ]

    print("OLP Ablation Study")
    print("=" * 80)
    print(f"Model: {model.n_params} params, trained={model.is_trained}")
    print(f"Tests: {len(test_designs)} held-out designs")
    print()
    print(f"{'Design':<25} {'No move':>12} {'Random':>12} {'OLP':>12} {'OLP vs Rand':>14}")
    print("-" * 80)

    results = []
    for n_cells, profile, seed in test_designs:
        chip = build_ispd_style_design(n_cells, profile=profile, seed=seed)
        r = ablation_one_design(chip, model, die=1000.0, seed=seed)
        r["design"] = f"{n_cells}_{profile}_{seed}"
        r["n_cells"] = n_cells
        r["profile"] = profile
        results.append(r)
        print(
            f"{r['design']:<25} {r['no_move']:>12.0f} {r['random_move']:>12.0f} {r['olp_move']:>12.0f} "
            f"{r['olp_improvement_vs_random_pct']:>+13.2f}%"
        )

    # Summary
    n_olp_wins = sum(1 for r in results if r["olp_move"] < r["random_move"])
    avg_improvement = sum(r["olp_improvement_vs_random_pct"] for r in results) / len(results)
    avg_improvement_vs_no_move = sum(r["olp_improvement_vs_no_move_pct"] for r in results) / len(results)
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  OLP beats random move: {n_olp_wins}/{len(results)}")
    print(f"  Avg improvement vs random: {avg_improvement:+.2f}%")
    print(f"  Avg improvement vs no-move: {avg_improvement_vs_no_move:+.2f}%")
    if n_olp_wins >= len(results) * 0.6:
        print(f"  ✓ OLP IS EFFECTIVE: the model has learned useful move patterns")
    elif n_olp_wins >= len(results) * 0.4:
        print(f"  ~ OLP IS MARGINAL: the model has learned some patterns but not consistently")
    else:
        print(f"  ✗ OLP IS NOT EFFECTIVE: the model has not learned useful patterns")
        print(f"    (likely because bootstrap synthetic drags are too different from random-init perturbations)")

    with open(out_path, "w") as f:
        json.dump({
            "results": results,
            "summary": {
                "n_olp_wins": n_olp_wins,
                "n_total": len(results),
                "avg_improvement_vs_random_pct": avg_improvement,
                "avg_improvement_vs_no_move_pct": avg_improvement_vs_no_move,
                "model_params": model.n_params,
            },
        }, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
