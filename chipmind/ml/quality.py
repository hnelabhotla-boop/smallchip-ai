"""
Congestion and thermal estimation for chip placements.

Congestion: per-region net density. For each cell, count how many nets pass
through its vicinity. High congestion = harder to route.

Thermal: per-region power density. For each cell, estimate its power
contribution and bin into a grid. High power density = hot spots.

These are estimates, not full OpenROAD routing/thermal analysis. They give
the designer a quick "feel" for how routable and thermally-balanced the
placement is.
"""

from collections import defaultdict
from typing import Dict, List, Any, Tuple


def estimate_congestion(chip: Dict[str, Any], grid_x: int = 10, grid_y: int = 10) -> Dict:
    """
    Estimate per-region routing congestion.

    Returns a grid of congestion values (n_nets passing through each cell's region)
    plus summary stats.
    """
    die = chip['die']
    die_x1, die_y1 = die['x1'], die['y1']
    die_x2, die_y2 = die['x2'], die['y2']
    die_w = die_x2 - die_x1
    die_h = die_y2 - die_y1
    cell_w = die_w / grid_x
    cell_h = die_h / grid_y

    components = chip['components']
    nets = chip.get('nets', [])

    # For each net, compute its bounding box, mark all grid cells it passes through
    grid = defaultdict(int)
    for net in nets:
        net_cells = net.get('components', net.get('cells', []))
        xs, ys = [], []
        for c in net_cells:
            if c in components:
                xs.append(components[c]['x'])
                ys.append(components[c]['y'])
        if len(xs) < 2:
            continue
        # Bounding box
        x_lo, x_hi = min(xs), max(xs)
        y_lo, y_hi = min(ys), max(ys)
        # Mark all grid cells the bounding box passes through
        gx_lo = max(0, min(grid_x - 1, int((x_lo - die_x1) / cell_w)))
        gx_hi = max(0, min(grid_x - 1, int((x_hi - die_x1) / cell_w)))
        gy_lo = max(0, min(grid_y - 1, int((y_lo - die_y1) / cell_h)))
        gy_hi = max(0, min(grid_y - 1, int((y_hi - die_y1) / cell_h)))
        for gx in range(gx_lo, gx_hi + 1):
            for gy in range(gy_lo, gy_hi + 1):
                grid[(gx, gy)] += 1

    # Build 2D array
    grid_array = [[grid[(gx, gy)] for gx in range(grid_x)] for gy in range(grid_y)]

    values = list(grid.values())
    return {
        'grid': grid_array,
        'grid_x': grid_x,
        'grid_y': grid_y,
        'max_congestion': max(values) if values else 0,
        'avg_congestion': sum(values) / len(values) if values else 0,
        'hot_spots': sum(1 for v in values if v > (sum(values) / len(values) * 3)) if values else 0,
    }


def estimate_thermal(chip: Dict[str, Any], grid_x: int = 10, grid_y: int = 10) -> Dict:
    """
    Estimate per-region thermal (power density).

    Heuristic: each cell contributes 1.0 power unit, distributed to its grid cell.
    This is a rough estimate — real thermal analysis needs activity factors.
    """
    die = chip['die']
    die_x1, die_y1 = die['x1'], die['y1']
    die_x2, die_y2 = die['x2'], die['y2']
    die_w = die_x2 - die_x1
    die_h = die_y2 - die_y1
    cell_w = die_w / grid_x
    cell_h = die_h / grid_y

    components = chip['components']

    grid = defaultdict(float)
    for name, pos in components.items():
        gx = max(0, min(grid_x - 1, int((pos['x'] - die_x1) / cell_w)))
        gy = max(0, min(grid_y - 1, int((pos['y'] - die_y1) / cell_h)))
        grid[(gx, gy)] += 1.0  # each cell = 1 power unit

    grid_array = [[grid[(gx, gy)] for gx in range(grid_x)] for gy in range(grid_y)]

    values = list(grid.values())
    if not values:
        return {'grid': grid_array, 'max_power': 0, 'avg_power': 0, 'hot_spots': 0, 'max_avg_ratio': 0}

    max_v = max(values)
    avg_v = sum(values) / len(values)
    return {
        'grid': grid_array,
        'grid_x': grid_x,
        'grid_y': grid_y,
        'max_power': max_v,
        'avg_power': avg_v,
        'hot_spots': sum(1 for v in values if v > avg_v * 2),
        'max_avg_ratio': max_v / avg_v if avg_v > 0 else 0,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/harshith/Documents/ChipPlacer')
    from chipmind.core import parse_def
    chip = parse_def('/Users/harshith/Documents/RLChip_ISEF/results/bigblue1_15k_subset.def')
    cong = estimate_congestion(chip)
    therm = estimate_thermal(chip)
    print(f"Congestion: max={cong['max_congestion']}, avg={cong['avg_congestion']:.0f}, hot spots={cong['hot_spots']}")
    print(f"Thermal: max={therm['max_power']}, avg={therm['avg_power']:.1f}, max/avg ratio={therm['max_avg_ratio']:.2f}")
