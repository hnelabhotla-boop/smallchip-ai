#!/usr/bin/env python3
"""
headtohead_ispd2005.py — Real benchmark on OpenROAD-flow designs (gcd, jpeg, aes, ibex).

Runs the SmallChip AI spectral + Adam + multi-start pipeline on the same netlists
that the OpenROAD flow uses. Compares our per-net HPWL to OpenROAD's published
number for the same design.

This is the most honest benchmark we can run without DREAMPlace/RePlAce installed.
OpenROAD is the only industry tool we can run on this machine.

Usage:
    python scripts/headtohead_ispd2005.py --out results/headtohead_ispd2005.json

Outputs a JSON with per-design: cell count, net count, our HPWL, our per-net,
OpenROAD's published HPWL (from OpenROAD-flow-scripts), and improvement ratio.
"""

import json
import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Synthesize the OpenROAD designs to gate-level and extract cell counts
# ---------------------------------------------------------------------------

OPENROAD_DESIGNS_DIR = Path("/tmp/orfs_tmp/flow/designs/sky130hd")
OPENROAD_FLOW_SCRIPT = Path("/tmp/orfs_tmp/flow/flow.tcl")

DESIGNS_TO_TEST = ["gcd", "aes", "ibex", "jpeg", "riscv32i"]


def synthesize_design(design_name: str) -> dict:
    """Run OpenROAD-flow-scripts synthesis + global placement on a design.

    Returns dict with {n_cells, n_nets, openroad_hpwl, runtime_s}.
    """
    design_dir = OPENROAD_DESIGNS_DIR / design_name
    if not design_dir.exists():
        return {"error": f"design dir not found: {design_dir}"}

    log_file = Path(f"/tmp/headtohead_{design_name}.log")
    results_dir = Path(f"/tmp/headtohead_{design_name}_results")
    results_dir.mkdir(exist_ok=True)

    # Synthesize + place using OpenROAD flow
    cmd = [
        "bash", "-c",
        f"cd {results_dir} && "
        f"{OPENROAD_FLOW_SCRIPT} -design {design_name} "
        f"-platform /tmp/orfs_tmp/flow/platforms/sky130hd "
        f"-to 3_place 2>&1 | tee {log_file}"
    ]
    print(f"[{design_name}] running: {cmd[2][:200]}")
    t0 = time.time()
    try:
        result = subprocess.run(cmd, timeout=1800, capture_output=True, text=True)
        runtime = time.time() - t0
    except subprocess.TimeoutExpired:
        return {"error": "OpenROAD timeout (30 min)", "runtime_s": 1800}
    except Exception as e:
        return {"error": f"OpenROAD failed: {e}"}

    # Parse the final DEF to get cell count
    def_file = results_dir / "results" / "sky130hd" / design_name / "base" / "3_place.def"
    if not def_file.exists():
        return {"error": f"DEF not found: {def_file}", "runtime_s": runtime}

    with open(def_file) as f:
        def_content = f.read()
    n_cells = def_content.count("COMPONENTS")
    n_components = 0
    for line in def_content.split("\n"):
        if line.strip().startswith("-") and "MACRO" not in line:
            n_components += 1
    # Parse the OpenROAD log for HPWL
    hpwl_dbu = None
    try:
        with open(log_file) as f:
            log_content = f.read()
        # OpenROAD log format: "Final HPWL: <number>" or "[INFO GPL-0101] Final placement HPWL: <number>"
        import re
        m = re.search(r"Final placement HPWL:\s+([\d.]+)", log_content)
        if not m:
            m = re.search(r"Final HPWL:\s+([\d.]+)", log_content)
        if m:
            hpwl_dbu = float(m.group(1))
    except Exception as e:
        print(f"  WARN: couldn't parse HPWL: {e}")

    return {
        "n_components": n_components,
        "openroad_hpwl_dbu": hpwl_dbu,
        "openroad_runtime_s": runtime,
        "def_path": str(def_file),
    }


# ---------------------------------------------------------------------------
# 2. Run SmallChip AI on the same DEF
# ---------------------------------------------------------------------------

def run_smallchip_on_def(def_path: str) -> dict:
    """Run SmallChip AI's spectral + Adam + multi-start pipeline on a DEF.

    Returns dict with {n_cells, n_nets, our_hpwl, our_per_net, runtime_s}.
    """
    # Add the repo root to sys.path
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))
    try:
        from scripts.placement_100m_demo import spectral_adam_placement
    except ImportError as e:
        return {"error": f"can't import spectral placer: {e}"}

    # Parse the DEF
    from chipmind.lef_def_parser import parse_def
    try:
        netlist = parse_def(def_path)
    except Exception as e:
        return {"error": f"DEF parse failed: {e}"}

    n_cells = len(netlist.cells)
    n_nets = len(netlist.nets)

    # Cap to 100K for memory; for larger we need hierarchical
    if n_cells > 100_000:
        return {
            "n_cells": n_cells,
            "n_nets": n_nets,
            "skipped": "above 100K — use cloud for hierarchical"
        }

    t0 = time.time()
    try:
        # Use the spectral+Adam pipeline (no learned model — fully held-out)
        positions, hpwl = spectral_adam_placement(
            netlist, n_starts=5, adam_iters=200, verbose=False
        )
        runtime = time.time() - t0
        return {
            "n_cells": n_cells,
            "n_nets": n_nets,
            "our_hpwl_dbu": hpwl,
            "our_per_net_dbu": hpwl / max(n_nets, 1),
            "our_runtime_s": runtime,
        }
    except Exception as e:
        return {"error": f"spectral+Adam failed: {e}", "n_cells": n_cells, "n_nets": n_nets}


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/headtohead_ispd2005.json")
    parser.add_argument("--designs", nargs="+", default=DESIGNS_TO_TEST)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results = {}
    for design in args.designs:
        print(f"\n=== {design} ===")
        print(f"--- Step 1: Run OpenROAD on {design} ---")
        or_result = synthesize_design(design)
        if "error" in or_result:
            print(f"  OpenROAD error: {or_result['error']}")
            results[design] = {"openroad": or_result, "smallchip": {"skipped": "OpenROAD failed"}}
            continue
        print(f"  OpenROAD: {or_result.get('n_components')} cells, HPWL={or_result.get('openroad_hpwl_dbu')}")

        print(f"--- Step 2: Run SmallChip AI on {design} ---")
        sc_result = run_smallchip_on_def(or_result["def_path"])
        if "error" in sc_result:
            print(f"  SmallChip error: {sc_result['error']}")
        else:
            print(f"  SmallChip: {sc_result.get('n_cells')} cells, HPWL={sc_result.get('our_hpwl_dbu'):.0f}")

        results[design] = {"openroad": or_result, "smallchip": sc_result}

        # Compute improvement ratio
        if (
            "openroad_hpwl_dbu" in or_result
            and or_result["openroad_hpwl_dbu"]
            and "our_hpwl_dbu" in sc_result
            and sc_result.get("our_hpwl_dbu", 0) > 0
        ):
            ratio = or_result["openroad_hpwl_dbu"] / sc_result["our_hpwl_dbu"]
            results[design]["our_improvement_ratio"] = ratio
            results[design]["our_improvement_pct"] = (1 - 1 / ratio) * 100
            print(f"  Our HPWL is {ratio:.2f}× {'better' if ratio > 1 else 'worse'} than OpenROAD")

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
