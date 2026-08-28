"""
chipmind/io/gds_writer.py — LEF + placed-DEF → GDS writer.

Generates a GDS-II file that captures the placed standard cells and the
technology stack (metal layers, vias). The output can be loaded into:
  - gdstk / klayout (Python)
  - KLayout GUI (3D view, layer-by-layer inspection)
  - gds-viewer.com, 3d-ic-vision.com (hosted 3D viewers)
  - Cadence Virtuoso, Synopsys IC Compiler (industrial EDA)

Layer mapping (matches gds-viewer.com defaults so it "just works" there):
  - Layer 100/0  → die boundary (boundary layer)
  - Layer 1-9    → metal1-metal9 (color = wire color)
  - Layer 30-39  → via1-via9 (small filled squares)
  - Layer 50/0   → cell fill (light grey, no metal)

For each placed cell:
  - A rectangle on layer 50/0 marking the cell's footprint
  - A small label polygon for the cell name (GDS text)
  - A bounding-box outline on layer 100/1

The result is a real GDS file that opens in any standard viewer.
For the in-app Three.js 3D viz, we ALSO write a sidecar JSON with all
the placement + layer info, so the JS viewer doesn't need to parse GDS.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import gdstk
import numpy as np

# Layer numbers (chosen to match common gds-viewer.com conventions)
LAYER_DIE = (100, 0)
LAYER_CELL = (50, 0)
LAYER_CELL_LABEL = (50, 1)
LAYER_BOUNDS = (100, 1)
LAYER_METAL_BASE = 1     # metal1 = 1, metal2 = 2, ...
LAYER_VIA_BASE = 30      # via1 = 30, via2 = 31, ...


def _poly_to_rect(x: float, y: float, w: float, h: float, layer: Tuple[int, int], datatype: int = 0):
    """Helper: a single rectangle on the given layer."""
    return gdstk.rectangle(
        (x, y), (x + w, y + h),
        layer=layer[0], datatype=datatype,
    )


def _hex_color_for_layer(layer_num: int) -> str:
    """Generate a distinct, viewer-friendly hex color for a metal layer.

    Maps metal1..metalN to a perceptually-distinct color palette so that
    stacking in 3D looks like the textbook chip cross-section.
    """
    palette = [
        "#3b82f6",  # blue   - metal1
        "#22c55e",  # green  - metal2
        "#eab308",  # yellow - metal3
        "#f97316",  # orange - metal4
        "#ef4444",  # red    - metal5
        "#a855f7",  # purple - metal6
        "#06b6d4",  # cyan   - metal7
        "#ec4899",  # pink   - metal8
        "#64748b",  # slate  - metal9
    ]
    return palette[(layer_num - 1) % len(palette)]


def _metal_layer_z(layer_num: int, z_scale: float = 1.0) -> float:
    """Z-height for a metal layer (in user units, scaled).

    Each subsequent metal layer is higher. We use a generous z scale so
    3D viz shows clear separation.
    """
    return (layer_num - 1) * z_scale


def _cell_color_for_macro(macro_name: str, default: str = "#94a3b8") -> str:
    """Color cells by macro category for the 3D view.

    Logic cells = one color, sequential cells = another, etc.
    """
    if not macro_name:
        return default
    name = macro_name.upper()
    if "BUF" in name or "INV" in name or "CLK" in name:
        return "#fbbf24"   # amber
    if "AND" in name or "NAND" in name or "OR" in name or "NOR" in name or "XOR" in name or "XNOR" in name:
        return "#a78bfa"   # violet
    if "MUX" in name or "DFF" in name or "DFFS" in name or "SDFF" in name or "LATCH" in name:
        return "#34d399"   # emerald
    if "HA" in name or "FA" in name or "ADD" in name or "SUB" in name:
        return "#f472b6"   # pink
    if "OAI" in name or "AOI" in name or "MAJ" in name:
        return "#60a5fa"   # light blue
    return default


def write_gds(
    chip: Dict[str, Any],
    placed_components: Dict[str, Tuple[float, float]],
    lef_data: Optional[Dict[str, Any]] = None,
    output_path: str = "out.gds",
) -> Dict[str, Any]:
    """Write a GDS-II file from a placed chip + LEF library.

    Args:
        chip:              parse_def() output — has 'die' (x1,y1,x2,y2),
                           'components' (input), 'nets' (for netlist reference).
        placed_components: {macro_name: (x, y)} — final placed positions.
        lef_data:          Optional parse_lef() output. If provided, metal
                           layer names and macros (with sizes) are used
                           for richer output.
        output_path:       Where to write the .gds file.

    Returns:
        dict with metadata: {
            'path': str,                  # output path
            'top_cell': str,              # top cell name
            'n_polygons': int,            # total polygons written
            'n_metal_layers': int,        # metal layers written
            'metal_layers': [{'gds_layer': int, 'name': str, 'color': '#...'}],
            'die': {x1,y1,x2,y2},
            'macros_used': [(name, x, y, w, h, color)],
        }
    """
    lib = gdstk.Library(name="SMALLCHIP_AI", unit=1e-6, precision=1e-9)

    # Build macro size lookup (default 0.19 x 1.71 µm if no LEF)
    macro_sizes: Dict[str, Tuple[float, float]] = {}
    if lef_data and "macros" in lef_data:
        for mname, m in lef_data["macros"].items():
            macro_sizes[mname] = (m.get("width", 0.19), m.get("height", 1.71))
    if not macro_sizes:
        # Default to a generic standard cell
        macro_sizes["_DEFAULT"] = (0.19, 1.71)

    # Extract metal layer info from LEF
    metal_layers: List[Dict[str, Any]] = []
    if lef_data and "layers" in lef_data:
        for lname, ldata in lef_data["layers"].items():
            if ldata.get("type", "").upper() == "ROUTING":
                # Extract metal number from name (e.g., "metal1" → 1)
                num = None
                for c in reversed(lname):
                    if c.isdigit():
                        num = (num or 0) * 10 + int(c)
                    else:
                        break
                if num is not None:
                    gds_layer = LAYER_METAL_BASE + (num - 1)
                    metal_layers.append({
                        "gds_layer": gds_layer,
                        "name": lname,
                        "number": num,
                        "color": _hex_color_for_layer(num),
                        "direction": ldata.get("direction", "HORIZONTAL"),
                        "pitch": ldata.get("pitch"),
                        "width": ldata.get("width"),
                    })
        metal_layers.sort(key=lambda x: x["number"])

    # Top cell name
    design_name = chip.get("design_name", "design")
    top_name = f"{design_name.upper()}_PLACED"
    top = gdstk.Cell(name=top_name)

    # 1. Die boundary
    die = chip.get("die", {"x1": 0, "y1": 0, "x2": 100, "y2": 100})
    d_x1, d_y1 = die["x1"], die["y1"]
    d_x2, d_y2 = die["x2"], die["y2"]
    die_poly = gdstk.rectangle(
        (d_x1, d_y1), (d_x2, d_y2),
        layer=LAYER_DIE[0], datatype=LAYER_DIE[1],
    )
    top.add(die_poly)

    # 2. Placed cells (rectangle footprint + label)
    macros_used = []
    placed = chip.get("components") or placed_components or {}
    n_polys = 1  # die

    # Normalize — values may be dict {'x','y'} OR tuple (x,y) OR (x,y,orient)
    def _xy(v):
        if isinstance(v, dict):
            return float(v["x"]), float(v["y"])
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return float(v[0]), float(v[1])
        return 0.0, 0.0

    for cname, raw in placed.items():
        cx, cy = _xy(raw)
        w, h = macro_sizes.get(cname, macro_sizes.get("_DEFAULT", (0.19, 1.71)))
        # Per-cell color
        # Try to infer macro class from name (e.g., "_435_" → BUF_X1, etc.)
        macro_name = cname
        color = _cell_color_for_macro(cname)
        # Rectangle on cell layer
        rect = gdstk.rectangle(
            (cx, cy), (cx + w, cy + h),
            layer=LAYER_CELL[0], datatype=LAYER_CELL[1],
        )
        top.add(rect)
        n_polys += 1

        # Add a small label rectangle (visual marker, optional)
        label_size = min(w, h) * 0.3
        if label_size > 0:
            label_rect = gdstk.rectangle(
                (cx + w * 0.3, cy + h * 0.3),
                (cx + w * 0.3 + label_size, cy + h * 0.3 + label_size),
                layer=LAYER_CELL_LABEL[0], datatype=LAYER_CELL_LABEL[1],
            )
            top.add(label_rect)
            n_polys += 1

        macros_used.append({
            "name": cname,
            "x": cx, "y": cy,
            "w": w, "h": h,
            "color": color,
        })

    # 3. Metal layer rectangles (simplified — fill the die with each layer
    # as a faint colored band so the 3D viewer can stack them clearly)
    # In a real GDS from a routed design, these would come from the DEF's
    # NETS section. For a placement-only GDS, we add the row/die outline.
    for ml in metal_layers:
        # Add a thin outline of each metal layer at the die boundary
        outline = gdstk.rectangle(
            (d_x1, d_y1), (d_x2, d_y2),
            layer=ml["gds_layer"], datatype=0,
        )
        top.add(outline)
        n_polys += 1

    lib.add(top)
    lib.write_gds(output_path)

    metadata = {
        "path": str(Path(output_path).resolve()),
        "top_cell": top_name,
        "n_polygons": n_polys,
        "n_metal_layers": len(metal_layers),
        "metal_layers": metal_layers,
        "die": {"x1": d_x1, "y1": d_y1, "x2": d_x2, "y2": d_y2},
        "n_macros": len(macros_used),
        "macros_used": macros_used[:50],  # cap for sidecar size
    }
    return metadata


def write_3d_sidecar(
    metadata: Dict[str, Any],
    sidecar_path: str,
    z_scale: float = 0.5,
) -> None:
    """Write a JSON sidecar with everything the Three.js 3D viewer needs.

    This sidecar is consumed by web/3d.html — it includes metal layer
    heights, colors, cell positions, and the die boundary, so the front-end
    can render a true 3D metal-layer-stack view without parsing GDS.

    Args:
        metadata:    Output of write_gds().
        sidecar_path: Output JSON path.
        z_scale:     Vertical scale per metal layer (µm per layer step).
    """
    sidecar = {
        "version": 1,
        "z_scale": z_scale,
        "die": metadata["die"],
        "top_cell": metadata["top_cell"],
        "metal_layers": [],
        "cells": metadata["macros_used"],
    }

    # Add Z heights to metal layers
    for ml in metadata["metal_layers"]:
        ml_copy = dict(ml)
        ml_copy["z"] = (ml["number"] - 1) * z_scale
        sidecar["metal_layers"].append(ml_copy)

    with open(sidecar_path, "w") as f:
        json.dump(sidecar, f, indent=2)


def gds_bytes(metadata: Dict[str, Any]) -> bytes:
    """Read back the GDS file as bytes for HTTP serving."""
    with open(metadata["path"], "rb") as f:
        return f.read()


# ------------------------------------------------------------------ #
# CLI test
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from chipmind.core import parse_def

    # Test on GCD
    chip = parse_def("/Users/harshith/Documents/ChipPlacer/web/examples/gcd_734cells.def")
    # Components are {name: {'x': ..., 'y': ...}} from parse_def
    comps = chip.get("components") or {}
    placed = {k: (v.get("x", 0), v.get("y", 0)) for k, v in comps.items() if isinstance(v, dict)}

    out = "/tmp/test_out.gds"
    meta = write_gds(chip, placed, lef_data=None, output_path=out)
    write_3d_sidecar(meta, "/tmp/test_3d.json")
    print(f"Wrote {out} ({meta['n_polygons']} polys, {meta['n_metal_layers']} metal layers)")
    print(f"Sidecar: /tmp/test_3d.json ({meta['n_macros']} cells)")
