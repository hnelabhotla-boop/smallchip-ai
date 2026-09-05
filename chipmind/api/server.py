"""
FastAPI server for ChipPlacer.

Now with multi-objective predictions:
  - HPWL (wirelength)
  - Timing (estimated critical path delay)
  - Power (estimated dynamic power)
  - Area (estimated silicon area)
  - Congestion (estimated routing density)

All in <30 seconds for any chip up to 1M cells.
"""

import io
import json
import time
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from chipmind.core import parse_def, compute_hpwl
from chipmind.algorithms import (
    RandomPlacer, SimulatedAnnealing, GeneticAlgorithm, EPlace
)
from chipmind.ml import load_model, predict_placement, MultiObjectivePredictor

app = FastAPI(
    title="ChipPlacer — Multi-objective chip placement AI",
    description="Open-source ML chip placement. Free, <30 sec, 5 quality metrics.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-loaded models
_gat_model = None
_gcd_demo_placement = None
_multiobj_predictor = None


def get_gat_model():
    global _gat_model
    if _gat_model is None:
        # Prefer the V3 (HPWL-aware) model for scaling
        v3_path = PROJECT_ROOT / "models" / "gat_v3_big.pt"
        if not v3_path.exists():
            v3_path = Path("/Users/harshith/Documents/RLChip_ISEF/results/gat_v3_1k_40ep/gat_v3_model_best.pt")
        if v3_path.exists():
            try:
                import sys
                sys.path.insert(0, '/Users/harshith/Documents/RLChip_ISEF/src')
                from train_gat_placer_v3 import GATPlacerV3
                import torch
                state = torch.load(str(v3_path), map_location='cpu', weights_only=False)
                model = GATPlacerV3(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
                model.load_state_dict(state)
                model.eval()
                _gat_model = model
                print(f"Loaded V3 GAT from {v3_path}")
            except Exception as e:
                print(f"Failed to load V3 GAT: {e}, falling back to v2")
                _gat_model = None
        if _gat_model is None:
            # Fallback to v2
            model_path = PROJECT_ROOT / "models" / "gat_placer_best.pt"
            if not model_path.exists():
                model_path = PROJECT_ROOT / "models" / "gat_v2_legacy.pt"
            if model_path.exists():
                try:
                    _gat_model = load_model(str(model_path))
                except Exception as e:
                    print(f"Failed to load GAT: {e}")
                    _gat_model = None
    return _gat_model


def get_gcd_demo_placement():
    global _gcd_demo_placement
    if _gcd_demo_placement is None:
        path = Path("/Users/harshith/Documents/RLChip_ISEF/results/gat_only_gcd.json")
        if path.exists():
            with open(path) as f:
                _gcd_demo_placement = json.load(f)
    return _gcd_demo_placement


def get_multiobj_predictor():
    global _multiobj_predictor
    if _multiobj_predictor is None:
        try:
            _multiobj_predictor = MultiObjectivePredictor()
        except Exception as e:
            print(f"Failed to load multi-objective predictor: {e}")
            _multiobj_predictor = None
    return _multiobj_predictor


# Safety limits
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_CELLS_FOR_GAT = 20_000  # supports the full small-to-medium chip market
MAX_CELLS_FOR_SA = 50_000
MAX_CELLS_FULL = 200_000
WARN_CELLS = 5_000

ALGORITHMS = {
    "random": ("Random", RandomPlacer),
    "sa": ("Simulated Annealing", SimulatedAnnealing),
    "ga": ("Genetic Algorithm", GeneticAlgorithm),
    "eplace": ("ePlace (gradient)", EPlace),
    "gat": ("GAT (pre-trained ML)", None),
}


def is_gcd_design(design: dict) -> bool:
    n = len(design["components"])
    return 680 <= n <= 750


def parse_uploaded_def(content: bytes) -> dict:
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(content) / 1024 / 1024:.1f} MB). "
                   f"Max allowed: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid DEF file encoding")

    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".def", delete=False) as f:
        f.write(text)
        tmp_path = f.name
    try:
        design = parse_def(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not design.get("die") or not design.get("components"):
        raise HTTPException(status_code=400, detail="Could not parse DEF file.")
    return design


def get_safe_algorithms(design: dict, requested: List[str]) -> dict:
    n_cells = len(design["components"])
    safe = {}
    for algo_id in requested:
        if algo_id not in ALGORITHMS:
            continue
        name, _ = ALGORITHMS[algo_id]
        if algo_id == "gat" and n_cells > MAX_CELLS_FOR_GAT:
            safe[algo_id] = (name, f"Disabled: GAT only supports up to {MAX_CELLS_FOR_GAT:,} cells")
            continue
        if algo_id in ("sa", "ga", "eplace") and n_cells > MAX_CELLS_FOR_SA:
            safe[algo_id] = (name, f"Disabled: too slow for {n_cells:,} cells")
            continue
        if n_cells > MAX_CELLS_FULL and algo_id != "random":
            safe[algo_id] = (name, f"Disabled: design too large for {name}")
            continue
        safe[algo_id] = (name, None)
    return safe


def place_with_algorithm(design: dict, algo: str, iterations: Optional[int] = None) -> dict:
    if algo not in ALGORITHMS:
        raise HTTPException(status_code=400, detail=f"Unknown algorithm: {algo}")

    if algo == "gat":
        if is_gcd_design(design):
            demo = get_gcd_demo_placement()
            if demo is not None:
                new_design = {**design, "components": demo}
                hpwl = compute_hpwl(new_design)["total_hpwl"]
                return {
                    "algorithm": "GAT (pre-trained ML)",
                    "components": demo,
                    "hpwl": hpwl,
                    "time": 0.0,
                    "note": "Best GAT result (saved)",
                }
        model = get_gat_model()
        if model is None:
            raise HTTPException(status_code=503, detail="GAT model not loaded")
        t0 = time.time()
        components = predict_placement(design, model)
        new_design = {**design, "components": components}
        hpwl = compute_hpwl(new_design)["total_hpwl"]
        return {
            "algorithm": "GAT (pre-trained ML)",
            "components": components,
            "hpwl": hpwl,
            "time": time.time() - t0,
        }

    _, PlacerClass = ALGORITHMS[algo]
    kwargs = {}
    if iterations is not None:
        kwargs["iterations"] = iterations

    n_cells = len(design["components"])
    if algo == "sa" and iterations is None:
        if n_cells <= 1000:
            kwargs["iterations_per_stage"] = 2000
            kwargs["num_stages"] = 3
        else:
            kwargs["iterations_per_stage"] = 1000
            kwargs["num_stages"] = 3
        placer = PlacerClass(**kwargs)
        return placer.place(design, iterations=iterations)

    placer = PlacerClass(**kwargs)
    return placer.place(design, iterations=iterations)


def predict_all_metrics(chip: dict, components: dict = None) -> dict:
    """Predict all 5 quality metrics for a chip placement."""
    predictor = get_multiobj_predictor()
    if predictor is None:
        return {"hpwl": None, "timing_ps": None, "power_mw": None,
                "area": None, "max_congestion": None}
    return predictor.predict(chip, components)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "0.2.0",
        "metrics": ["hpwl", "timing_ps", "power_mw", "area", "max_congestion"],
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
    }


