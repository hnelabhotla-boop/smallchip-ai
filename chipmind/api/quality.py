"""
Quality metrics API — congestion and thermal estimation endpoints.

GET /api/quality — run congestion and thermal estimation on the current placement
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from chipmind.core import parse_def
from chipmind.ml.quality import estimate_congestion, estimate_thermal

router = APIRouter()


@router.get("/api/quality")
async def quality_metrics(def_path: str, grid: int = 10):
    """Run congestion and thermal estimation on a .def file."""
    try:
        chip = parse_def(def_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse DEF: {e}")

    cong = estimate_congestion(chip, grid_x=grid, grid_y=grid)
    therm = estimate_thermal(chip, grid_x=grid, grid_y=grid)

    return {
        "design": Path(def_path).stem,
        "n_cells": len(chip["components"]),
        "congestion": cong,
        "thermal": therm,
    }
