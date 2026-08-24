"""
hpwl_calculator.py — Week 2 Project Foundation
Reads a .DEF chip layout file and computes the Half-Perimeter Wire Length (HPWL).
HPWL is the metric your RL agent will optimize.

Run: python src/hpwl_calculator.py <path-to-def-file>
"""

import sys
import re
from pathlib import Path


def parse_def(def_path: str) -> dict:
    """
    Parse a .DEF file using a state machine. Tracks which section
    (COMPONENTS, NETS, etc.) is currently being parsed.
    """
    with open(def_path, "r") as f:
        content = f.read()

    die = None
    components = {}
    nets = []

    # Section tracking
    in_components = False
    in_nets = False
    current_net = None

    for raw_line in content.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Section transitions
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
            # Finalize any open net
            if current_net and len(current_net["components"]) >= 2:
                nets.append(current_net)
            current_net = None
            in_nets = False
            continue

        # Parse components
        if in_components and line.startswith("-"):
            # Format: - comp_name cell_name + PLACED ( x y ) orient ;
            # Also:  - comp_name cell_name ;  (no placement, pre-placement file)
            m = re.match(r"-\s+(\S+)\s+\S+\s+.*\+\s*PLACED\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)", line)
            if m:
                components[m.group(1)] = {
                    "x": int(m.group(2)),
                    "y": int(m.group(3)),
                }
            else:
                # No PLACED — pre-placement file. Use (0,0) as placeholder.
                # Caller should randomize or pre-place before computing HPWL.
                m2 = re.match(r"-\s+(\S+)", line)
                if m2:
                    components[m2.group(1)] = {"x": 0, "y": 0}
            continue

        # Parse nets (multi-line, ends with ;)
        if in_nets and line.startswith("-"):
            # Start of a new net
            # Finalize any open net first
            if current_net and len(current_net["components"]) >= 2:
                nets.append(current_net)
            m = re.match(r"-\s+(\S+)", line)
            current_net = {"name": m.group(1) if m else "unnamed", "components": []}
            # Also extract components from the start line (some have them inline)
            for cm in re.finditer(r"\(\s*(\S+)\s+\S+\s*\)", line):
                current_net["components"].append(cm.group(1))
            continue

        if in_nets and current_net is not None:
            # Continuation of current net — extract all ( comp pin ) pairs
            for cm in re.finditer(r"\(\s*(\S+)\s+\S+\s*\)", line):
                current_net["components"].append(cm.group(1))
            # If line ends with ;, this is the last line of the net
            if line.endswith(";"):
                if len(current_net["components"]) >= 2:
                    nets.append(current_net)
                current_net = None
            continue

    return {"die": die, "components": components, "nets": nets}


def compute_hpwl(design: dict) -> dict:
    """
    Compute the total Half-Perimeter Wire Length.
    For each net: HPWL = (max_x - min_x) + (max_y - min_y) of all connected components.
    Total HPWL = sum over all nets.
    """
    components = design["components"]
    nets = design["nets"]

    total_hpwl = 0
    net_hpwls = []
    skipped = 0

    for net in nets:
        coords = []
        for comp_name in net["components"]:
            if comp_name in components:
                c = components[comp_name]
                coords.append((c["x"], c["y"]))

        if len(coords) < 2:
            skipped += 1
            continue  # single-pin net, no wirelength

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        hpwl = (max(xs) - min(xs)) + (max(ys) - min(ys))
        total_hpwl += hpwl
        net_hpwls.append((net["name"], hpwl))

    return {
        "total_hpwl": total_hpwl,
        "num_nets": len(nets),
        "num_valid_nets": len(net_hpwls),
        "skipped_single_pin": skipped,
        "num_components": len(components),
        "top_10_nets": sorted(net_hpwls, key=lambda x: -x[1])[:10],
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python hpwl_calculator.py <path-to-def-file>")
        print("Example: python hpwl_calculator.py data/benchmarks/gcd_nangate45.def")
        sys.exit(1)

    def_path = sys.argv[1]
    if not Path(def_path).exists():
        print(f"ERROR: File not found: {def_path}")
        sys.exit(1)

    print("=" * 60)
    print("  ChipMind — HPWL Calculator (Pure Python)")
    print("=" * 60)
    print(f"\nReading: {def_path}\n")

    design = parse_def(def_path)

    if design["die"]:
        d = design["die"]
        print(f"Die area: ({d['x1']}, {d['y1']}) to ({d['x2']}, {d['y2']})")
        print(
            f"Die size: {(d['x2']-d['x1'])/2000:.1f} x {(d['y2']-d['y1'])/2000:.1f} um"
            f"  (Nangate45 uses 2000 db units per um)"
        )

    print(f"Components: {len(design['components'])}")
    print(f"Nets:       {len(design['nets'])}")

    result = compute_hpwl(design)

    print("\n" + "=" * 60)
    print("  HPWL RESULTS")
    print("=" * 60)
    print(f"\nTotal HPWL:       {result['total_hpwl']:,} database units")
    print(
        f"                  = {result['total_hpwl']/2000:.1f} um"
        f"  (Nangate45: 2000 db units per um)"
    )
    print(f"Valid nets:       {result['num_valid_nets']}")
    print(f"Skipped (1-pin):  {result['skipped_single_pin']}")
    print(f"Components:       {result['num_components']}")

    if result["top_10_nets"]:
        print("\nTop 10 longest nets:")
        print(f"  {'Net name':<20} {'HPWL (db units)':>15}")
        for name, hpwl in result["top_10_nets"]:
            print(f"  {name:<20} {hpwl:>15,}")

    print("\n" + "=" * 60)
    print("  This is your BASELINE. The RL agent must beat this.")
    print("=" * 60)


if __name__ == "__main__":
    main()
