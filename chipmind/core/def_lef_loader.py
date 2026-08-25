"""
chipmind/core/def_lef_loader.py — Combined DEF + LEF loader

Takes both a DEF and a LEF file and produces a chip dict with:
  - die, components (with real cell widths), nets
  - macros (per-cell width/height/pins)
  - site (for row snapping)

This replaces the uniform `cell_w` parameter in the smart legalizer with
real per-cell widths, which is what you need for accurate legal placement.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from typing import Dict, Any
try:
    from .def_parser import parse_def
    from .lef_parser import parse_lef, get_cell_width_db, get_site_dimensions
except ImportError:
    from chipmind.core.def_parser import parse_def
    from chipmind.core.lef_parser import parse_lef, get_cell_width_db, get_site_dimensions


def load_design(def_path: str, lef_path: str = None) -> dict:
    """
    Load a chip design from DEF (and optionally LEF).

    Args:
        def_path: path to .def file
        lef_path: optional path to .lef file for cell library

    Returns:
        dict with:
          - die, components, nets (from DEF)
          - macros: {name: {width_db, height_db, ...}} (from LEF, in DBU)
          - site: {width_um, height_um}
          - default_cell_width_db: int (most common cell width, in DBU)
          - units: {database_microns, ...}
    """
    chip = parse_def(def_path)

    if lef_path is None:
        # No LEF — return what we have with sensible defaults
        chip["macros"] = {}
        chip["site"] = None
        chip["default_cell_width_db"] = 380  # FreePDK45 minimum
        return chip

    lef = parse_lef(lef_path)
    db_microns = lef.get("units", {}).get("database_microns", 2000)

    # Build per-macro width/height table
    macros_db = {}
    widths = []
    for macro_name, macro in lef.get("macros", {}).items():
        w_um = macro.get("width")
        h_um = macro.get("height")
        if w_um is None or h_um is None:
            continue
        w_db = int(round(w_um * db_microns))
        h_db = int(round(h_um * db_microns))
        macros_db[macro_name] = {
            "width_um": w_um,
            "height_um": h_um,
            "width_db": w_db,
            "height_db": h_db,
            "pins": [p["name"] for p in macro.get("pins", [])],
            "class": macro.get("class"),
        }
        widths.append(w_db)

    # Default cell width = mode (most common)
    if widths:
        from collections import Counter
        default_w = Counter(widths).most_common(1)[0][0]
    else:
        default_w = 380

    # Get site dimensions
    site_dims = get_site_dimensions(lef)  # (w, h) in um

    chip["macros"] = macros_db
    chip["site"] = {
        "width_um": site_dims[0] if site_dims else None,
        "height_um": site_dims[1] if site_dims else None,
    } if site_dims else None
    chip["default_cell_width_db"] = default_w
    chip["units"] = lef.get("units", {})
    chip["lef_version"] = lef.get("version")

    return chip


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python def_lef_loader.py <def-path> <lef-path>")
        sys.exit(1)
    chip = load_design(sys.argv[1], sys.argv[2])
    print(f"Die: {chip['die']}")
    print(f"Components: {len(chip['components'])}")
    print(f"Nets: {len(chip['nets'])}")
    print(f"Macros: {len(chip['macros'])}")
    if chip["macros"]:
        first = next(iter(chip["macros"].items()))
        print(f"  First macro: {first[0]}: {first[1]['width_um']}x{first[1]['height_um']} um ({first[1]['width_db']}x{first[1]['height_db']} DBU)")
    print(f"Site: {chip['site']}")
    print(f"Default cell width: {chip['default_cell_width_db']} DBU")
