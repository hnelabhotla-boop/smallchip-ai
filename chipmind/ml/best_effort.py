"""
Best-effort placer: tries multiple strategies and returns the lowest-HPWL result.

Strategies:
  1. V3 with original cell positions (deterministic)
  2. V3 with random initial cell positions, multiple seeds (3)
  3. V3 output rotated/flipped (4 orientations)
  4. Random placement baseline (worst case, for reference)

After each V3 pass:
  - Legalize via snap_to_legal
  - Run detailed_placer (multiple passes)
  - Compute HPWL

Return the lowest-HPWL placement.

This is the maximum-quality mode, used by default in /api/place_full.
"""
import sys
import time
import random
import copy
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Make sure RLChip path is on sys.path so we can import V3
_RLCHIP = "/Users/harshith/Documents/RLChip_ISEF/src"
if _RLCHIP not in sys.path:
    sys.path.insert(0, _RLCHIP)

from train_gat_placer_v3 import predict, chip_to_data, tanh_to_die
import torch


def compute_hpwl(positions, nets) -> float:
    """Compute total HPWL given positions dict and nets list."""
    total = 0
    for net in nets:
        xs, ys = [], []
        for c in net["components"]:
            if c in positions:
                pos = positions[c]
                if isinstance(pos, dict):
                    xs.append(pos["x"]); ys.append(pos["y"])
                else:
                    xs.append(pos[0]); ys.append(pos[1])
        if len(xs) >= 2:
            total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def run_v3_with_initial_positions(model, chip_copy, seed=None) -> Dict[str, dict]:
    """Run V3 with optional randomized input positions. chip_copy is mutated and passed in."""
    if seed is not None:
        die = chip_copy["die"]
        rng = random.Random(seed)
        for c in chip_copy["components"]:
            chip_copy["components"][c] = {
                "x": rng.randint(die["x1"], die["x2"]),
                "y": rng.randint(die["y1"], die["y2"]),
            }
    return predict(model, chip_copy)


def transform_positions(positions, transform: str, die) -> Dict[str, dict]:
    """Apply a spatial transform to positions."""
    out = {}
    for cell, pos in positions.items():
        if isinstance(pos, dict):
            x, y = pos["x"], pos["y"]
        else:
            x, y = pos[0], pos[1]
        if transform == "identity":
            nx, ny = x, y
        elif transform == "rotate90":
            cx = (die["x1"] + die["x2"]) / 2
            cy = (die["y1"] + die["y2"]) / 2
            dx, dy = x - cx, y - cy
            nx = cx - dy
            ny = cy + dx
        elif transform == "rotate180":
            cx = (die["x1"] + die["x2"]) / 2
            cy = (die["y1"] + die["y2"]) / 2
            nx = 2 * cx - x
            ny = 2 * cy - y
        elif transform == "rotate270":
            cx = (die["x1"] + die["x2"]) / 2
            cy = (die["y1"] + die["y2"]) / 2
            dx, dy = x - cx, y - cy
            nx = cx + dy
            ny = cy - dx
        elif transform == "flip_h":
            nx = die["x2"] - (x - die["x1"])
            ny = y
        elif transform == "flip_v":
            nx = x
            ny = die["y2"] - (y - die["y1"])
        else:
            nx, ny = x, y
        out[cell] = {"x": nx, "y": ny}
    return out


def random_placement(chip, seed=42) -> Dict[str, dict]:
    """Truly random placement — the baseline we should beat."""
    die = chip["die"]
    rng = random.Random(seed)
    out = {}
    for c in chip["components"]:
        out[c] = {
            "x": rng.uniform(die["x1"], die["x2"]),
            "y": rng.uniform(die["y1"], die["y2"]),
        }
    return out


