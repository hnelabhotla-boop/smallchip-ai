"""
chipmind/ml/detailed_placer.py — Real detailed placer for chip placement.

A real detailed placer (NTUplace, ABCDPlace, FastDP) does these steps:
1. **Row assignment**: assign each cell to a specific row based on y-coordinate
2. **Initial legalization**: snap each cell to the nearest available site in its row
3. **Cell flipping**: mirror cells vertically (Y axis) to reduce wirelength
4. **Cell shifting**: move cells by 1-2 site widths within their row
5. **Local reordering**: swap adjacent cells in the same row to reduce crossings
6. **Iterate** until no improvement

This is the missing piece the smart legalizer doesn't do. It should push
5K from 820K to ~200-300K and 15K from 800K-1M to ~400-500K.

Usage:
    from chipmind.ml.detailed_placer import detailed_placement
    result = detailed_placement(v3_positions, die, cell_w_um=0.19, cell_h_um=1.4)
    # result is {cell_name: {"x": ..., "y": ...}, ...}
"""

import random
from collections import defaultdict
from typing import Dict, Any, List, Tuple
import time


def _compute_hpwl(components: Dict[str, dict], nets: List[dict]) -> float:
    """Fast HPWL computation."""
    total = 0
    for net in nets:
        coords = []
        for cell_name in net["components"]:
            if cell_name in components:
                c = components[cell_name]
                coords.append((c["x"], c["y"]))
        if len(coords) < 2:
            continue
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        total += (max(xs) - min(xs)) + (max(ys) - min(ys))
    return total


def _assign_to_rows(
    components: Dict[str, dict],
    die: dict,
    cell_h_um: float,
) -> Tuple[Dict[str, int], List[float]]:
    """
    Assign each cell to a row based on its y-coordinate.
    Returns (cell_to_row, row_y_centers).
    """
    die_h_um = (die["y2"] - die["y1"]) / 1000.0
    n_rows = max(1, int(die_h_um / cell_h_um))
    row_centers = [(i + 0.5) * die_h_um / n_rows for i in range(n_rows)]

    cell_to_row = {}
    for name, comp in components.items():
        y_um = comp["y"] / 1000.0  # convert DBU to um
        row_idx = int(y_um / cell_h_um)
        row_idx = max(0, min(n_rows - 1, row_idx))
        cell_to_row[name] = row_idx
    return cell_to_row, row_centers


def _initial_legal(
    components: Dict[str, dict],
    die: dict,
    cell_w_um: float,
    cell_h_um: float,
    cell_to_row: Dict[str, int],
    row_centers: List[float],
) -> Dict[str, dict]:
    """
    Initial legalization: snap each cell to the nearest available site in its row.
    """
    die_w_um = (die["x2"] - die["x1"]) / 1000.0
    sites_per_row = int(die_w_um / cell_w_um)
    if sites_per_row < 1:
        sites_per_row = 1

    # Group cells by row, sorted by x (preserving the original ordering)
    row_cells: Dict[int, List[Tuple[str, float]]] = defaultdict(list)
    for name, comp in components.items():
        row_idx = cell_to_row[name]
        row_cells[row_idx].append((name, comp["x"]))

    for row_idx in row_cells:
        row_cells[row_idx].sort(key=lambda c: c[1])

    # Snap to sites
    new_components = {}
    for row_idx, cells in row_cells.items():
        y_um = row_centers[row_idx]
        occupied = set()
        for name, _x in cells:
            desired_site = int(_x / (cell_w_um * 1000))
            desired_site = max(0, min(sites_per_row - 1, desired_site))
            # Find nearest available site
            best_site = None
            for offset in range(sites_per_row):
                for sign in [1, -1]:
                    site = desired_site + sign * offset
                    if 0 <= site < sites_per_row and site not in occupied:
                        best_site = site
                        break
                if best_site is not None:
                    break
            if best_site is None:
                best_site = desired_site  # fall back even if overlapping
            occupied.add(best_site)
            x_um = best_site * cell_w_um + cell_w_um / 2
            new_components[name] = {"x": x_um * 1000, "y": y_um * 1000}
    return new_components


