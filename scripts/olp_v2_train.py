#!/usr/bin/env python3
"""
olp_v2_train.py — Retrain OLP on the centroid-expert drags.

Loads the centroid-expert drags from results/olp_centroid_drags.json
and trains the OLP model. Then runs the iterative ablation.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from chipmind.olp.olp_model import OLPMovePredictor


def train_on_centroid_drags():
    drag_file = Path("results/olp_centroid_drags.json")
    if not drag_file.exists():
        print(f"Run olp_bootstrap_v2.py first")
        return
    with open(drag_file) as f:
        examples = json.load(f)
    X = np.array([e["features"] for e in examples], dtype=np.float32)
    y = np.array([e["target_dxdy"] for e in examples], dtype=np.float32)
    print(f"Training OLP on {len(examples)} centroid-expert drags")
    print(f"  X shape: {X.shape}, y shape: {y.shape}")
    print(f"  y mean: {y.mean(axis=0)}, y std: {y.std(axis=0)}")

    model = OLPMovePredictor()
    losses = model.train(X, y, verbose=True)
    model.save()
    print(f"\nFinal loss: {losses[-1]:.4f}")
    print(f"Saved to {model_path if False else 'results/olp_model.pt.npz'}")
    return model


if __name__ == "__main__":
    train_on_centroid_drags()
