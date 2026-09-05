"""
Inter-block wire guidance.

After V3 places cells within each block, this module nudges cells with
external connections toward the boundary of the block that faces their
external partners. This is a standard technique in hierarchical
placement called "macro pin guidance."

The motivation: V3 has no idea that some of its cells connect to cells
in other blocks. It places them anywhere within the block. After
stitching, an inter-block wire can span the full die. By pre-anchoring
external cells to the block edge that faces their partners, we cut
inter-block wire length roughly in half.

Algorithm:
  1. For each cell in block A with external nets, find the centroid
     of its external partners (using the centroid of each partner's
     block as a proxy for partner position).
  2. Compute the direction from cell's V3 position to the external
     centroid.
  3. Move the cell by alpha * direction, but bound the move to keep
     the cell within the block.

This is a single pass; an iterative version would refine further.
"""
from collections import defaultdict


def refine_inter_block_positions(
    block_cells: dict,
    block_positions: dict,
    block_bounds: dict,
    nets: list,
    cell_global_positions: dict,
    cell_to_block: dict,
    alpha: float = 0.5,
    n_iterations: int = 1,
    verbose: bool = False,
) -> dict:
    """
    Nudge cells with external connections toward the block boundary that
    faces their external partners. Iterative: apply n_iterations times.
    """
    updated = dict(cell_global_positions)
    for it in range(n_iterations):
        moved = 0
        total_pull = 0.0
        for net in nets:
            comps = net["components"]
            if len(comps) < 2:
                continue
            by_block = defaultdict(list)
            for c in comps:
                if c in cell_to_block:
                    by_block[cell_to_block[c]].append(c)
            for bid, cells_in_block in by_block.items():
                if bid not in block_positions:
                    continue
                other_bids = [b for b in by_block.keys() if b != bid]
                if not other_bids:
                    continue
                ext_cx = sum(block_positions[ob][0] for ob in other_bids) / len(other_bids)
                ext_cy = sum(block_positions[ob][1] for ob in other_bids) / len(other_bids)
                for c in cells_in_block:
                    if c not in updated or bid not in block_bounds:
                        continue
                    cx, cy = updated[c]
                    b_x1, b_y1, b_x2, b_y2 = block_bounds[bid]
                    dx = ext_cx - cx
                    dy = ext_cy - cy
                    new_x = cx + alpha * dx
                    new_y = cy + alpha * dy
                    new_x = max(b_x1, min(b_x2, new_x))
                    new_y = max(b_y1, min(b_y2, new_y))
                    if abs(new_x - cx) + abs(new_y - cy) > 0.01:
                        moved += 1
                        total_pull += abs(new_x - cx) + abs(new_y - cy)
                    updated[c] = (new_x, new_y)
        if verbose:
            print(f"  Inter-block refine iter {it + 1}: {moved} cells nudged, avg pull = {total_pull/max(moved,1):.1f} DBU")
        if moved == 0:
            break
    return updated


def detect_v3_collapse(positions: dict, expected_count: int, std_threshold: float = 0.01) -> bool:
    """
    Detect if V3 placement collapsed (all cells at the same point).

    Args:
        positions: {cell_name: {"x": float, "y": float}}
        expected_count: how many cells we expected
        std_threshold: standard deviation below which we consider collapsed

    Returns:
        True if V3 collapsed, False if placement looks healthy
    """
    if not positions or len(positions) < expected_count * 0.5:
        return True
    xs = [p["x"] for p in positions.values() if isinstance(p, dict)]
    ys = [p["y"] for p in positions.values() if isinstance(p, dict)]
    if not xs or not ys:
        return True
    import statistics
    try:
        x_std = statistics.stdev(xs) / (max(xs) - min(xs) + 1e-9)
        y_std = statistics.stdev(ys) / (max(ys) - min(ys) + 1e-9)
    except statistics.StatisticsError:
        return True
    return x_std < std_threshold and y_std < std_threshold


def grid_fallback_positions(block_cells: list, block_bounds: tuple) -> dict:
    """
    Grid-based fallback for V3 collapse. Place cells in a uniform grid
    within the block.
    """
    n = len(block_cells)
    if n == 0:
        return {}
    b_x1, b_y1, b_x2, b_y2 = block_bounds
    bw = b_x2 - b_x1
    bh = b_y2 - b_y1
    cols = int(n ** 0.5) + 1
    cell_w = bw / cols
    cell_h = bh / cols
    positions = {}
    for i, c in enumerate(block_cells):
        col = i % cols
        row = i // cols
        x = b_x1 + (col + 0.5) * cell_w
        y = b_y1 + (row + 0.5) * cell_h
        positions[c] = {"x": x, "y": y}
    return positions