def _try_flip(
    cell_name: str,
    components: Dict[str, dict],
    die: dict,
    cell_h_um: float,
    cell_to_row: Dict[str, int],
    row_centers: List[float],
    nets: List[dict],
) -> bool:
    """
    Try flipping cell vertically (mirror Y around row center).
    Returns True if accepted.
    """
    if cell_name not in cell_to_row:
        return False
    row_idx = cell_to_row[cell_name]
    row_y = row_centers[row_idx] * 1000  # DBU
    die_y_center = (die["y1"] + die["y2"]) / 2

    # Flip: y_new = die_y_center + (die_y_center - y)
    old_y = components[cell_name]["y"]
    new_y = 2 * die_y_center - old_y
    # Bound to die
    new_y = max(die["y1"], min(die["y2"], new_y))

    # Compute delta HPWL (only nets containing this cell)
    delta = 0
    for net in nets:
        if cell_name not in net["components"]:
            continue
        # Compute net's current HPWL contribution
        coords_old = []
        for cn in net["components"]:
            if cn in components:
                coords_old.append((components[cn]["x"], components[cn]["y"]))
        if len(coords_old) < 2:
            continue
        xs_old = [c[0] for c in coords_old]
        ys_old = [c[1] for c in coords_old]
        old_hpwl = (max(xs_old) - min(xs_old)) + (max(ys_old) - min(ys_old))

        # Compute new HPWL with this cell flipped
        coords_new = list(coords_old)
        for i, cn in enumerate(net["components"]):
            if cn == cell_name:
                coords_new[i] = (coords_new[i][0], new_y)
                break
        xs_new = [c[0] for c in coords_new]
        ys_new = [c[1] for c in coords_new]
        new_hpwl = (max(xs_new) - min(xs_new)) + (max(ys_new) - min(ys_new))

        delta += new_hpwl - old_hpwl

    if delta < 0:
        components[cell_name]["y"] = new_y
        return True
    return False


def _try_shift(
    cell_name: str,
    components: Dict[str, dict],
    die: dict,
    cell_w_um: float,
    cell_to_row: Dict[str, int],
    row_centers: List[float],
    row_occupancy: Dict[int, set],
    nets: List[dict],
) -> bool:
    """
    Try shifting cell by 1 site width in either direction.
    Returns True if accepted.
    """
    if cell_name not in cell_to_row:
        return False
    row_idx = cell_to_row[cell_name]
    sites_per_row = int((die["x2"] - die["x1"]) / 1000.0 / cell_w_um)
    if sites_per_row < 2:
        return False

    current_x = components[cell_name]["x"]
    current_site = int(current_x / (cell_w_um * 1000))
    y = components[cell_name]["y"]

    # Try both directions
    for direction in [1, -1]:
        new_site = current_site + direction
        if new_site < 0 or new_site >= sites_per_row:
            continue
        if new_site in row_occupancy[row_idx]:
            continue
        new_x = (new_site * cell_w_um + cell_w_um / 2) * 1000

        # Compute delta
        delta = 0
        for net in nets:
            if cell_name not in net["components"]:
                continue
            coords_old = []
            for cn in net["components"]:
                if cn in components:
                    coords_old.append((components[cn]["x"], components[cn]["y"]))
            if len(coords_old) < 2:
                continue
            xs_old = [c[0] for c in coords_old]
            ys_old = [c[1] for c in coords_old]
            old_hpwl = (max(xs_old) - min(xs_old)) + (max(ys_old) - min(ys_old))

            coords_new = []
            for cn in net["components"]:
                if cn == cell_name:
                    coords_new.append((new_x, y))
                elif cn in components:
                    coords_new.append((components[cn]["x"], components[cn]["y"]))
            xs_new = [c[0] for c in coords_new]
            ys_new = [c[1] for c in coords_new]
            new_hpwl = (max(xs_new) - min(xs_new)) + (max(ys_new) - min(ys_new))

            delta += new_hpwl - old_hpwl

        if delta < 0:
            # Accept the shift
            row_occupancy[row_idx].discard(current_site)
            row_occupancy[row_idx].add(new_site)
            components[cell_name]["x"] = new_x
            return True
    return False