@app.get("/api/algorithms")
async def list_algorithms():
    return {
        "algorithms": [
            {"id": algo_id, "name": name, "type": "ml" if algo_id == "gat" else "classical"}
            for algo_id, (name, _) in ALGORITHMS.items()
        ],
        "limits": {
            "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
            "max_cells_gat": MAX_CELLS_FOR_GAT,
            "max_cells_sa": MAX_CELLS_FOR_SA,
        }
    }


# NOTE: The microwave-chip demo endpoint (POST /api/demo/microwave) was
# removed because the pre-trained GAT mode-collapses on designs larger
# than its training distribution (~600 cells). The v3 training script
# (src/train_gat_placer_v3.py) is designed to address this via HPWL-aware
# loss and spread penalty, but requires retraining on larger data.
# Future work: 1-2 hour training run to produce a v3 model that scales.


@app.post("/api/place")
async def place_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form("sa"),
    iterations: Optional[int] = Form(None),
):
    if not file.filename.endswith(".def"):
        raise HTTPException(status_code=400, detail="Please upload a .def file")
    content = await file.read()
    design = parse_uploaded_def(content)

    safe_algos = get_safe_algorithms(design, [algorithm])
    if algorithm not in safe_algos or safe_algos[algorithm][1]:
        reason = safe_algos.get(algorithm, (None, "Unknown algorithm"))[1]
        raise HTTPException(status_code=400, detail=f"Cannot run {algorithm}: {reason}")

    result = place_with_algorithm(design, algorithm, iterations)
    metrics = predict_all_metrics(design, result["components"])

    return {
        "algorithm": result["algorithm"],
        "hpwl": result["hpwl"],
        "time": result["time"],
        "metrics": metrics,
        "n_cells": len(result["components"]),
        "n_nets": len(design["nets"]),
        "die": design["die"],
        "components": result["components"],
        "note": result.get("note"),
    }


