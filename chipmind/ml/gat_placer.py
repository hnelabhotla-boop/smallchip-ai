"""
GAT-based pre-trained placer.

This is the AlphaChip-inspired ML approach. We pre-train a Graph Attention
Network on real chip placements (ISPD 2005 benchmark suite), then apply
the trained model to predict placements for new designs.

Two architectures are supported:
- "v2": 3 layers × 64 hidden × 4 heads (18K params) — current default
- "238k": 4 layers × 128 hidden × 4 heads (94K params) — best on benchmarks,
          requires Tanh(scale=0.5) output activation
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data
from typing import Dict
import numpy as np


class GATPlacer(nn.Module):
    """Graph Attention Network for chip placement prediction."""

    def __init__(self, in_dim: int = 9, hidden: int = 64, out_dim: int = 2,
                 num_layers: int = 3, heads: int = 4, head_act: str = "relu"):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden)
        self.gat_layers = nn.ModuleList([
            GATConv(hidden, hidden // heads, heads=heads, concat=True)
            for _ in range(num_layers)
        ])
        self.layer_norms = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(num_layers)])

        # Head architecture depends on hidden size
        if hidden >= 128:
            # Best (94K) model: 128 -> 128 -> 64 -> 2 with GELU
            self.head = nn.Sequential(
                nn.Linear(hidden, hidden),
                nn.GELU(),
                nn.Linear(hidden, hidden // 2),
                nn.GELU(),
                nn.Linear(hidden // 2, out_dim),
            )
        else:
            # Default: hidden -> hidden -> out_dim with ReLU
            act = nn.ReLU() if head_act == "relu" else nn.GELU()
            self.head = nn.Sequential(
                nn.Linear(hidden, hidden),
                act,
                nn.Linear(hidden, out_dim),
                nn.Sigmoid(),
            )

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        h = F.relu(self.input_proj(x))
        for gat, ln in zip(self.gat_layers, self.layer_norms):
            h_new = gat(h, edge_index)
            h = ln(h + h_new)
            h = F.relu(h)
        return self.head(h)


class GATPlacer(nn.Module):
    """Graph Attention Network for chip placement prediction."""

    def __init__(self, in_dim: int = 9, hidden: int = 64, out_dim: int = 2,
                 num_layers: int = 3, heads: int = 4, head_act: str = "relu"):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden)
        self.gat_layers = nn.ModuleList([
            GATConv(hidden, hidden // heads, heads=heads, concat=True)
            for _ in range(num_layers)
        ])
        self.layer_norms = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(num_layers)])

        # Head architecture: depends on hidden size
        if hidden >= 128:
            # 94K model: 128 -> 128 -> 64 -> 2 with GELU
            self.head = nn.Sequential(
                nn.Linear(hidden, hidden),
                nn.GELU(),
                nn.Linear(hidden, hidden // 2),
                nn.GELU(),
                nn.Linear(hidden // 2, out_dim),
            )
        else:
            # Default: hidden -> hidden -> out_dim with ReLU/Sigmoid
            act = nn.ReLU() if head_act == "relu" else nn.GELU()
            self.head = nn.Sequential(
                nn.Linear(hidden, hidden),
                act,
                nn.Linear(hidden, out_dim),
                nn.Sigmoid(),
            )

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        h = F.relu(self.input_proj(x))
        for gat, ln in zip(self.gat_layers, self.layer_norms):
            h_new = gat(h, edge_index)
            h = ln(h + h_new)
            h = F.relu(h)
        return self.head(h)


def _compute_features(chip: dict) -> torch.Tensor:
    """Compute 9-dim features per cell."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}

    net_count = {n: 0 for n in cell_names}
    net_sizes = {n: [] for n in cell_names}
    for net in nets:
        for c in net["components"]:
            if c in name_to_idx:
                net_count[c] += 1
                net_sizes[c].append(len(net["components"]))

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


