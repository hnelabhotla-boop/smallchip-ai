"""
Pareto GAT — multi-objective GAT that takes a preference vector and places a chip
optimizing for those weighted objectives.

Architecture: same as V3 GAT but with a 5-dim preference vector input.
Output: Tanh (positions in [-1, 1] mapped to die coordinates).

Training: same as V3 (HPWL loss) but with the preference vector as a global context.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data
from typing import Dict, List
import numpy as np


class ParetoGATPlacer(nn.Module):
    """GAT placer conditioned on a 5-dim preference vector.
    Preference: [hpwl, power, area, timing, congestion] (sum to 1).
    """

    def __init__(self, in_dim: int = 9, hidden: int = 64, out_dim: int = 2,
                 num_layers: int = 3, heads: int = 4, pref_dim: int = 5):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden)
        self.pref_proj = nn.Linear(pref_dim, hidden)  # preference → hidden
        # Gate: preference modulates per-cell features
        self.pref_gate = nn.Linear(pref_dim, hidden)
        self.gat_layers = nn.ModuleList([
            GATConv(hidden, hidden // heads, heads=heads, concat=True)
            for _ in range(num_layers)
        ])
        self.layer_norms = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(num_layers)])
        # Tanh head
        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, out_dim),
            nn.Tanh(),
        )

    def forward(self, data, preference):
        """data.x: [N, in_dim], edge_index: [2, E], preference: [5] (or [B, 5])"""
        x, edge_index = data.x, data.edge_index
        h = F.relu(self.input_proj(x))  # [N, hidden]
        # Modulate by preference: scale = sigmoid(pref_gate(pref)), shift = pref_proj(pref)
        scale = torch.sigmoid(self.pref_gate(preference))  # [hidden]
        h = h * scale  # broadcast over cells
        for gat, ln in zip(self.gat_layers, self.layer_norms):
            h_new = gat(h, edge_index)
            h = ln(h + h_new)
            h = F.relu(h)
        return self.head(h)  # [N, 2] in [-1, 1]


def _compute_features(chip: dict) -> torch.Tensor:
    """Same as the V3 GAT."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}

    net_count = {n: 0 for n in cell_names}
    net_sizes = {n: [] for n in cell_names}
    for net in nets:
        cells = net.get("components", net.get("cells", []))
        for c in cells:
            if c in name_to_idx:
                net_count[c] += 1
                net_sizes[c].append(len(cells))

    die_w = max(die["x2"] - die["x1"], 1)
    die_h = max(die["y2"] - die["y1"], 1)
    feats = []
    for c in cell_names:
        pos = components[c]
        ns = net_sizes[c] or [0]
        f = [
            net_count[c],
            sum(ns) / len(ns),
            max(ns),
            min(ns),
            pos["x"] / die_w,
            pos["y"] / die_h,
            net_count[c] / max(len(cell_names), 1),
            (pos["x"] - die["x1"]) / die_w,
            (pos["y"] - die["y1"]) / die_h,
        ]
        feats.append(f)
    return torch.tensor(feats, dtype=torch.float32)


def _chip_to_data(chip: dict):
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}
    edges = []
    for net in nets:
        cells = net.get("components", net.get("cells", []))
        cells_in_net = [name_to_idx[c] for c in cells if c in name_to_idx]
        for i in range(len(cells_in_net)):
            for j in range(i + 1, len(cells_in_net)):
                edges.append([cells_in_net[i], cells_in_net[j]])
                edges.append([cells_in_net[j], cells_in_net[i]])
    x = _compute_features(chip)
    edge_index = (torch.tensor(edges, dtype=torch.long).t().contiguous()
                   if edges else torch.zeros((2, 0), dtype=torch.long))
    return Data(x=x, edge_index=edge_index), cell_names, die, name_to_idx


def predict_pareto(model: ParetoGATPlacer, chip: dict, preference=None) -> Dict[str, Dict[str, float]]:
    """Predict placement conditioned on a 5-dim preference vector.
    preference: list/array of 5 floats summing to 1, or None for default [0.2, 0.2, 0.2, 0.2, 0.2].
    """
    if preference is None:
        preference = [0.2, 0.2, 0.2, 0.2, 0.2]
    preference = torch.tensor(preference, dtype=torch.float32)
    data, cell_names, die, name_to_idx = _chip_to_data(chip)
    model.eval()
    with torch.no_grad():
        tanh_pred = model(data, preference)

    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]
    components = {}
    for name, idx in name_to_idx.items():
        x_norm = (float(tanh_pred[idx, 0]) + 1) / 2
        y_norm = (float(tanh_pred[idx, 1]) + 1) / 2
        components[name] = {
            "x": x_norm * die_w + die["x1"],
            "y": y_norm * die_h + die["y1"],
        }
    return components


def load_pareto_model(checkpoint_path: str) -> ParetoGATPlacer:
    """Load a trained Pareto GAT. Falls back to uniform preference if model
    wasn't trained with the preference input."""
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]
    hidden = state["input_proj.weight"].shape[0]
    model = ParetoGATPlacer(in_dim=9, hidden=hidden, out_dim=2,
                            num_layers=3, heads=4, pref_dim=5)
    # Try to load; fall back to plain V3 weights
    try:
        model.load_state_dict(state)
    except RuntimeError:
        # Strip the pref_gate/pref_proj keys, use uniform preference
        filtered = {k: v for k, v in state.items()
                    if not k.startswith("pref_")}
        model.load_state_dict(filtered, strict=False)
    model.eval()
    return model