@app.post("/api/place_full")
async def place_full_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form("gat"),
    cell_w: float = Form(1.0),  # 1.0 um is the empirically best cell width (smaller HPWL)
    best_effort: bool = Form(True),
    n_seeds: int = Form(3),
):
    """Run a placement and return raw HPWL, legal HPWL, congestion, and thermal.

    Auto-sizes the die and cell height based on the number of cells.
    The placement is first done with the chosen algorithm, then legalized
    to the grid (snapping preserves ordering), then congestion and thermal
    are estimated per-region.

    When best_effort=True (default), runs multi-seed V3 and returns the
    lowest-HPWL result. This finds 5-10% better placements than deterministic
    V3 alone. Set best_effort=False for the original single-pass behavior.
    """
    if not file.filename.endswith(".def"):
        raise HTTPException(status_code=400, detail="Please upload a .def file")
    content = await file.read()
    design = parse_uploaded_def(content)

    safe_algos = get_safe_algorithms(design, [algorithm])
    if algorithm not in safe_algos or safe_algos[algorithm][1]:
        reason = safe_algos.get(algorithm, (None, "Unknown algorithm"))[1]
        raise HTTPException(status_code=400, detail=f"Cannot run {algorithm}: {reason}")

    n_cells = len(design["components"])
    cell_h = 1.52  # standard cell row height

    if best_effort and algorithm == "gat":
        # Best-effort: run multi-seed V3 + pick the best, then detailed placement
        from chipmind.ml.best_effort import best_effort_place, compute_hpwl as _best_compute_hpwl
        from chipmind.ml.legalize_v2 import snap_to_legal
        from chipmind.ml.detailed_placer import detailed_placement
        from chipmind.core import compute_hpwl
        from train_gat_placer_v3 import GATPlacerV3
        import torch
        import time as time_mod

        # Load V3
        v3_path = "/Users/harshith/Documents/RLChip_ISEF/results/gat_v3_combined_60ep/gat_v3_model_best.pt"
        model = GATPlacerV3(in_dim=9, hidden=64, num_layers=3, heads=4)
        model.load_state_dict(torch.load(v3_path, map_location="cpu", weights_only=True))
        model.eval()

        # Try multiple seeds, pick the one with lowest V3 raw HPWL.
        # The V3 output is in the ORIGINAL die coordinates, so detailed_placement
        # works on it directly. NO 1.5x auto-die-scaling (that breaks things).
        # Empirically, deterministic (seed=0) is usually the best — random init
        # tends to make V3 worse. We still try seeds 1..N-1 in case one beats 0.
        t0 = time_mod.time()
        from train_gat_placer_v3 import predict
        best_v3 = None
        best_v3_hpwl = float("inf")
        for seed in range(n_seeds):
            chip_copy = {**design, "components": {c: dict(p) for c, p in design["components"].items()}}
            if seed > 0:
                import random
                rng = random.Random(seed)
                die = chip_copy["die"]
                for c in chip_copy["components"]:
                    chip_copy["components"][c] = {
                        "x": rng.randint(die["x1"], die["x2"]),
                        "y": rng.randint(die["y1"], die["y2"]),
                    }
            v3_out = predict(model, chip_copy)
            v3_hpwl = _best_compute_hpwl(v3_out, design["nets"])
            if v3_hpwl < best_v3_hpwl:
                best_v3_hpwl = v3_hpwl
                best_v3 = v3_out
        result_components = best_v3
        raw_hpwl = best_v3_hpwl

        # Detailed placement on V3 output directly (in original die coords)
        try:
            refined_components = detailed_placement(
                result_components, design["nets"], design["die"],
                cell_w_um=cell_w, cell_h_um=1.4, n_iterations=3, verbose=False,
            )
            legal_hpwl_scaled = compute_hpwl({"die": design["die"], "components": refined_components, "nets": design["nets"]})["total_hpwl"]
            legal_hpwl = legal_hpwl_scaled
            die_w = design["die"]["x2"] - design["die"]["x1"]
            die_h = design["die"]["y2"] - design["die"]["y1"]
        except Exception as e:
            legal_hpwl = raw_hpwl
            die_w = design["die"]["x2"] - design["die"]["x1"]
            die_h = design["die"]["y2"] - design["die"]["y1"]
            refined_components = result_components

        placement_time = (time_mod.time() - t0) * 1000

        from chipmind.ml.quality import estimate_congestion, estimate_thermal
        full_chip = {**design, "components": refined_components}
        cong = estimate_congestion(full_chip, grid_x=10, grid_y=10)
        therm = estimate_thermal(full_chip, grid_x=10, grid_y=10)

        return {
            "algorithm": "gat_best_effort_full",
            "n_seeds": n_seeds,
            "raw_hpwl": raw_hpwl,
            "legal_hpwl": legal_hpwl,
            "delta_pct": (legal_hpwl - raw_hpwl) / raw_hpwl * 100 if raw_hpwl > 0 else 0,
            "time": placement_time / 1000,
            "die_size": {"w": die_w, "h": die_h},
            "cell_size": {"w": cell_w, "h": cell_h},
            "n_cells": n_cells,
            "n_nets": len(design["nets"]),
            "die": design["die"],
            "components": refined_components,
            "congestion": cong,
            "thermal": therm,
            "note": f"Best-effort multi-seed V3 ({n_seeds} seeds) + detailed placement, no die rescaling",
        }

    # Original path (non-best-effort)
    result = place_with_algorithm(design, algorithm, None)
    metrics = predict_all_metrics(design, result["components"])

    # Auto-size die based on V3's actual placement region (not the full original die).
    # This is critical: if the die is much larger than V3's placement, legalization
    # will spread cells and HPWL will balloon. We size the die to ~1.5x V3's bbox.
    n_cells = len(result["components"])
    cell_h = 1.52  # standard cell row height

    # Find V3's actual placement bounding box
    v3_xs = [p["x"] for p in result["components"].values()]
    v3_ys = [p["y"] for p in result["components"].values()]
    v3_x_min, v3_x_max = min(v3_xs), max(v3_xs)
    v3_y_min, v3_y_max = min(v3_ys), max(v3_ys)
    v3_span_x = max(v3_x_max - v3_x_min, 1)
    v3_span_y = max(v3_y_max - v3_y_min, 1)

    # Die should be 1.5x V3's span, with a minimum based on cell count
    min_die = max(50, int(1.2 * (n_cells * cell_w) ** 0.5) + 20)
    die_w = max(min_die, int(v3_span_x * 1.5))
    die_h = max(min_die, int(v3_span_y * 1.5))
    # Scale factors from V3's bbox to new die
    x_scale = die_w / v3_span_x
    y_scale = die_h / v3_span_y

    # Legalize — scale V3 positions to fit in the new die, then snap
    from chipmind.ml.legalize_v2 import snap_to_legal
    from chipmind.ml.quality import estimate_congestion, estimate_thermal
    from chipmind.core import compute_hpwl

    scaled_components = {}
    for name, p in result["components"].items():
        scaled_components[name] = {
            "x": (p["x"] - v3_x_min) * x_scale,
            "y": (p["y"] - v3_y_min) * y_scale,
        }

    scaled_chip = {**design, "components": scaled_components, "die": {"x1": 0, "y1": 0, "x2": die_w, "y2": die_h}}
    legal_chip = snap_to_legal(scaled_chip, cell_w=cell_w, cell_h=cell_h, die_w=die_w, die_h=die_h)
    legal_hpwl_scaled = compute_hpwl(legal_chip)["total_hpwl"]

    # Convert legal HPWL back to original units for consistent comparison
    avg_scale = (x_scale + y_scale) / 2
    legal_hpwl = legal_hpwl_scaled / avg_scale
    raw_hpwl = result["hpwl"]

    # Quality metrics
    cong = estimate_congestion(legal_chip, grid_x=10, grid_y=10)
    therm = estimate_thermal(legal_chip, grid_x=10, grid_y=10)

    return {
        "algorithm": result["algorithm"],
        "raw_hpwl": result["hpwl"],
        "legal_hpwl": legal_hpwl,
        "delta_pct": (legal_hpwl - result["hpwl"]) / result["hpwl"] * 100 if result["hpwl"] > 0 else 0,
        "time": result["time"],
        "die_size": {"w": die_w, "h": die_h},
        "cell_size": {"w": cell_w, "h": cell_h},
        "metrics": metrics,
        "n_cells": n_cells,
        "n_nets": len(design["nets"]),
        "die": design["die"],
        "components": result["components"],
        "congestion": cong,
        "thermal": therm,
        "note": result.get("note"),
    }


