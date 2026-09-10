"""
OLP — Online Learning Placement.

The first placement algorithm that learns from real expert interactions.
Every drag-to-re-place a verified expert does becomes training data.
A small MLP learns to predict where an expert would drag each cell.
Over time, the placer improves.

Three components:
1. olp.db (SQLite) — drag log storage
2. olp_model.py — the 5-10K param MLP
3. olp_api.py — the /api/log_drag and /api/predict_drag endpoints
4. olp_bootstrap.py — generate synthetic expert drags from V3 GAT
5. olp_verify.py — expert verification via industry DEF upload
"""

# Re-exports for convenience
from .olp_db import DragLog, ExpertVerification, get_db, init_db
from .olp_model import OLPMovePredictor, MODEL_CONFIG
from .olp_bootstrap import bootstrap_from_v3, generate_synthetic_expert_drags
from .olp_verify import verify_expert_from_def, is_verified_expert
