"""
Greedy graph partitioner for hierarchical placement.

Splits a netlist into N balanced blocks while minimizing the cut (number
of nets that span multiple blocks). This is the standard k-way partitioning
problem. The result feeds the per-block V3 GAT placement.

Algorithm: BFS seed + Fiduccia-Mattheyses (FM) refinement
  1. BFS from seed cells, growing each block to its target size
  2. Compute per-cell gain (cut change if moved)
  3. Move cells with positive gain to other blocks
  4. Repeat until no positive-gain moves remain
"""
import random
from collections import defaultdict, deque
from typing import Dict, List, Set


def bfs_balanced_partition(
    cell_names: List[str],
    nets: List[dict],
    n_blocks: int,
    seed: int = 42,
    verbose: bool = False,
) -> List[Set[str]]:
    """
    BFS-based initial partitioner. Much better cut than random for chip designs.

    For each block:
      1. Pick an unassigned cell as the seed
      2. BFS outward, adding cells to this block (preferring those with
         most connections to the current block) until block is full
      3. Move to next block
    """
    rng = random.Random(seed)
    n = len(cell_names)
    target = n / n_blocks
    cell_set_global = set(cell_names)
    # Build adjacency list
    adj = defaultdict(set)
    for net in nets:
        comps = [c for c in net["components"] if c in cell_set_global]
        for i in range(len(comps)):
            for j in range(i + 1, len(comps)):
                adj[comps[i]].add(comps[j])
                adj[comps[j]].add(comps[i])
    # BFS each block
    assign = {}
    blocks = [set() for _ in range(n_blocks)]
    block_order = list(range(n_blocks))
    rng.shuffle(block_order)
    for bidx in block_order:
        # Find an unassigned cell as seed
        seed_cell = None
        for c in cell_names:
            if c not in assign:
                seed_cell = c
                break
        if seed_cell is None:
            break
        visited = {seed_cell}
        queue = deque([seed_cell])
        while queue and len(blocks[bidx]) < target:
            cur = queue.popleft()
            if cur not in cell_set_global or cur in assign:
                continue
            assign[cur] = bidx
            blocks[bidx].add(cur)
            neighbors = [(nb, len(adj[nb] & blocks[bidx])) for nb in adj[cur] if nb not in visited]
            neighbors.sort(key=lambda x: -x[1])
            for nb, _ in neighbors:
                if nb not in visited and nb not in assign:
                    visited.add(nb)
                    queue.append(nb)
        # Fill remaining target with random unassigned cells
        attempts = 0
        while len(blocks[bidx]) < target and attempts < 1000:
            for c in cell_names:
                if c not in assign:
                    assign[c] = bidx
                    blocks[bidx].add(c)
                    break
            attempts += 1
    # Final sweep: any unassigned cell goes to the smallest block
    for c in cell_names:
        if c not in assign:
            smallest = min(range(n_blocks), key=lambda b: len(blocks[b]))
            assign[c] = smallest
            blocks[smallest].add(c)
    if verbose:
        sizes = [len(b) for b in blocks]
        print(f"  BFS partition: block sizes {sizes}")
    return blocks


def greedy_fm_partition(
    cell_names: List[str],
    nets: List[dict],
    n_blocks: int,
    seed: int = 42,
    max_passes: int = 8,
    verbose: bool = False,
) -> List[Set[str]]:
    """
    Greedy FM partitioner with BFS initial assignment.
    Returns list of `n_blocks` cell sets.
    """
    rng = random.Random(seed)
    n = len(cell_names)

    # 1. BFS initial assignment
    blocks = bfs_balanced_partition(cell_names, nets, n_blocks, seed=seed, verbose=verbose)
    assign = {}
    for i, b in enumerate(blocks):
        for c in b:
            assign[c] = i

    # 2. Build per-cell net index
    cell_nets = defaultdict(list)
    for ni, net in enumerate(nets):
        comps = [c for c in net["components"] if c in assign]
        if len(comps) >= 2:
            for c in comps:
                cell_nets[c].append(ni)

    # 3. Initial cut count
    def total_cut():
        cut = 0
        for ni, net in enumerate(nets):
            comps = [c for c in net["components"] if c in assign]
            if len(comps) < 2:
                continue
            blocks_in_net = {assign[c] for c in comps}
            if len(blocks_in_net) > 1:
                cut += 1
        return cut

    initial_cut = total_cut()
    if verbose:
        print(f"  Initial cut (BFS): {initial_cut} nets (of {len(nets)})")

    # 4. FM passes
    for pass_idx in range(max_passes):
        block_size = [0] * n_blocks
        for c in cell_names:
            block_size[assign[c]] += 1

        def compute_gain(c):
            current_block = assign[c]
            gains = {}
            for target in range(n_blocks):
                if target == current_block:
                    continue
                if block_size[target] >= target * 1.3:
                    gains[target] = -9999
                    continue
                delta = 0
                for ni in cell_nets.get(c, []):
                    net = nets[ni]
                    comps = [cc for cc in net["components"] if cc in assign]
                    if len(comps) < 2:
                        continue
                    blocks_in_net = {assign[cc] for cc in comps}
                    was_cut = len(blocks_in_net) > 1
                    new_blocks = (blocks_in_net - {current_block}) | {target}
                    will_be_cut = len(new_blocks) > 1
                    if was_cut and not will_be_cut:
                        delta += 1
                    elif not was_cut and will_be_cut:
                        delta -= 1
                gains[target] = delta
            return gains

        cells_order = list(cell_names)
        rng.shuffle(cells_order)
        moves_this_pass = 0
        max_gain_seen = 0
        for c in cells_order:
            gains = compute_gain(c)
            if not gains:
                continue
            best_target = max(gains, key=gains.get)
            best_gain = gains[best_target]
            if best_gain > max_gain_seen:
                max_gain_seen = best_gain
            if best_gain > 0:
                old = assign[c]
                assign[c] = best_target
                block_size[old] -= 1
                block_size[best_target] += 1
                moves_this_pass += 1
        if verbose:
            print(f"  Pass {pass_idx + 1}: max_gain={max_gain_seen}, {moves_this_pass} moves")
        if moves_this_pass == 0:
            break

    final_cut = total_cut()
    if verbose:
        print(f"  Final cut: {final_cut} ({(1 - final_cut/max(initial_cut, 1)) * 100:.1f}% reduction)")

    blocks = [set() for _ in range(n_blocks)]
    for c, b in assign.items():
        blocks[b].add(c)
    return blocks


def cut_aware_partition(
    cell_names: List[str],
    nets: List[dict],
    n_blocks: int,
    seed: int = 42,
    verbose: bool = False,
) -> List[Set[str]]:
    """Public alias."""
    return greedy_fm_partition(cell_names, nets, n_blocks, seed=seed, verbose=verbose)