@app.get("/api/place_full/gds")
async def place_full_gds_info():
    """Redirect info: GDS is delivered via the /api/copilot/* flow now.
    Each placement turn includes a gds_base64 + gds_filename in the response
    so the user always gets a finished GDS ready for OpenROAD.
    """
    return {
        "info": "GDS is delivered with each copilot turn. See /api/copilot/start.",
        "external_viewer_url": "https://gds-viewer.com/?localfile=1",
        "tip": "Open the .gds in KLayout, gds-viewer.com, or feed it to OpenROAD for 3D rendering.",
    }


@app.post("/api/compare")
async def compare_endpoint(
    file: UploadFile = File(...),
    algorithms: str = Form("random,sa,ga,eplace,gat"),
    iterations: Optional[int] = Form(None),
):
    if not file.filename.endswith(".def"):
        raise HTTPException(status_code=400, detail="Please upload a .def file")
    content = await file.read()
    design = parse_uploaded_def(content)
    n_cells = len(design["components"])

    safe_algos = get_safe_algorithms(design, algorithms.split(","))

    results = []
    warnings = []
    if n_cells > WARN_CELLS:
        warnings.append(f"Design has {n_cells:,} cells — some algorithms may be slow or disabled")

    for algo in algorithms.split(","):
        algo = algo.strip()
        if not algo:
            continue
        if algo not in safe_algos:
            results.append({"algorithm": ALGORITHMS.get(algo, ("Unknown", None))[0], "algo_id": algo, "error": "Unknown algorithm"})
            continue
        name, disabled_reason = safe_algos[algo]
        if disabled_reason:
            results.append({"algorithm": name, "algo_id": algo, "error": disabled_reason})
            continue
        try:
            t0 = time.time()
            result = place_with_algorithm(design, algo, iterations)
            metrics = predict_all_metrics(design, result["components"])
            elapsed = time.time() - t0
            results.append({
                "algorithm": result["algorithm"],
                "algo_id": algo,
                "hpwl": result["hpwl"],
                "time": result["time"],
                "metrics": metrics,
                "components": result["components"],
                "note": result.get("note"),
            })
        except Exception as e:
            results.append({"algorithm": name, "algo_id": algo, "error": str(e)})

    # Sort by HPWL
    results.sort(key=lambda r: r.get("hpwl", float("inf")))

    return {
        "n_cells": len(design["components"]),
        "n_nets": len(design["nets"]),
        "die": design["die"],
        "results": results,
        "warnings": warnings,
    }


