"""
chipmind/core/lef_parser.py — LEF (Library Exchange Format) parser

Parses .lef files into a chip-library dict with:
  - macros: {name: {width, height, class, pins: [{name, direction, rects}]}}
  - sites: {name: {width, height, class}}
  - layers: {name: {type, direction, pitch, width}}
  - units: {database_microns, ...}
  - manufacturing_grid: float

This is the format used by ISPD 2015/2017/2018 contest benchmarks and is the
standard industry cell library format. Reading LEF unlocks:
  - Real per-cell widths (replaces the `cell_w` parameter in the smart legalizer)
  - Per-cell pin positions (for proper detailed placement)
  - Standard cell site dimensions (for row snapping)

LEF is a state-machine language similar to DEF but with library semantics.
We do a single-pass parser with section tracking (VERSION, SITE, MACRO, etc.).
"""

import re
from pathlib import Path
from typing import Dict, List, Any


def parse_lef(lef_path: str) -> dict:
    """
    Parse a .LEF file using a single-pass state machine.

    Returns dict with: version, units, sites, layers, macros, manufacturing_grid
    """
    with open(lef_path, "r") as f:
        content = f.read()

    result = {
        "version": None,
        "units": {},
        "manufacturing_grid": None,
        "sites": {},          # {name: {width, height, class}}
        "layers": {},         # {name: {type, direction, pitch, width, ...}}
        "macros": {},         # {name: {width, height, class, origin, pins, ...}}
    }

    # First, parse simple top-level scalars
    m = re.search(r"VERSION\s+(\S+)\s*;", content)
    if m:
        result["version"] = m.group(1)

    m = re.search(r"MANUFACTURINGGRID\s+(\S+)\s*;", content)
    if m:
        result["manufacturing_grid"] = float(m.group(1))

    # Parse UNITS block
    units_match = re.search(
        r"UNITS\s+(.*?)END\s+UNITS", content, re.DOTALL
    )
    if units_match:
        units_block = units_match.group(1)
        m = re.search(r"DATABASE\s+(\S+)\s+(\d+)\s*;", units_block)
        if m:
            result["units"]["database"] = m.group(1)         # "MICRONS"
            result["units"]["database_microns"] = int(m.group(2))
        for key in ["CAPACITANCE", "CURRENT", "RESISTANCE", "TIME", "POWER", "VOLTAGE", "FREQUENCY"]:
            m = re.search(rf"{key}\s+(\d+)\s*;", units_block)
            if m:
                result["units"][key.lower()] = int(m.group(1))

    # Parse SITE blocks
    for site_match in re.finditer(
        r"SITE\s+(\S+)\s+(.*?)END\s+\1\b", content, re.DOTALL
    ):
        site_name = site_match.group(1)
        site_body = site_match.group(2)
        site = {}
        m = re.search(r"SIZE\s+(\S+)\s+BY\s+(\S+)\s*;", site_body)
        if m:
            site["width"] = float(m.group(1))
            site["height"] = float(m.group(2))
        m = re.search(r"CLASS\s+(\S+)\s*;", site_body)
        if m:
            site["class"] = m.group(1)
        m = re.search(r"SYMMETRY\s+(.*?);", site_body, re.DOTALL)
        if m:
            site["symmetry"] = m.group(1).strip().split()
        result["sites"][site_name] = site

    # Parse LAYER blocks (minimal — just what matters for routing)
    for layer_match in re.finditer(
        r"LAYER\s+(\S+)\s+(.*?)END\s+\1\b", content, re.DOTALL
    ):
        layer_name = layer_match.group(1)
        layer_body = layer_match.group(2)
        layer = {}
        m = re.search(r"TYPE\s+(\S+)\s*;", layer_body)
        if m:
            layer["type"] = m.group(1)
        m = re.search(r"DIRECTION\s+(\S+)\s*;", layer_body)
        if m:
            layer["direction"] = m.group(1)
        m = re.search(r"PITCH\s+(\S+)\s*;", layer_body)
        if m:
            layer["pitch"] = float(m.group(1))
        m = re.search(r"WIDTH\s+(\S+)\s*;", layer_body)
        if m:
            layer["width"] = float(m.group(1))
        if layer:  # only store if we parsed something
            result["layers"][layer_name] = layer

    # Parse MACRO blocks (the meat of it)
    for macro_match in re.finditer(
        r"MACRO\s+(\S+)\s+(.*?)END\s+\1\b", content, re.DOTALL
    ):
        macro_name = macro_match.group(1)
        macro_body = macro_match.group(2)
        macro = {"name": macro_name, "pins": []}

        m = re.search(r"CLASS\s+(\S+)\s*;", macro_body)
        if m:
            macro["class"] = m.group(1)

        m = re.search(r"FOREIGN\s+(\S+)\s+(\S+)\s+(\S+)\s*;", macro_body)
        if m:
            macro["foreign"] = {
                "name": m.group(1),
                "x": float(m.group(2)),
                "y": float(m.group(3)),
            }

        m = re.search(r"ORIGIN\s+(\S+)\s+(\S+)\s*;", macro_body)
        if m:
            macro["origin"] = (float(m.group(1)), float(m.group(2)))

        m = re.search(r"SIZE\s+(\S+)\s+BY\s+(\S+)\s*;", macro_body)
        if m:
            macro["width"] = float(m.group(1))
            macro["height"] = float(m.group(2))

        m = re.search(r"SYMMETRY\s+(.*?);", macro_body, re.DOTALL)
        if m:
            macro["symmetry"] = m.group(1).strip().split()

        m = re.search(r"SITE\s+(\S+)\s*;", macro_body)
        if m:
            macro["site"] = m.group(1)

        # Parse PIN blocks within this macro
        for pin_match in re.finditer(
            r"PIN\s+(\S+)\s+(.*?)END\s+\1\b", macro_body, re.DOTALL
        ):
            pin_name = pin_match.group(1)
            pin_body = pin_match.group(2)
            pin = {"name": pin_name, "rects": []}

            m = re.search(r"DIRECTION\s+(\S+)\s*;", pin_body)
            if m:
                pin["direction"] = m.group(1)

            m = re.search(r"USE\s+(\S+)\s*;", pin_body)
            if m:
                pin["use"] = m.group(1)

            # Parse RECTs (geometry of the pin on metal layers)
            for rect_match in re.finditer(
                r"RECT\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*;", pin_body
            ):
                pin["rects"].append({
                    "x1": float(rect_match.group(1)),
                    "y1": float(rect_match.group(2)),
                    "x2": float(rect_match.group(3)),
                    "y2": float(rect_match.group(4)),
                })

            macro["pins"].append(pin)

        result["macros"][macro_name] = macro

    return result


