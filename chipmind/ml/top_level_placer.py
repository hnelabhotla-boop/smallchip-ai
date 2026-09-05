"""
Top-level block placer: positions N blocks on the global canvas to
minimize inter-block wire length.

Takes the per-block partition (from partition.py) and a net list, then
uses force-directed relaxation to spread blocks such that blocks with
many inter-block connections are placed closer together.

This is the "top layer" of the three-layer hierarchy. The result is
block (x, y) positions on the global canvas, with bounds proportional
to cell count.
"""
import math
import random
from typing import Dict, List, Set, Tuple


def build_block_graph(
    blocks: List[Set[str]],
    nets: List[dict],
) -> Dict[int, Dict[int, int]]:
    """
    Build the block connectivity graph from a partition.
    Returns {block_id: {other_block_id: num_inter_block_nets}}.
    """
    n_blocks = len(blocks)
    cell_to_block = {}
    for bid, bset in enumerate(blocks):
        for c in bset:
            cell_to_block[c] = bid
    # Initialize weight matrix
    weights = {bid: {other: 0 for other in range(n_blocks) if other != bid}
               for bid in range(n_blocks)}
    for net in nets:
        comps = [c for c in net["components"] if c in cell_to_block]
        blocks_in_net = {cell_to_block[c] for c in comps}
        if len(blocks_in_net) < 2:
            continue
        # For each pair of blocks in this net, increment weight
        block_list = list(blocks_in_net)
        for i in range(len(block_list)):
            for j in range(i + 1, len(block_list)):
                a, b = block_list[i], block_list[j]
                if a > b:
                    a, b = b, a
                weights[a][b] = weights[a].get(b, 0) + 1
                weights[b][a] = weights[b].get(a, 0) + 1
    return weights


def force_directed_block_placement(
    blocks: List[Set[str]],
    weights: Dict[int, Dict[int, int]],
    canvas_w: float,
    canvas_h: float,
    n_iterations: int = 200,
    k_repel: float = 0.5,
    k_spring: float = 0.05,
    seed: int = 42,
    verbose: bool = False,
) -> List[Tuple[float, float, float, float]]:
    """
    Force-directed block placement.

    Each block has (x, y) position. Forces:
      - Repulsion: every pair of blocks repel each other (Coulomb-like)
      - Spring: blocks with inter-block connections attract (Hooke-like)

    Returns list of (x, y, w, h) per block, with w/h proportional to cell count.
    """
    rng = random.Random(seed)
    n = len(blocks)
    # Compute target block sizes
    total_cells = sum(len(b) for b in blocks)
    total_area = canvas_w * canvas_h * 0.85  # 15% margin
    block_areas = [len(b) / total_cells * total_area for b in blocks]
    block_sizes = [math.sqrt(a) for a in block_areas]
    # Initial positions: random in canvas
    positions = [
        (rng.uniform(block_sizes[i] / 2, canvas_w - block_sizes[i] / 2),
         rng.uniform(block_sizes[i] / 2, canvas_h - block_sizes[i] / 2))
        for i in range(n)
    ]
    # Initial wire length
    def wire_length():
        wl = 0.0
        for a in range(n):
            x1, y1 = positions[a]
            for b, w_ab in weights.get(a, {}).items():
                if b > a:
                    x2, y2 = positions[b]
                    wl += w_ab * (math.hypot(x1 - x2, y1 - y2))
        return wl
    initial_wl = wire_length()
    if verbose:
        print(f"  Initial wire length: {initial_wl:.0f}")
    # Iterative force relaxation
    for it in range(n_iterations):
        # Compute net force on each block
        forces = [(0.0, 0.0) for _ in range(n)]
        for i in range(n):
            xi, yi = positions[i]
            fx, fy = 0.0, 0.0
            # Repulsion from all other blocks
            for j in range(n):
                if j == i:
                    continue
                xj, yj = positions[j]
                dx = xi - xj
                dy = yi - yj
                dist = math.hypot(dx, dy) + 1e-3
                # Coulomb-like repulsion
                repulse = k_repel * (block_sizes[i] * block_sizes[j]) / (dist * dist)
                fx += repulse * dx / dist
                fy += repulse * dy / dist
            # Spring attraction from connected blocks
            for j, w_ij in weights.get(i, {}).items():
                xj, yj = positions[j]
                dx = xj - xi
                dy = yj - yi
                dist = math.hypot(dx, dy) + 1e-3
                attract = k_spring * w_ij
                fx += attract * dx / dist
                fy += attract * dy / dist
            forces[i] = (fx, fy)
        # Apply forces with damping
        damping = 0.5 * (1 - it / n_iterations)
        for i in range(n):
            xi, yi = positions[i]
            fx, fy = forces[i]
            new_x = xi + fx * damping
            new_y = yi + fy * damping
            new_x = max(block_sizes[i] / 2, min(canvas_w - block_sizes[i] / 2, new_x))
            new_y = max(block_sizes[i] / 2, min(canvas_h - block_sizes[i] / 2, new_y))
            positions[i] = (new_x, new_y)
    final_wl = wire_length()
    if verbose:
        improvement = (initial_wl - final_wl) / max(initial_wl, 1) * 100
        print(f"  Final wire length: {final_wl:.0f}  ({improvement:.1f}% reduction)")
    # Return (x, y, w, h) per block — use block_sizes as w/h
    return [
        (positions[i][0], positions[i][1], block_sizes[i], block_sizes[i])
        for i in range(n)
    ]


def blocks_to_grid_layout(
    block_positions: List[Tuple[float, float, float, float]],
    canvas_w: float,
    canvas_h: float,
) -> List[Dict]:
    """
    Convert force-directed (cx, cy, w, h) into bounding boxes that don't overlap.

    The positions from force_directed can overlap. We project them to
    non-overlapping grid cells based on the relative position, preserving
    the force-directed ordering.
    """
    n = len(block_positions)
    # Sort by x then y
    order = sorted(range(n), key=lambda i: (block_positions[i][0], block_positions[i][1]))
    # Lay out in a grid preserving the ordering
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    block_w = canvas_w / cols
    block_h = canvas_h / rows
    out = [None] * n
    for i, bid in enumerate(order):
        col = i % cols
        row = i // cols
        out[bid] = {
            "x1": col * block_w,
            "y1": row * block_h,
            "x2": (col + 1) * block_w,
            "y2": (row + 1) * block_h,
        }
    return out
