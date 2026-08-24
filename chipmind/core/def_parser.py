"""
chipmind/core/def_parser.py — DEF file parser

Parses Design Exchange Format (.def) files into a chip dict.
"""

import re
from pathlib import Path
from typing import Dict, List, Any


def parse_def(def_path: str) -> dict:
    """
    Parse a .DEF file using a state machine.
    Returns dict with: die, components, nets
    """
    with open(def_path, "r") as f:
        content = f.read()

    die = None
    components = {}
    nets = []

    in_components = False
    in_nets = False
    current_net = None

    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("DIEAREA"):
            nums = re.findall(r"-?\d+", line)
            if len(nums) >= 4:
                die = {
                    "x1": int(nums[0]),
                    "y1": int(nums[1]),
                    "x2": int(nums[2]),
                    "y2": int(nums[3]),
                }

        elif re.match(r"COMPONENTS\s+\d+\s*;", line):
            in_components = True
            in_nets = False
            continue
        elif line.startswith("END COMPONENTS"):
            in_components = False
            continue

        elif re.match(r"NETS\s+\d+\s*;", line):
            in_components = False
            in_nets = True
            continue
        elif line.startswith("END NETS"):
            if current_net and len(current_net["components"]) >= 2:
                nets.append(current_net)
            current_net = None
            in_nets = False
            continue

        if in_components and line.startswith("-"):
            m = re.match(r"-\s+(\S+)\s+\S+\s+.*\+\s*PLACED\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)", line)
            if m:
                components[m.group(1)] = {"x": int(m.group(2)), "y": int(m.group(3))}
            else:
                m2 = re.match(r"-\s+(\S+)", line)
                if m2:
                    components[m2.group(1)] = {"x": 0, "y": 0}
            continue

        if in_nets and line.startswith("-"):
            if current_net and len(current_net["components"]) >= 2:
                nets.append(current_net)
            m = re.match(r"-\s+(\S+)", line)
            current_net = {"name": m.group(1) if m else "unnamed", "components": []}
            # First line of a net often has components inline: - net ( cell pin ) ( cell pin ) ...
            for cm in re.finditer(r"\(\s*(\S+)", line):
                cell_name = cm.group(1)
                if cell_name != "*":
                    current_net["components"].append(cell_name)

        elif in_nets and current_net is not None and line.startswith("("):
            # Format: ( CELL_NAME PIN_NAME ) or just ( CELL_NAME )
            m = re.match(r"\(\s*(\S+)", line)
            if m:
                cell_name = m.group(1)
                if cell_name != "*":  # skip wildcard
                    current_net["components"].append(cell_name)

    if current_net and len(current_net["components"]) >= 2:
        nets.append(current_net)

    return {
        "die": die,
        "components": components,
        "nets": nets,
    }


def write_def(chip: dict, output_path: str) -> None:
    """Write a placement as a DEF file."""
    die = chip["die"]
    components = chip["components"]
    nets = chip["nets"]

    # Try to preserve cell types from the original chip (if any)
    cell_types = chip.get("cell_types", {})

    with open(output_path, "w") as f:
        f.write("VERSION 5.8 ;\n")
        f.write("DESIGN chipmind_output ;\n")
        f.write("UNITS DISTANCE MICRONS 2000 ;\n")
        f.write(f"DIEAREA ( {die['x1']} {die['y1']} ) ( {die['x2']} {die['y2']} ) ;\n\n")
        f.write(f"COMPONENTS {len(components)} ;\n")
        for name, pos in components.items():
            cell_type = cell_types.get(name, "CELL")
            f.write(f"  - {name} {cell_type} + PLACED ( {pos['x']} {pos['y']} ) N ;\n")
        f.write("END COMPONENTS\n\n")
        # Skip SPECIALNETS — OpenROAD's strict parser doesn't accept our format
        f.write(f"NETS {len(nets)} ;\n")
        # Build set of valid cell names
        valid_cells = set(components.keys())
        for net in nets:
            net_name = net.get("name", "unnamed")
            cells = net.get("components", [])
            # Filter to only known cells (skip routing coordinates captured by parser)
            cells = [c for c in cells if c in valid_cells]
            if cells:
                cell_strs = " ".join(f"( {c} )" for c in cells)
                # OpenROAD expects USE SIGNAL at the end of each net
                f.write(f"  - {net_name} {cell_strs} + USE SIGNAL ;\n")
            else:
                f.write(f"  - {net_name} ;\n")
        f.write("END NETS\n")
        f.write("END DESIGN\n")