def get_cell_width_db(lef: dict, macro_name: str, db_microns: int) -> int:
    """
    Get the cell width for a macro in database units (DBU).

    Args:
        lef: parsed LEF dict
        macro_name: macro name (e.g., "INV_X1", "BUF_X1")
        db_microns: database units per micron (e.g., 1000 or 2000)

    Returns:
        Cell width in DBU, or None if macro not found.
    """
    macro = lef.get("macros", {}).get(macro_name)
    if not macro:
        return None
    width_um = macro.get("width")
    if width_um is None:
        return None
    return int(round(width_um * db_microns))


def get_site_dimensions(lef: dict, site_name: str = None) -> tuple:
    """
    Get (width, height) of a site in microns.
    Defaults to the first CLASS CORE site if not specified.
    """
    if not lef.get("sites"):
        return None
    if site_name is None:
        for name, site in lef["sites"].items():
            if site.get("class") == "CORE":
                return (site.get("width"), site.get("height"))
        # Fall back to first site
        first = next(iter(lef["sites"].values()))
        return (first.get("width"), first.get("height"))
    site = lef["sites"].get(site_name)
    if site:
        return (site.get("width"), site.get("height"))
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python lef_parser.py <path-to-lef>")
        sys.exit(1)
    lef = parse_lef(sys.argv[1])
    print(f"LEF version: {lef['version']}")
    print(f"Units: {lef['units']}")
    print(f"Sites: {len(lef['sites'])}")
    print(f"Layers: {len(lef['layers'])}")
    print(f"Macros: {len(lef['macros'])}")
    if lef["macros"]:
        first_name = next(iter(lef["macros"]))
        first = lef["macros"][first_name]
        print(f"  First macro: {first_name}")
        print(f"    class: {first.get('class')}")
        print(f"    size: {first.get('width')} x {first.get('height')}")
        print(f"    pins: {[p['name'] for p in first.get('pins', [])]}")