def best_effort_place(
    model,
    chip: dict,
    n_random_seeds: int = 3,
    include_transforms: bool = True,
    nets: List[dict] = None,
    legalizer=None,
    detailed_placer=None,
    verbose: bool = False,
) -> Tuple[Dict[str, dict], float, Dict[str, Any]]:
    """
    Try multiple placement strategies, return the lowest-HPWL result.
    Uses deep copies of the chip to avoid cross-contamination.
    """
    if nets is None:
        nets = chip.get("nets", [])
    die = chip["die"]
    metadata = {
        "strategies_tried": [],
        "results": [],
    }
    best_positions = None
    best_hpwl = float("inf")

    def score_candidate(label, positions, chip_template):
        """Legalize + detailed + HPWL. Returns (hpwl, refined_positions)."""
        try:
            # Build a working chip with these positions
            work_chip = copy.deepcopy(chip_template)
            work_chip["components"] = copy.deepcopy(positions)
            if legalizer is not None:
                work_chip = legalizer(work_chip)
            if detailed_placer is not None:
                # detailed_placement signature: (components, nets, die, ...)
                positions = detailed_placer(work_chip["components"], nets, work_chip["die"])
            else:
                positions = work_chip["components"]
            hpwl = compute_hpwl(positions, nets)
            return hpwl, positions
        except Exception as e:
            if verbose:
                print(f"  {label} failed: {e}")
            return float("inf"), positions

    # 1. Random baseline (uses a copy of chip to avoid mutating caller's chip)
    chip_copy = copy.deepcopy(chip)
    rnd = random_placement(chip_copy, seed=42)
    hpwl, rnd_refined = score_candidate("random", rnd, copy.deepcopy(chip))
    if hpwl < best_hpwl:
        best_hpwl = hpwl; best_positions = rnd_refined
    metadata["strategies_tried"].append("random")
    metadata["results"].append({"label": "random", "hpwl": hpwl})
    if verbose:
        print(f"  random: HPWL = {hpwl:,.0f}")

    # 2. V3 deterministic
    chip_copy = copy.deepcopy(chip)
    try:
        v3_det = predict(model, chip_copy)
        hpwl, refined = score_candidate("v3_det", v3_det, copy.deepcopy(chip))
        if hpwl < best_hpwl:
            best_hpwl = hpwl; best_positions = refined
        metadata["strategies_tried"].append("v3_det")
        metadata["results"].append({"label": "v3_det", "hpwl": hpwl})
        if verbose:
            print(f"  v3_det: HPWL = {hpwl:,.0f} {' <-- new best' if hpwl == best_hpwl else ''}")
    except Exception as e:
        if verbose:
            print(f"  v3_det failed: {e}")

    # 3. V3 with random initial positions, multiple seeds
    for seed in range(n_random_seeds):
        chip_copy = copy.deepcopy(chip)
        try:
            v3_rnd = run_v3_with_initial_positions(model, chip_copy, seed=seed)
            hpwl, refined = score_candidate(f"v3_seed{seed}", v3_rnd, copy.deepcopy(chip))
            if hpwl < best_hpwl:
                best_hpwl = hpwl; best_positions = refined
            metadata["strategies_tried"].append(f"v3_seed{seed}")
            metadata["results"].append({"label": f"v3_seed{seed}", "hpwl": hpwl})
            if verbose:
                print(f"  v3_seed{seed}: HPWL = {hpwl:,.0f} {' <-- new best' if hpwl == best_hpwl else ''}")
        except Exception as e:
            if verbose:
                print(f"  v3_seed{seed} failed: {e}")

    # 4. Test-time augmentation: rotate/flip the BEST positions and re-detailed-place
    if include_transforms and best_positions is not None:
        for transform in ["rotate90", "rotate180", "rotate270", "flip_h", "flip_v"]:
            try:
                transformed = transform_positions(best_positions, transform, die)
                hpwl, refined = score_candidate(f"best_{transform}", transformed, copy.deepcopy(chip))
                if hpwl < best_hpwl:
                    best_hpwl = hpwl; best_positions = refined
                metadata["strategies_tried"].append(f"best_{transform}")
                metadata["results"].append({"label": f"best_{transform}", "hpwl": hpwl})
                if verbose:
                    print(f"  best_{transform}: HPWL = {hpwl:,.0f} {' <-- new best' if hpwl == best_hpwl else ''}")
            except Exception as e:
                if verbose:
                    print(f"  best_{transform} failed: {e}")

    metadata["best_hpwl"] = best_hpwl
    if metadata["results"]:
        best_label = next((r["label"] for r in metadata["results"] if r["hpwl"] == best_hpwl), None)
        metadata["best_strategy"] = best_label
    return best_positions, best_hpwl, metadata