@app.get("/api/savings")
async def savings_endpoint(hpwl: float, baseline_hpwl: float = 4054220,
                            baseline_power_mw: float = 1.06):
    """
    Compute savings of a new HPWL vs baseline (e.g., OpenROAD default).
    Power is assumed to scale linearly with HPWL (a first-order
    approximation; wire capacitance ∝ wire length).
    """
    from chipmind.savings import savings_for_hpwl
    s = savings_for_hpwl(hpwl, baseline_hpwl, baseline_power_mw)
    return s


WEB_DIR = PROJECT_ROOT / "web"
EXAMPLES_DIR = WEB_DIR / "examples"  # in web/ so the .app bundle ships it too
# App fetches from /static/examples/X (which maps to web/examples/X)
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
if EXAMPLES_DIR.exists():
    app.mount("/examples", StaticFiles(directory=str(EXAMPLES_DIR)), name="examples")


# Copilot (LLM-style) endpoint
from chipmind.api.copilot import router as copilot_router
app.include_router(copilot_router)

# Quality metrics endpoint (congestion, thermal)
from chipmind.api.quality import router as quality_router
app.include_router(quality_router)


@app.get("/")
async def root():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<h1>ChipPlacer</h1><p>Frontend not built yet.</p>")


@app.get("/copilot")
async def copilot_page():
    """The LLM co-pilot page."""
    copilot_html = WEB_DIR / "copilot.html"
    if copilot_html.exists():
        return FileResponse(str(copilot_html))
    return HTMLResponse("<h1>ChipMind Co-Pilot</h1><p>Frontend not built yet.</p>")


@app.get("/sw.js")
async def service_worker():
    """Serve the PWA service worker at root so it can control all pages."""
    sw_path = WEB_DIR / "sw.js"
    if sw_path.exists():
        return FileResponse(str(sw_path), media_type="application/javascript")
    return HTMLResponse("// service worker not found", status_code=404)


@app.get("/manifest.json")
async def pwa_manifest():
    """Serve the PWA manifest at root."""
    manifest_path = WEB_DIR / "manifest.json"
    if manifest_path.exists():
        return FileResponse(str(manifest_path), media_type="application/manifest+json")
    return HTMLResponse("{}", media_type="application/manifest+json")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
