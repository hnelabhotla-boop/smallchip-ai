"""
train_multiobj_predictors.py — Train 4 ML models for multi-objective prediction
  - TimingPredictor: predicts critical path delay
  - PowerPredictor: predicts dynamic power
  - AreaPredictor: predicts total area
  - CongestionPredictor: predicts max routing congestion

Uses small MLPs since features are per-chip (8 features, 1 target).
"""

import sys
import json
import time
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


class MetricPredictor(nn.Module):
    """Small MLP for predicting a single chip-level metric."""

    def __init__(self, in_dim: int = 9, hidden: int = 64, out_dim: int = 1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )

    def forward(self, x):
        return self.net(x)


def normalize_features(features: dict) -> np.ndarray:
    """Convert feature dict to normalized numpy array."""
    # Order matters - keep consistent
    keys = ["n_cells", "n_nets", "avg_net_size", "max_net_size",
            "avg_cell_degree", "max_cell_degree", "die_area", "die_aspect", "hpwl"]
    return np.array([features[k] for k in keys], dtype=np.float32)


def normalize_target(values: np.ndarray) -> tuple:
    """Normalize targets to [0, 1] range. Returns (normalized, min, max)."""
    vmin, vmax = values.min(), values.max()
    if vmax > vmin:
        normalized = (values - vmin) / (vmax - vmin)
    else:
        normalized = np.zeros_like(values)
    return normalized.astype(np.float32), float(vmin), float(vmax)


def denormalize_target(normalized: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    """Convert normalized back to original scale."""
    if vmax > vmin:
        return normalized * (vmax - vmin) + vmin
    return np.full_like(normalized, vmin)


def train_one_predictor(name: str, data: list, target_key: str, epochs: int = 200, lr: float = 1e-3):
    """Train a single metric predictor."""
    print(f"\n--- Training {name} (target: {target_key}) ---")

    # Prepare data
    X = np.array([normalize_features(d["features"]) for d in data])
    y = np.array([d["metrics"][target_key] for d in data], dtype=np.float32)
    y_norm, y_min, y_max = normalize_target(y)

    # Normalize features (z-score)
    x_mean = X.mean(axis=0)
    x_std = X.std(axis=0) + 1e-6
    X_norm = (X - x_mean) / x_std

    X_t = torch.tensor(X_norm, dtype=torch.float32)
    y_t = torch.tensor(y_norm, dtype=torch.float32).unsqueeze(1)

    model = MetricPredictor(in_dim=9, hidden=64, out_dim=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    print(f"  Model: {sum(p.numel() for p in model.parameters()):,} params")
    print(f"  Data: {len(data)} samples, target range: [{y_min:.2f}, {y_max:.2f}]")

    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Training: {epochs} epochs")

    start = time.time()
    for epoch in range(epochs):
        pred = model(X_t)
        loss = F.mse_loss(pred, y_t)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:>3}/{epochs}  loss = {loss.item():.6f}", flush=True)

    elapsed = time.time() - start
    print(f"  Done in {elapsed:.1f}s. Final loss: {loss.item():.6f}")

    return model, (x_mean, x_std), (y_min, y_max)


def predict_metric(model, features: dict, x_stats, y_stats) -> float:
    """Predict a single metric for a new chip."""
    x_mean, x_std = x_stats
    y_min, y_max = y_stats

    x = normalize_features(features)
    x_norm = (x - x_mean) / x_std
    x_t = torch.tensor(x_norm, dtype=torch.float32).unsqueeze(0)

    model.eval()
    with torch.no_grad():
        pred_norm = model(x_t)
    pred = denormalize_target(pred_norm.numpy().flatten(), y_min, y_max)
    return float(pred[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/multiobj_training_data.json")
    parser.add_argument("--save-dir", default="models")
    parser.add_argument("--epochs", type=int, default=200)
    args = parser.parse_args()

    print("=" * 60)
    print("  ChipMind — Multi-objective Predictor Training")
    print("=" * 60)

    with open(args.data) as f:
        data = json.load(f)
    print(f"\nLoaded {len(data)} samples")

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Train 4 predictors
    targets = [
        ("TimingPredictor", "timing_ps"),
        ("PowerPredictor", "power_mw"),
        ("AreaPredictor", "area"),
        ("CongestionPredictor", "max_congestion"),
    ]

    stats = {}
    for name, key in targets:
        model, x_stats, y_stats = train_one_predictor(name, data, key, epochs=args.epochs)
        # Save
        torch.save({
            "model": model.state_dict(),
            "x_stats": x_stats,
            "y_stats": y_stats,
        }, save_dir / f"{name.lower().replace('predictor', '_model')}.pt")
        stats[name] = (model, x_stats, y_stats)
        print(f"  Saved: {name.lower().replace('predictor', '_model')}.pt")

    # Save combined stats file
    combined = {
        name: {
            "x_mean": [float(x) for x in stats[name][1][0]],
            "x_std": [float(x) for x in stats[name][1][1]],
            "y_min": float(stats[name][2][0]),
            "y_max": float(stats[name][2][1]),
        }
        for name in [t[0] for t in targets]
    }
    with open(save_dir / "multiobj_stats.json", "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  All 4 predictors trained and saved to {save_dir}/")
    print(f"  Ready for inference!")


if __name__ == "__main__":
    main()