def _chip_to_data(chip: dict) -> Data:
    """Convert chip dict to PyG Data object."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}

    edges = []
    for net in nets:
        cells_in_net = [name_to_idx[c] for c in net["components"] if c in name_to_idx]
        for i in range(len(cells_in_net)):
            for j in range(i + 1, len(cells_in_net)):
                a, b = cells_in_net[i], cells_in_net[j]
                edges.append([a, b])
                edges.append([b, a])

    x = _compute_features(chip)
    edge_index = (torch.tensor(edges, dtype=torch.long).t().contiguous()
                  if edges else torch.zeros((2, 0), dtype=torch.long))
    return Data(x=x, edge_index=edge_index), cell_names, die, name_to_idx


def predict_placement(chip: dict, model: GATPlacer, device: str = "cpu",
                      output_activation: str = "auto") -> Dict[str, Dict[str, float]]:
    """Use trained GAT to predict placement for a chip.

    output_activation:
      - "auto": use tanh(scale=0.5) for hidden>=128 models, [-1,1]->[0,1] for others
      - "tanh": apply tanh, then map [-1, 1] to [0, 1]
      - "sigmoid": apply sigmoid
      - "direct": use raw output (assumed to be in [0, 1])
    """
    data, cell_names, die, name_to_idx = _chip_to_data(chip)
    model.eval()
    with torch.no_grad():
        out = model(data.to(device))

    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]

    # Determine activation based on model architecture
    needs_remap = False
    if output_activation == "auto":
        # Best (94K) model: output is unbounded.
        # Use sigmoid with scale 0.05 to get a meaningful spread across the die.
        n_params = sum(p.numel() for p in model.parameters())
        if n_params > 50000:  # 94K model
            out = torch.sigmoid(out * 0.05)
        # else: head already has Sigmoid, output is in [0, 1]
    elif output_activation == "tanh":
        out = torch.tanh(out * 0.5)
        needs_remap = True
    elif output_activation == "sigmoid":
        out = torch.sigmoid(out * 0.05)

    out_np = out.numpy()
    components = {}
    for name, idx in name_to_idx.items():
        x_raw = float(out_np[idx, 0])
        y_raw = float(out_np[idx, 1])
        if needs_remap:
            x_norm = (x_raw + 1) / 2
            y_norm = (y_raw + 1) / 2
        else:
            x_norm = x_raw
            y_norm = y_raw
        x_norm = max(0.0, min(1.0, x_norm))
        y_norm = max(0.0, min(1.0, y_norm))
        components[name] = {
            "x": x_norm * die_w + die["x1"],
            "y": y_norm * die_h + die["y1"],
        }
    return components


def load_model(checkpoint_path: str) -> GATPlacer:
    """Load a pre-trained GAT placer from a checkpoint.

    Auto-detects architecture from the checkpoint.
    """
    state = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if isinstance(state, dict) and "model" in state:
        state = state["model"]

    # Auto-detect hidden size from first GAT layer
    hidden = state["input_proj.weight"].shape[0]
    # num_layers = max index in gat_layers + 1
    layer_indices = set()
    for k in state:
        if k.startswith("gat_layers."):
            try:
                layer_indices.add(int(k.split(".")[1]))
            except (ValueError, IndexError):
                pass
    num_layers = max(layer_indices) + 1 if layer_indices else 3
    in_dim = state["input_proj.weight"].shape[1]
    # Output dim: last linear in head
    head_keys = [k for k in state if k.startswith("head.") and k.endswith(".weight")]
    head_keys.sort()
    if head_keys:
        out_dim = state[head_keys[-1]].shape[0]
    else:
        out_dim = 2
    heads = 4  # default

    model = GATPlacer(in_dim=in_dim, hidden=hidden, out_dim=out_dim,
                      num_layers=num_layers, heads=heads)
    model.load_state_dict(state)
    model.eval()
    return model
