"""
Smart legalizer: snap V3's cells to the placement grid PRESERVING V3's ordering.

The problem with OpenROAD's legalizer: it spreads cells across the entire die,
destroying V3's tight placement. The fix: snap each cell to the nearest available
grid position IN V3'S ORDER, so the relative layout is preserved.

This is the "snap-to-legal" approach:
  1. Sort cells by V3's y (row assignment)
  2. Within each row, sort by V3's x
  3. Snap to grid: find nearest available site
  4. Skip overlapping sites
"""

import math
from collections import defaultdict
from typing import Dict, List, Any, Tuple


def snap_to_legal(chip: Dict[str, Any],
                   cell_w: float = 0.38,  # FreePDK45 site width (microns)
                   cell_h: float = 1.4,   # FreePDK45 row height (microns)
                   die_w: float = 200,
                   die_h: float = 200
                   ) -> Dict[str, Any]:
    """
    Snap V3's cells to legal grid positions, preserving their relative ordering.

    Args:
        chip: chip dict with 'components' ({name: {x, y}}), 'die', 'nets'
        cell_w: standard cell width (microns)
        cell_h: standard cell height (microns)
        die_w, die_h: die dimensions (microns)

    Returns:
        New chip dict with snapped components
    """
    components = chip['components']
    nets = chip.get('nets', [])

    # Build grid: rows are horizontal strips
    n_rows = int(die_h / cell_h)
    row_h = die_h / n_rows
    row_centers = [die_h * (i + 0.5) / n_rows for i in range(n_rows)]

    # Assign each cell to its nearest row (by y)
    cell_to_row = {}
    for name, pos in components.items():
        y = pos['y']
        # y is in 0-die_h range (from V3's scaled output)
        row_idx = int(y / row_h)
        row_idx = max(0, min(n_rows - 1, row_idx))
        cell_to_row[name] = row_idx

    # Group cells by row, sorted by x (preserving V3's left-to-right ordering)
    row_cells = defaultdict(list)
    for name, pos in components.items():
        row_idx = cell_to_row[name]
        row_cells[row_idx].append((name, pos['x']))

    for row_idx in row_cells:
        row_cells[row_idx].sort(key=lambda c: c[1])

    # Snap each cell to the nearest available site in its row
    snapped = {}
    sites_per_row = int(die_w / cell_w)  # number of sites per row

    for row_idx, cells in row_cells.items():
        y = row_centers[row_idx]
        # Track which sites are occupied in this row
        occupied = set()
        for name, v3_x in cells:
            # Find nearest available site
            desired_site = int(v3_x / cell_w)
            # Try sites in order of distance from desired
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
                best_site = 0  # fallback
            occupied.add(best_site)
            x = best_site * cell_w + cell_w / 2  # center of site
            snapped[name] = {'x': x, 'y': y}

    new_chip = dict(chip)
    new_chip['components'] = snapped
    return new_chip


def compute_snap_hpwl(chip: Dict[str, Any], cell_w: float = 0.38, cell_h: float = 1.4,
                       die_w: float = 200, die_h: float = 200) -> Dict[str, Any]:
    """Snap to legal and compute HPWL."""
    from chipmind.core import compute_hpwl
    raw_hpwl = compute_hpwl(chip)['total_hpwl']
    legal_chip = snap_to_legal(chip, cell_w=cell_w, cell_h=cell_h, die_w=die_w, die_h=die_h)
    legal_hpwl = compute_hpwl(legal_chip)['total_hpwl']
    return {
        'raw_hpwl': raw_hpwl,
        'legal_hpwl': legal_hpwl,
        'delta_pct': (legal_hpwl - raw_hpwl) / raw_hpwl * 100 if raw_hpwl > 0 else 0,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/harshith/Documents/RLChip_ISEF/src')
    sys.path.insert(0, '/Users/harshith/Documents/ChipPlacer')
    from train_gat_placer_v3 import GATPlacerV3, predict as v3_predict
    from chipmind.core import parse_def, compute_hpwl
    import torch, re

    m = GATPlacerV3(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
    state = torch.load('/Users/harshith/Documents/RLChip_ISEF/results/gat_v3_1k_40ep/gat_v3_model_best.pt', map_location='cpu', weights_only=False)
    m.load_state_dict(state)
    m.eval()

    chip = parse_def('/Users/harshith/Documents/RLChip_ISEF/results/bigblue1_15k_subset.def')
    components = v3_predict(m, chip)

    # Scale to 0-200 micron die
    die_size = 200
    xs = [p['x'] for p in components.values()]
    ys = [p['y'] for p in components.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_scale = die_size / (x_max - x_min)
    y_scale = die_size / (y_max - y_min)

    scaled = {}
    for name, p in components.items():
        scaled[name] = {'x': (p['x'] - x_min) * x_scale, 'y': (p['y'] - y_min) * y_scale}

    chip_v3 = {**chip, 'components': scaled}
    result = compute_snap_hpwl(chip_v3)
    print(f"V3 raw HPWL: {result['raw_hpwl']:,.2f} microns")
    print(f"Snapped legal HPWL: {result['legal_hpwl']:,.2f} microns")
    print(f"Delta: {result['delta_pct']:+.1f}%")
    if result['legal_hpwl'] < 1_000_000:
        print(f"TARGET MET: {result['legal_hpwl']:,.0f} < 1,000,000")
    else:
        print(f"Target: {result['legal_hpwl']:,.0f} > 1,000,000")
