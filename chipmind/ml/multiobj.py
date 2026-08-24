"""
chipmind/ml/multiobj.py — Multi-objective quality predictor.
Takes a chip design and placement, predicts 5 quality metrics:
  - HPWL (wirelength)
  - Timing (estimated critical path delay)
  - Power (estimated dynamic power)
  - Area (estimated silicon area)
  - Congestion (estimated routing density)
"""

import sys
import json
import numpy as np
import torch
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))
from train_multiobj_predictors import (
    MetricPredictor, normalize_features, denormalize_target
)
from chipmind.core import compute_hpwl
from chipmind.core.fast_hpwl import FastHPWL
from generate_multiobj_data import (
    estimate_timing, estimate_power, estimate_congestion, compute_area
)


class MultiObjectivePredictor:
    """
    Predicts 5 quality metrics for a chip design + placement.
    Uses 4 trained ML models for timing/power/area/congestion.
    HPWL computed directly.
    """

    def __init__(self, models_dir: str = None):
        if models_dir is None:
            # Path: chipmind/ml/multiobj.py -> chipmind/ml/ -> chipmind/ -> project_root/
            models_dir = Path(__file__).parent.parent.parent / "models"
        self.models_dir = Path(models_dir)

        # Load 4 ML models
        self.timing_model, self.timing_stats = self._load("timing_model.pt")
        self.power_model, self.power_stats = self._load("power_model.pt")
        self.area_model, self.area_stats = self._load("area_model.pt")
        self.congestion_model, self.congestion_stats = self._load("congestion_model.pt")

        # Build fast HPWL calculator on demand (cached per chip)

    def _load(self, name: str):
        path = self.models_dir / name
        if not path.exists():
            print(f"Warning: model {name} not found at {path}")
            return None, None
        ckpt = torch.load(path, map_location="cpu")
        model = MetricPredictor(in_dim=9, hidden=64, out_dim=1)
        model.load_state_dict(ckpt["model"])
        model.eval()
        x_stats = (np.array(ckpt["x_stats"][0]), np.array(ckpt["x_stats"][1]))
        y_stats = (ckpt["y_stats"][0], ckpt["y_stats"][1])
        return model, (x_stats, y_stats)

    def _compute_features(self, chip: dict) -> dict:
        """Compute the 9 features for a chip."""
        components = chip["components"]
        nets = chip["nets"]
        die = chip["die"]

        cell_nets = {}
        net_sizes = []
        for net in nets:
            cells = [c for c in net["components"] if c in components]
            if len(cells) >= 2:
                net_sizes.append(len(cells))
                for c in cells:
                    cell_nets[c] = cell_nets.get(c, 0) + 1

        # HPWL is part of features so models can use placement quality
        hpwl = compute_hpwl(chip)["total_hpwl"]

        return {
            "n_cells": len(components),
            "n_nets": len(nets),
            "avg_net_size": float(np.mean(net_sizes)) if net_sizes else 0.0,
            "max_net_size": int(max(net_sizes)) if net_sizes else 0,
            "avg_cell_degree": float(np.mean(list(cell_nets.values()))) if cell_nets else 0.0,
            "max_cell_degree": max(cell_nets.values()) if cell_nets else 0,
            "die_area": float((die["x2"] - die["x1"]) * (die["y2"] - die["y1"])),
            "die_aspect": float((die["x2"] - die["x1"]) / max(1, die["y2"] - die["y1"])),
            "hpwl": float(hpwl),
        }

    def _predict_metric(self, model, features, stats):
        """Predict a single metric using one of the trained models."""
        if model is None or stats is None:
            return None
        x_stats, y_stats = stats

        x = normalize_features(features)
        x_norm = (x - x_stats[0]) / x_stats[1]
        x_t = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            pred_norm = model(x_t)
        pred = denormalize_target(pred_norm.numpy().flatten(), y_stats[0], y_stats[1])
        return float(pred[0])

    def predict(self, chip: dict, components: dict = None) -> dict:
        """
        Predict all 5 quality metrics for a chip design.

        Args:
            chip: chip dict with die, components, nets
            components: optional override for component positions (for predicted placements)

        Returns:
            dict with hpwl, timing_ps, power_mw, area, max_congestion
        """
        # If components override given, use it
        if components is not None:
            eval_chip = {**chip, "components": components}
        else:
            eval_chip = chip

        # 1. HPWL: compute directly (most accurate)
        hpwl = compute_hpwl(eval_chip)["total_hpwl"]

        # 2. Compute features for ML models
        features = self._compute_features(eval_chip)

        # 3. ML predictions (clamp to non-negative)
        timing = self._predict_metric(self.timing_model, features, self.timing_stats)
        power = self._predict_metric(self.power_model, features, self.power_stats)
        area = self._predict_metric(self.area_model, features, self.area_stats)
        congestion = self._predict_metric(self.congestion_model, features, self.congestion_stats)

        return {
            "hpwl": float(hpwl),
            "timing_ps": max(0.0, float(timing)) if timing else None,
            "power_mw": max(0.0, float(power)) if power else None,
            "area": max(0.0, float(area)) if area else None,
            "max_congestion": max(0.0, float(congestion)) if congestion else None,
        }

    def predict_estimate(self, chip: dict) -> dict:
        """
        Quick prediction based on chip features only (no actual placement).
        Used for "what-if" before placing.
        """
        features = self._compute_features(chip)
        return {
            "timing_ps": self._predict_metric(self.timing_model, features, self.timing_stats),
            "power_mw": self._predict_metric(self.power_model, features, self.power_stats),
            "area": self._predict_metric(self.area_model, features, self.area_stats),
            "max_congestion": self._predict_metric(self.congestion_model, features, self.congestion_stats),
        }