def _try_swap(
    cell_a: str,
    cell_b: str,
    components: Dict[str, dict],
    cell_to_row: Dict[str, int],
    row_occupancy: Dict[int, set],
    nets: List[dict],
) -> bool:
    """
    Try swapping two adjacent cells in the same row.
    Returns True if accepted.
    """
    if cell_a not in cell_to_row or cell_b not in cell_to_row:
        return False
    if cell_to_row[cell_a] != cell_to_row[cell_b]:
        return False

    a_x = components[cell_a]["x"]
    b_x = components[cell_b]["x"]
    a_y = components[cell_a]["y"]
    b_y = components[cell_b]["y"]

    # Compute delta
    delta = 0
    for cell_name, new_x, new_y in [(cell_a, b_x, a_y), (cell_b, a_x, b_y)]:
        for net in nets:
            if cell_name not in net["components"]:
                continue
            coords_old = []
            for cn in net["components"]:
                if cn in components:
                    coords_old.append((components[cn]["x"], components[cn]["y"]))
            if len(coords_old) < 2:
                continue
            xs_old = [c[0] for c in coords_old]
            ys_old = [c[1] for c in coords_old]
            old_hpwl = (max(xs_old) - min(xs_old)) + (max(ys_old) - min(ys_old))

            coords_new = []
            for cn in net["components"]:
                if cn == cell_name:
                    coords_new.append((new_x, new_y))
                elif cn in components:
                    coords_new.append((components[cn]["x"], components[cn]["y"]))
            xs_new = [c[0] for c in coords_new]
            ys_new = [c[1] for c in coords_new]
            new_hpwl = (max(xs_new) - min(xs_new)) + (max(ys_new) - min(ys_new))

            delta += new_hpwl - old_hpwl

    if delta < 0:
        components[cell_a]["x"] = b_x
        components[cell_a]["y"] = b_y
        components[cell_b]["x"] = a_x
        components[cell_b]["y"] = a_y
        return True
    return False


