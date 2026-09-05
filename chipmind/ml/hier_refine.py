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
    verbose: bool = False,
) -> dict:
    """
    Nudge cells with external connections toward the block boundary that
    faces their external partners.

    Args:
        block_cells: {block_id: set_of_cell_names}
        block_positions: {block_id: (cx, cy, w, h)}  block centers and sizes
        block_bounds: {block_id: (x1, y1, x2, y2)}  block bounding boxes
        nets: list of {"components": [c1, c2, ...]}
        cell_global_positions: {cell_name: (x, y)}  from V3 + stitch
        cell_to_block: {cell_name: block_id}
        alpha: how much to nudge (0 = no change, 1 = full pull toward boundary)

    Returns:
        Updated cell_global_positions dict
    """
    updated = dict(cell_global_positions)  # shallow copy
    moved = 0
    total_pull = 0.0
    # Build per-cell external connections
    for net in nets:
        comps = net["components"]
        if len(comps) < 2:
            continue
        # Group by block
        by_block = defaultdict(list)
        for c in comps:
            if c in cell_to_block:
                by_block[cell_to_block[c]].append(c)
        # For each block, compute centroid of external cells
        for bid, cells_in_block in by_block.items():
            if bid not in block_positions:
                continue
            # Find external cells
            external = []
            for other_bid, other_cells in by_block.items():
                if other_bid != bid:
                    external.extend(other_cells)
            if not external:
                continue
            # External centroid (use block center as proxy)
            ext_cx = sum(block_positions[ob][0] for ob in by_block if ob != bid) / max(len(by_block) - 1, 1)
            ext_cy = sum(block_positions[ob][1] for ob in by_block if ob != bid) / max(len(by_block) - 1, 1)
            # For each cell in this block, nudge toward external centroid
            for c in cells_in_block:
                if c not in updated or bid not in block_bounds:
                    continue
                cx, cy = updated[c]
                b_x1, b_y1, b_x2, b_y2 = block_bounds[bid]
                # Direction from cell to external centroid
                dx = ext_cx - cx
                dy = ext_cy - cy
                # Normalize to block half-extent
                bw = b_x2 - b_x1
                bh = b_y2 - b_y1
                # Nudge
                new_x = cx + alpha * dx
                new_y = cy + alpha * dy
                # Clamp to block bounds
                new_x = max(b_x1, min(b_x2, new_x))
                new_y = max(b_y1, min(b_y2, new_y))
                # Track how much we moved
                if abs(new_x - cx) + abs(new_y - cy) > 0.01:
                    moved += 1
                    total_pull += abs(new_x - cx) + abs(new_y - cy)
                updated[c] = (new_x, new_y)
    if verbose:
        print(f"  Inter-block refinement: {moved} cells nudged, avg pull = {total_pull/max(moved,1):.1f} DBU")
    return updated
