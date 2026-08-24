"""
bookshelf_reader.py — Parse ISPD 2005 Bookshelf format
Extract: cell info, netlist, reference placement, die area
Returns data in our chip dict format.

Bookshelf format:
  .aux: top-level pointer file
  .nodes: cell sizes (one cell per line)
  .nets: netlist (NetDegree: ... then pin lines)
  .pl: placement positions
  .scl: site/core row info (die area)
  .wts: weights
"""

import os
import re
from pathlib import Path


def read_nodes(path: str) -> dict:
    """Returns {cell_name: (size_x, size_y, is_terminal)}"""
    cells = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or not line.startswith("\t") and not line[0].isalpha():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            name = parts[0]
            try:
                sx, sy = int(parts[1]), int(parts[2])
            except ValueError:
                continue
            is_terminal = len(parts) > 3 and parts[3] == "terminal"
            cells[name] = (sx, sy, is_terminal)
    return cells


def read_nets(path: str) -> list:
    """Returns list of nets: [{name, cells: [cell_names]}]"""
    nets = []
    current = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("NetDegree"):
                if current is not None:
                    nets.append(current)
                parts = line.split(":")
                current = {"name": parts[-1].strip(), "cells": []}
            else:
                parts = line.split()
                if parts and current is not None:
                    current["cells"].append(parts[0])
    if current is not None:
        nets.append(current)
    return nets


def read_pl(path: str) -> dict:
    """Returns {cell_name: (x, y)} from placement file"""
    placement = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("UCLA"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            name = parts[0]
            try:
                x, y = int(parts[1]), int(parts[2])
            except ValueError:
                continue
            placement[name] = (x, y)
    return placement


def read_scl(path: str) -> dict:
    """Returns die area: {x1, y1, x2, y2}"""
    rows = []
    current_row = None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("CoreRow"):
                if current_row is not None:
                    rows.append(current_row)
                current_row = {}
            elif line.startswith("Coordinate") and current_row is not None:
                try:
                    current_row["y"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("Height") and current_row is not None:
                try:
                    current_row["h"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("SubrowOrigin") and current_row is not None:
                try:
                    current_row["x"] = int(line.split(":")[-1].split()[0])
                except (ValueError, IndexError):
                    pass
            elif line.startswith("NumSites") and current_row is not None:
                try:
                    current_row["num_sites"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
        if current_row is not None:
            rows.append(current_row)

    if not rows:
        return {"x1": 0, "y1": 0, "x2": 100000, "y2": 100000}

    # Die area: x range from subrow origin to (subrow origin + num_sites)
    # y range from min row y to (max row y + max row height)
    xs = [r.get("x", 0) for r in rows]
    ys = [r.get("y", 0) for r in rows]
    hs = [r.get("h", 1) for r in rows]
    sites = [r.get("num_sites", 10000) for r in rows]
    # X2: max of (subrow_origin + num_sites)
    x_max = max(x + s for x, s in zip(xs, sites))
    # Y2: max of (y + height)
    y_max = max(y + h for y, h in zip(ys, hs))
    return {
        "x1": min(xs) if xs else 0,
        "y1": min(ys) if ys else 0,
        "x2": x_max,
        "y2": y_max,
    }


def parse_bookshelf(benchmark_dir: str) -> dict:
    """Parse a full ISPD 2005 Bookshelf benchmark. Returns chip dict."""
    base = Path(benchmark_dir)
    name = base.name

    cells = read_nodes(base / f"{name}.nodes")
    nets = read_nets(base / f"{name}.nets")
    placement = read_pl(base / f"{name}.pl")
    die = read_scl(base / f"{name}.scl")

    return {
        "name": name,
        "cells": cells,  # {name: (size_x, size_y, is_terminal)}
        "nets": nets,
        "placement": placement,  # {name: (x, y)}
        "die": die,
    }


def subset_chip(bookshelf: dict, n_cells: int = 200, seed: int = 42) -> dict:
    """Extract a CONNECTED random subset of n_cells from a Bookshelf design.
    BFS from a random starting cell, growing the set via net connections.
    Returns a chip dict compatible with our SA and parser."""
    import random
    from collections import deque
    random.seed(seed)

    # Build cell->nets index for fast BFS
    cell_to_nets = {}
    for net in bookshelf["nets"]:
        for c in net["cells"]:
            if c in bookshelf["cells"]:
                cell_to_nets.setdefault(c, []).append(net)

    cell_names = list(bookshelf["cells"].keys())
    if len(cell_names) < n_cells:
        n_cells = len(cell_names)

    # BFS from random starting cell
    start = random.choice(cell_names)
    selected = {start}
    queue = deque([start])
    while queue and len(selected) < n_cells:
        c = queue.popleft()
        for net in cell_to_nets.get(c, []):
            for neighbor in net["cells"]:
                if neighbor in bookshelf["cells"] and neighbor not in selected and len(selected) < n_cells:
                    selected.add(neighbor)
                    queue.append(neighbor)

    # Extract nets that have at least 2 selected cells
    selected_nets = []
    for net in bookshelf["nets"]:
        net_cells = [c for c in net["cells"] if c in selected]
        if len(net_cells) >= 2:
            selected_nets.append({"name": net["name"], "components": net_cells})

    # Build components dict with placement positions
    components = {}
    for c in selected:
        if c in bookshelf["placement"]:
            x, y = bookshelf["placement"][c]
            components[c] = {"x": x, "y": y}

    return {
        "name": f"{bookshelf['name']}_sub{len(selected)}",
        "components": components,
        "nets": selected_nets,
        "die": bookshelf["die"],
    }