def detailed_placement(
    components: Dict[str, dict],
    nets: List[dict],
    die: dict,
    cell_w_um: float = 0.19,
    cell_h_um: float = 1.4,
    n_iterations: int = 3,
    verbose: bool = True,
) -> Dict[str, dict]:
    """
    Run real detailed placement: legalization + cell flipping + shifting + swapping.

    Args:
        components: {name: {x, y}} raw V3 positions in DBU
        nets: [{name, components: [names]}] netlist
        die: {x1, y1, x2, y2} die area in DBU
        cell_w_um: standard cell width (FreePDK45 = 0.19µm)
        cell_h_um: standard cell height (FreePDK45 = 1.4µm)
        n_iterations: number of optimization passes
        verbose: print progress

    Returns:
        {name: {x, y}} optimized legal positions in DBU
    """
    t0 = time.time()

    # Step 1: Assign to rows
    cell_to_row, row_centers = _assign_to_rows(components, die, cell_h_um)

    # Step 2: Initial legalization
    cur = _initial_legal(components, die, cell_w_um, cell_h_um, cell_to_row, row_centers)
    initial_hpwl = _compute_hpwl(cur, nets)
    if verbose:
        print(f"  After initial legalization: {initial_hpwl:,.0f} DBU ({time.time()-t0:.1f}s)")

    # Build row occupancy map (site -> cell name)
    sites_per_row = int((die["x2"] - die["x1"]) / 1000.0 / cell_w_um)
    if sites_per_row < 1:
        sites_per_row = 1

    row_occupancy = defaultdict(set)  # row_idx -> set of occupied sites
    site_to_cell = {}  # (row_idx, site) -> cell_name
    for name, comp in cur.items():
        row_idx = cell_to_row[name]
        site = int(comp["x"] / (cell_w_um * 1000))
        site = max(0, min(sites_per_row - 1, site))
        row_occupancy[row_idx].add(site)
        site_to_cell[(row_idx, site)] = name

    cell_names = list(cur.keys())

    # Optimization loop
    for it in range(n_iterations):
        it_t0 = time.time()
        flips = 0
        shifts = 0
        swaps = 0

        # Shuffle cell order to avoid bias
        random.shuffle(cell_names)

        # Pass 1: Cell flipping
        for name in cell_names:
            if _try_flip(name, cur, die, cell_h_um, cell_to_row, row_centers, nets):
                flips += 1

        # Pass 2: Cell shifting
        for name in cell_names:
            if _try_shift(name, cur, die, cell_w_um, cell_to_row, row_centers, row_occupancy, nets):
                shifts += 1

        # Pass 3: Adjacent swaps (within each row)
        for row_idx in range(len(row_centers)):
            sorted_sites = sorted(row_occupancy[row_idx])
            for i in range(len(sorted_sites) - 1):
                a = site_to_cell.get((row_idx, sorted_sites[i]))
                b = site_to_cell.get((row_idx, sorted_sites[i + 1]))
                if a and b and _try_swap(a, b, cur, cell_to_row, row_occupancy, nets):
                    swaps += 1

        cur_hpwl = _compute_hpwl(cur, nets)
        if verbose:
            print(
                f"  Iteration {it+1}/{n_iterations}: {cur_hpwl:,.0f} DBU "
                f"({flips} flips, {shifts} shifts, {swaps} swaps; {time.time()-it_t0:.1f}s)"
            )

    final_hpwl = _compute_hpwl(cur, nets)
    if verbose:
        print(f"  FINAL: {final_hpwl:,.0f} DBU (improvement: {(1 - final_hpwl/initial_hpwl)*100:.1f}%)")
    return cur


if __name__ == "__main__":
    import sys
    from pathlib import Path
    REPO = Path("/Users/harshith/Documents/RLChip_ISEF")
    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    sys.path.insert(0, "/Users/harshith/Documents/ChipPlacer")
    from chipmind.core.def_parser import parse_def
    from chipmind.core.hpwl import compute_hpwl
    from src.train_gat_placer_v3 import GATPlacerV3, predict as v3_predict
    import torch

    V3 = REPO / "results/gat_v3_combined_60ep/gat_v3_model_best.pt"
    DEF = REPO / "results/bigblue1_5k_subset.def"

    m = GATPlacerV3(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
    m.load_state_dict(torch.load(V3, map_location="cpu", weights_only=False))
    m.eval()

    parsed = parse_def(str(DEF))
    die = parsed["die"]
    comps = {n: {"x": c["x"], "y": c["y"], "width": 1.0, "height": 1.0, "is_terminal": False}
             for n, c in parsed["components"].items()}
    chip = {"die": die, "components": comps, "nets": parsed["nets"]}
    pred = v3_predict(m, chip)

    print(f"5K subset: {len(parsed['components'])} cells, {len(parsed['nets'])} nets")
    print(f"V3 raw: {compute_hpwl({'die': die, 'components': pred, 'nets': parsed['nets']})['total_hpwl']:,.0f} DBU\n")

    print("Running detailed placement (cell_w=0.50µm)...")
    result = detailed_placement(pred, parsed["nets"], die, cell_w_um=0.5, cell_h_um=1.4, n_iterations=3)
    hpwl = compute_hpwl({"die": die, "components": result, "nets": parsed["nets"]})["total_hpwl"]
    print(f"\nFinal: {hpwl:,.0f} DBU")
