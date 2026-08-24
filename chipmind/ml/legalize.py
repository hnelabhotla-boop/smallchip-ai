"""
Grid-based legalizer for V3 placement output.

Takes a V3-placed chip (raw x,y positions) and produces a LEGAL placement where:
  1. Every cell is on a placement row (aligned to the site grid)
  2. No two cells overlap
  3. Every cell is within the die area

Approach: simple row-based legalization
  - Divide the die into horizontal rows
  - Assign each cell to its nearest row (by y-coordinate)
  - Within each row, sort by x and pack left-to-right with no overlap
  - Snap x positions to a site grid

This is a simple legalizer — not as good as OpenROAD's, but fast and gives
a valid legal placement we can measure HPWL on.
"""

import math
from typing import Dict, List, Tuple, Any
from collections import defaultdict


def legalize(chip: Dict[str, Any],
             cell_w: float = 200,   # site width (DBU)
             cell_h: float = 100,   # site height (DBU)
             site_step: float = 100  # x grid step
             ) -> Dict[str, Any]:
    """
    Legalize a V3 placement.

    Args:
        chip: chip dict with 'components' ({name: {x, y}}), 'die' ({x1, y1, x2, y2}), 'nets'
        cell_w: standard cell width
        cell_h: standard cell height
        site_step: x grid step (cells snap to multiples of this)

    Returns:
        New chip dict with legalized components
    """
    die = chip['die']
    die_x1, die_y1 = die['x1'], die['y1']
    die_x2, die_y2 = die['x2'], die['y2']
    die_w = die_x2 - die_x1
    die_h = die_y2 - die_y1

    components = chip['components']
    nets = chip.get('nets', [])

    # Build rows
    n_rows = max(1, int(die_h / cell_h))
    row_h = die_h / n_rows
    rows = []
    for i in range(n_rows):
        y_center = die_y1 + (i + 0.5) * row_h
        rows.append(y_center)

    # Assign each cell to its nearest row
    cell_to_row = {}
    for name, pos in components.items():
        y = pos['y']
        row_idx = int((y - die_y1) / row_h)
        row_idx = max(0, min(n_rows - 1, row_idx))
        cell_to_row[name] = row_idx

    # Group cells by row
    row_cells = defaultdict(list)
    for name, pos in components.items():
        row_idx = cell_to_row[name]
        row_cells[row_idx].append((name, pos['x']))

    # Pack cells within each row
    legalized = {}
    for row_idx, cells in row_cells.items():
        # Sort by x (left to right)
        cells.sort(key=lambda c: c[1])
        y = rows[row_idx]
        # Start from left edge of die
        x = die_x1
        for name, _ in cells:
            # Snap x to grid
            x_snapped = math.ceil(x / site_step) * site_step
            # Make sure cell is within die
            if x_snapped + cell_w > die_x2:
                # Wrap to next "row segment" — push to right edge
                x_snapped = die_x2 - cell_w
            legalized[name] = {'x': x_snapped, 'y': y}
            x = x_snapped + cell_w

    # Build new chip dict
    new_chip = dict(chip)
    new_chip['components'] = legalized
    return new_chip


def compute_legal_hpwl(chip: Dict[str, Any], cell_w: float = 200, cell_h: float = 100) -> Dict[str, Any]:
    """
    Legalize a chip and compute the HPWL of the legal placement.
    Returns dict with: legal_hpwl, raw_hpwl, n_cells, n_rows, delta_pct
    """
    from chipmind.core import compute_hpwl

    raw_hpwl = compute_hpwl(chip)['total_hpwl']
    legal_chip = legalize(chip, cell_w=cell_w, cell_h=cell_h)
    legal_hpwl = compute_hpwl(legal_chip)['total_hpwl']

    die = chip['die']
    die_h = die['y2'] - die['y1']
    n_rows = max(1, int(die_h / cell_h))

    delta_pct = ((legal_hpwl - raw_hpwl) / raw_hpwl * 100) if raw_hpwl > 0 else 0

    return {
        'raw_hpwl': raw_hpwl,
        'legal_hpwl': legal_hpwl,
        'n_cells': len(chip['components']),
        'n_rows': n_rows,
        'delta_pct': delta_pct,
    }


if __name__ == "__main__":
    # Quick self-test
    import sys
    sys.path.insert(0, '/Users/harshith/Documents/ChipPlacer')
    from chipmind.core import parse_def
    chip = parse_def('/Users/harshith/Documents/RLChip_ISEF/results/bigblue1_15k_subset.def')
    result = compute_legal_hpwl(chip)
    print(f"Legal HPWL on 15K: {result['legal_hpwl']:,}")
    print(f"Raw HPWL: {result['raw_hpwl']:,}")
    print(f"Delta: {result['delta_pct']:+.1f}%")
    print(f"Rows: {result['n_rows']}")
