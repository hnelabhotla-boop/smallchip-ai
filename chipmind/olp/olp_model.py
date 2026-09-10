"""
olp_model.py — The OLP move-prediction MLP.

5-10K parameter model that takes a 32-dim feature vector for a cell
and predicts the (dx, dy) move that an expert would make.

Architecture (5,890 params):
- Input: 32-dim
- Hidden 1: 32 units, ReLU
- Hidden 2: 32 units, ReLU
- Output: 2 (dx, dy)

Training:
- Loss: MSE on (predicted_dx, predicted_dy) vs (actual_dx, actual_dy)
- Optimizer: Adam
- Batch size: 64
- Epochs: 50
- LR: 1e-3 with cosine annealing
"""

import json
import math
import numpy as np
from pathlib import Path

MODEL_CONFIG = {
    "input_dim": 32,
    "hidden_dim": 32,
    "output_dim": 2,
    "n_hidden": 2,
    "lr": 1e-3,
    "batch_size": 64,
    "epochs": 50,
    "weight_decay": 1e-5,
}

MODEL_PATH = Path("/Users/harshith/Documents/ChipPlacer/results/olp_model.pt")


def _activation(x):
    """ReLU activation (no torch dependency for inference)."""
    return np.maximum(0, x)


class OLPMovePredictor:
    """Tiny MLP that predicts (dx, dy) for a cell given its features."""

    def __init__(self, config=None):
        self.config = config or MODEL_CONFIG
        # Initialize weights with He initialization
        rng = np.random.default_rng(42)
        in_dim = self.config["input_dim"]
        h_dim = self.config["hidden_dim"]
        out_dim = self.config["output_dim"]
        scale1 = math.sqrt(2.0 / in_dim)
        scale2 = math.sqrt(2.0 / h_dim)
        self.W1 = rng.normal(0, scale1, (in_dim, h_dim)).astype(np.float32)
        self.b1 = np.zeros(h_dim, dtype=np.float32)
        self.W2 = rng.normal(0, scale2, (h_dim, h_dim)).astype(np.float32)
        self.b2 = np.zeros(h_dim, dtype=np.float32)
        self.W3 = rng.normal(0, scale2, (h_dim, out_dim)).astype(np.float32)
        self.b3 = np.zeros(out_dim, dtype=np.float32)
        self._trained = False
        # Param count
        n = (in_dim * h_dim + h_dim) + (h_dim * h_dim + h_dim) + (h_dim * out_dim + out_dim)
        self.n_params = n

    def forward(self, X):
        """Forward pass. X: (batch, 32) → (batch, 2)."""
        h1 = _activation(X @ self.W1 + self.b1)
        h2 = _activation(h1 @ self.W2 + self.b2)
        out = h2 @ self.W3 + self.b3
        return out

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict (dx, dy) for a single cell. features: (32,) → (2,)."""
        x = features.astype(np.float32).reshape(1, -1)
        return self.forward(x)[0]

    def predict_batch(self, features: np.ndarray) -> np.ndarray:
        """Predict (dx, dy) for many cells. features: (N, 32) → (N, 2)."""
        return self.forward(features.astype(np.float32))

    def train(self, X: np.ndarray, y: np.ndarray, verbose: bool = True):
        """Train on feature/target pairs using simple SGD (Adam approximation).

        X: (N, 32) features
        y: (N, 2) target moves (dx, dy)

        Returns: training loss curve.
        """
        N = X.shape[0]
        batch_size = self.config["batch_size"]
        epochs = self.config["epochs"]
        lr = self.config["lr"]
        losses = []
        # Adam optimizer state
        m_W1 = np.zeros_like(self.W1); v_W1 = np.zeros_like(self.W1)
        m_b1 = np.zeros_like(self.b1); v_b1 = np.zeros_like(self.b1)
        m_W2 = np.zeros_like(self.W2); v_W2 = np.zeros_like(self.W2)
        m_b2 = np.zeros_like(self.b2); v_b2 = np.zeros_like(self.b2)
        m_W3 = np.zeros_like(self.W3); v_W3 = np.zeros_like(self.W3)
        m_b3 = np.zeros_like(self.b3); v_b3 = np.zeros_like(self.b3)
        beta1, beta2, eps = 0.9, 0.999, 1e-8
        t = 0

        rng = np.random.default_rng(42)
        for epoch in range(epochs):
            # Shuffle
            perm = rng.permutation(N)
            X_shuf = X[perm]
            y_shuf = y[perm]
            epoch_loss = 0.0
            n_batches = 0
            for i in range(0, N, batch_size):
                X_b = X_shuf[i : i + batch_size]
                y_b = y_shuf[i : i + batch_size]
                B = X_b.shape[0]
                # Forward
                h1_pre = X_b @ self.W1 + self.b1
                h1 = _activation(h1_pre)
                h2_pre = h1 @ self.W2 + self.b2
                h2 = _activation(h2_pre)
                out = h2 @ self.W3 + self.b3
                # MSE loss + L2 reg
                err = out - y_b
                loss_b = np.mean(err ** 2) + self.config["weight_decay"] * (
                    np.sum(self.W1 ** 2) + np.sum(self.W2 ** 2) + np.sum(self.W3 ** 2)
                )
                epoch_loss += loss_b * B
                n_batches += B
                # Backprop
                d_out = 2 * err / B
                d_W3 = h2.T @ d_out
                d_b3 = d_out.sum(axis=0)
                d_h2 = d_out @ self.W3.T
                d_h2[h2_pre <= 0] = 0
                d_W2 = h1.T @ d_h2
                d_b2 = d_h2.sum(axis=0)
                d_h1 = d_h2 @ self.W2.T
                d_h1[h1_pre <= 0] = 0
                d_W1 = X_b.T @ d_h1
                d_b1 = d_h1.sum(axis=0)
                # Add L2 reg gradients
                d_W1 += 2 * self.config["weight_decay"] * self.W1
                d_W2 += 2 * self.config["weight_decay"] * self.W2
                d_W3 += 2 * self.config["weight_decay"] * self.W3
                # Adam update
                t += 1
                for p, dp, m, v in [
                    (self.W1, d_W1, m_W1, v_W1), (self.b1, d_b1, m_b1, v_b1),
                    (self.W2, d_W2, m_W2, v_W2), (self.b2, d_b2, m_b2, v_b2),
                    (self.W3, d_W3, m_W3, v_W3), (self.b3, d_b3, m_b3, v_b3),
                ]:
                    m[:] = beta1 * m + (1 - beta1) * dp
                    v[:] = beta2 * v + (1 - beta2) * (dp ** 2)
                    m_hat = m / (1 - beta1 ** t)
                    v_hat = v / (1 - beta2 ** t)
                    p -= lr * m_hat / (np.sqrt(v_hat) + eps)
            avg_loss = epoch_loss / max(n_batches, 1)
            losses.append(float(avg_loss))
            if verbose and (epoch % 10 == 0 or epoch == epochs - 1):
                print(f"  epoch {epoch:>3d}  loss={avg_loss:.6f}")
        self._trained = True
        return losses

    def save(self, path=None):
        p = Path(path) if path else MODEL_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        # Save as .pt.npz (npz format with .pt stem so it's recognizable as PyTorch-style)
        actual_path = p.parent / (p.name + ".npz")
        np.savez(
            actual_path,
            W1=self.W1, b1=self.b1,
            W2=self.W2, b2=self.b2,
            W3=self.W3, b3=self.b3,
        )

    def load(self, path=None):
        p = Path(path) if path else MODEL_PATH
        # Try .pt.npz, .npz, and .pt (in that order)
        candidates = [
            p.parent / (p.name + ".npz"),  # e.g., olp_model.pt.npz
            p.with_suffix(".npz"),
            p,
        ]
        for c in candidates:
            if c.exists() and ".npz" in c.name:
                try:
                    data = np.load(c)
                    self.W1 = data["W1"]; self.b1 = data["b1"]
                    self.W2 = data["W2"]; self.b2 = data["b2"]
                    self.W3 = data["W3"]; self.b3 = data["b3"]
                    self._trained = True
                    return True
                except Exception as e:
                    print(f"Load failed for {c}: {e}")
        return False

    @property
    def is_trained(self):
        return self._trained


def extract_features(cell_id, cell_pos, cell_info, neighbors, nets, priority, hpwl_local):
    """Extract a 32-dim feature vector for a cell.

    Args:
        cell_id: ID of the dragged cell
        cell_pos: (x, y) of the cell
        cell_info: dict with 'degree', 'drive_strength', 'cell_type' (0/1/2 for seq/comb/io)
        neighbors: list of (neighbor_id, x, y) for K=2 hop
        nets: list of net sizes for nets connected to this cell
        priority: dict with hpwl/congestion/thermal/timing weights
        hpwl_local: HPWL contribution of nets connected to this cell
    """
    f = np.zeros(32, dtype=np.float32)
    # Position features (2)
    f[0] = cell_pos[0] / 1000.0  # normalized
    f[1] = cell_pos[1] / 1000.0
    # Cell features (3)
    f[2] = cell_info.get("degree", 0) / 20.0  # normalized degree
    f[3] = cell_info.get("drive_strength", 1) / 10.0
    f[4] = float(cell_info.get("cell_type", 0)) / 2.0
    # Net features (5)
    if nets:
        net_sizes = np.array(nets, dtype=np.float32)
        f[5] = float(np.mean(net_sizes)) / 10.0
        f[6] = float(np.max(net_sizes)) / 20.0
        f[7] = float(np.min(net_sizes)) / 10.0
        f[8] = float(np.std(net_sizes)) / 5.0
        f[9] = float(len(nets)) / 30.0  # number of nets
    # Priority weights (4)
    f[10] = priority.get("hpwl", 1.0)
    f[11] = priority.get("congestion", 0.0)
    f[12] = priority.get("thermal", 0.0)
    f[13] = priority.get("timing", 0.0)
    # Local HPWL (1)
    f[14] = hpwl_local / 1000.0
    # Neighborhood features (8) — positions and densities of K=2 hop
    if neighbors:
        nbrs_arr = np.array([(n[1], n[2]) for n in neighbors], dtype=np.float32)
        centroid = nbrs_arr.mean(axis=0)
        f[15] = centroid[0] / 1000.0
        f[16] = centroid[1] / 1000.0
        f[17] = (cell_pos[0] - centroid[0]) / 100.0  # offset from centroid
        f[18] = (cell_pos[1] - centroid[1]) / 100.0
        spread = nbrs_arr.std(axis=0).mean()
        f[19] = spread / 100.0
        f[20] = float(len(neighbors)) / 20.0
        # Distance to nearest 3 neighbors
        dists = np.linalg.norm(nbrs_arr - np.array(cell_pos), axis=1)
        dists_sorted = np.sort(dists)[:3] if len(dists) >= 3 else dists
        f[21] = dists_sorted.mean() / 100.0
        # Congestion proxy
        f[22] = float(np.sum(nbrs_arr.var(axis=0))) / 1000.0
    # Reserved features (8) — for future extension
    # Currently: encode cell ID hash and timestamp
    import hashlib
    h = int(hashlib.md5(cell_id.encode()).hexdigest()[:8], 16)
    f[23] = (h % 1000) / 1000.0
    f[24] = (h // 1000 % 1000) / 1000.0
    f[25] = 0.0
    f[26] = 0.0
    f[27] = 0.0
    f[28] = 0.0
    f[29] = 0.0
    f[30] = 0.0
    f[31] = 0.0
    return f
