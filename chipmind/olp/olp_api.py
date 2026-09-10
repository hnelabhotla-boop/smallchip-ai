"""
olp_api.py — The OLP HTTP endpoints.

Three endpoints:
- POST /api/olp/log_drag — log a drag-to-re-place (verified experts only)
- POST /api/olp/predict_drag — predict the next best move (any user)
- GET  /api/olp/stats — drag counts, model status, expert count
- POST /api/olp/verify_expert — verify a user as expert by uploading a DEF
- POST /api/olp/train — retrain the OLP model on logged drags

This is a FastAPI router — mount it under the main app.
"""

import json
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from .olp_db import DragLog, init_db, is_verified_expert, count_drags
from .olp_model import OLPMovePredictor, MODEL_PATH, extract_features
from .olp_bootstrap import build_ispd_style_design
from .olp_verify import verify_expert_from_def, detect_industry_tool, count_cells


router = APIRouter(prefix="/api/olp", tags=["olp"])

# Global model instance (lazy-loaded)
_model: Optional[OLPMovePredictor] = None


def get_model() -> OLPMovePredictor:
    global _model
    if _model is None:
        _model = OLPMovePredictor()
        _model.load()
    return _model


@router.get("/stats")
async def olp_stats():
    """OLP system stats: drag counts, model status, expert count."""
    init_db()
    from .olp_db import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM expert_verification")
    n_experts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM drag_log WHERE is_synthetic = 0")
    n_real_drags = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM drag_log WHERE is_synthetic = 1")
    n_synth_drags = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM drag_log")
    n_total = c.fetchone()[0]
    conn.close()
    model = get_model()
    return {
        "n_experts_verified": n_experts,
        "n_real_drags": n_real_drags,
        "n_synthetic_drags": n_synth_drags,
        "n_total_drags": n_total,
        "model_trained": model.is_trained,
        "model_params": model.n_params,
        "model_path": str(MODEL_PATH),
    }


@router.post("/log_drag")
async def log_drag(req: dict):
    """Log a drag-to-re-place event. Verified experts only.

    Body: {
        "user_id": str,
        "chip_id": str,
        "cell_id": str,
        "before": [x, y],
        "after": [x, y],
        "priority": {"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0},
        "hpwl_before": float,
        "hpwl_after": float,
        "features": [32 floats] (optional)
    }
    """
    user_id = req.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id required")
    if not is_verified_expert(user_id):
        raise HTTPException(
            403,
            f"User '{user_id}' is not a verified expert. Upload an industry DEF to /api/olp/verify_expert first.",
        )
    init_db()
    log = DragLog(
        user_id=user_id,
        chip_id=req.get("chip_id", "unknown"),
        cell_id=req.get("cell_id", "unknown"),
        before_x=float(req["before"][0]),
        before_y=float(req["before"][1]),
        after_x=float(req["after"][0]),
        after_y=float(req["after"][1]),
        priority=req.get("priority", {"hpwl": 1.0, "congestion": 0, "thermal": 0, "timing": 0}),
        hpwl_before=float(req.get("hpwl_before", 0)),
        hpwl_after=float(req.get("hpwl_after", 0)),
        features=req.get("features"),
        is_synthetic=False,
    )
    log.save()
    return {"ok": True, "log_id": log.timestamp}


@router.post("/predict_drag")
async def predict_drag(req: dict):
    """Predict the next best move for a cell. Any user (real or not).

    Body: {
        "cell_id": str,
        "features": [32 floats] — feature vector for the cell
    }
    Returns: {"dx": float, "dy": float, "model_trained": bool}
    """
    features = req.get("features")
    if not features or len(features) != 32:
        raise HTTPException(400, f"features must be a list of 32 floats (got {len(features) if features else 0})")
    import numpy as np
    model = get_model()
    f = np.array(features, dtype=np.float32)
    if model.is_trained:
        pred = model.predict(f)
    else:
        # Untrained: return zero move with explanation
        pred = np.zeros(2, dtype=np.float32)
    return {
        "dx": float(pred[0]),
        "dy": float(pred[1]),
        "model_trained": model.is_trained,
        "model_params": model.n_params,
        "note": "Model is bootstrapped from V3 GAT synthetic drags. Will improve with real expert drags." if not model.is_trained else None,
    }


@router.post("/verify_expert")
async def verify_expert(
    user_id: str = Form(...),
    def_file: UploadFile = File(...),
):
    """Verify a user as expert by uploading a real industry DEF.

    Form fields:
      - user_id: their chosen ID
      - def_file: a .def file output by OpenROAD, Cadence, Synopsys, KLayout, or Yosys
    """
    init_db()
    # Save the uploaded file temporarily
    tmp = Path(f"/tmp/verify_{user_id}_{int(time.time())}.def")
    with open(tmp, "wb") as f:
        f.write(await def_file.read())
    result = verify_expert_from_def(user_id, str(tmp))
    if result.get("verified"):
        result["message"] = (
            f"Welcome, expert. Your DEF was generated by {result['tool']} "
            f"with {result['cells']:,} cells. Your future drags will train the OLP model."
        )
    return result


@router.post("/train")
async def train_olp(req: dict = None):
    """Retrain the OLP model on all logged drags (synthetic + real)."""
    init_db()
    from .olp_db import get_db
    import numpy as np
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT features_json, before_x, before_y, after_x, after_y FROM drag_log"
    )
    rows = c.fetchall()
    conn.close()
    if not rows:
        raise HTTPException(400, "No drags logged yet. Bootstrap from V3 or wait for expert drags.")
    X_list = []
    y_list = []
    for r in rows:
        try:
            features = json.loads(r["features_json"])
        except Exception:
            continue
        if len(features) != 32:
            continue
        X_list.append(features)
        y_list.append([r["after_x"] - r["before_x"], r["after_y"] - r["before_y"]])
    if len(X_list) < 50:
        raise HTTPException(400, f"Need at least 50 drags; have {len(X_list)}")
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    model = get_model()
    losses = model.train(X, y, verbose=True)
    model.save()
    return {
        "ok": True,
        "n_training_examples": len(X_list),
        "final_loss": float(losses[-1]),
        "model_params": model.n_params,
        "model_path": str(MODEL_PATH),
    }


@router.post("/bootstrap")
async def bootstrap(n_designs: int = 5, n_cells: int = 500, drags_per_design: int = 200):
    """Generate synthetic expert drags from V3 GAT and train the model.

    This is the cold-start. Real experts can later contribute their own drags.
    """
    from .olp_bootstrap import bootstrap_from_v3
    examples = bootstrap_from_v3(
        n_designs=n_designs, n_cells=n_cells, drags_per_design=drags_per_design
    )
    # Auto-train
    init_db()
    import numpy as np
    X = np.array([e["features"] for e in examples], dtype=np.float32)
    y = np.array([e["target_dxdy"] for e in examples], dtype=np.float32)
    model = get_model()
    losses = model.train(X, y, verbose=True)
    model.save()
    return {
        "ok": True,
        "n_synthetic_drags_generated": len(examples),
        "final_loss": float(losses[-1]),
        "model_path": str(MODEL_PATH),
    }
