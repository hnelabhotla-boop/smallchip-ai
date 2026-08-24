"""
train_gat.py — Quick training script for ChipPlacer's GAT model.
Trains a GAT on ISPD 2005 data to predict good chip placements.
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
from torch_geometric.nn import GATConv
from torch_geometric.data import Data

sys.path.insert(0, str(Path(__file__).parent))
from chipmind.ml.gat_placer import GATPlacer


def chip_to_data(chip):
    """Convert chip to PyG Data."""
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
                edges.append([cells_in_net[i], cells_in_net[j]])
                edges.append([cells_in_net[j], cells_in_net[i]])

    # Compute features
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
        feats.append([
            net_count[c],
            sum(ns) / len(ns),
            max(ns),
            min(ns),
            pos["x"] / die_w,
            pos["y"] / die_h,
            net_count[c] / max(len(cell_names), 1),
            (pos["x"] - die["x1"]) / die_w,
            (pos["y"] - die["y1"]) / die_h,
        ])

    x = torch.tensor(feats, dtype=torch.float32)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.zeros((2, 0), dtype=torch.long)

    die_w = max(die["x2"] - die["x1"], 1)
    die_h = max(die["y2"] - die["y1"], 1)
    targets = []
    for c in cell_names:
        pos = components[c]
        targets.append([
            (pos["x"] - die["x1"]) / die_w,
            (pos["y"] - die["y1"]) / die_h,
        ])
    y = torch.tensor(targets, dtype=torch.float32)

    return Data(x=x, edge_index=edge_index, y=y)


def train(data_path, epochs=100, save_path="models/gat_placer.pt", lr=1e-3, log_every=10):
    print("=" * 60)
    print("  ChipPlacer — GAT Training")
    print("=" * 60)

    print(f"\nLoading: {data_path}")
    with open(data_path) as f:
        chips = json.load(f)
    print(f"  {len(chips)} chips")

    print("Building graphs...")
    graphs = [chip_to_data(c) for c in chips]
    print(f"  Built {len(graphs)} graphs")

    model = GATPlacer(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n  Model: {n_params:,} params")
    print(f"  Training: {epochs} epochs, lr={lr}")

    best_loss = float("inf")
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    best_path = save_path.parent / "gat_placer_best.pt"

    start = time.time()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        np.random.shuffle(graphs)
        for data in graphs:
            pred = model(data)
            loss = F.mse_loss(pred, data.y)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(graphs)
        elapsed = time.time() - start
        if (epoch + 1) % log_every == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:>3}/{epochs}  loss={avg_loss:.4f}  ({elapsed:.0f}s)", flush=True)
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), best_path)
            # Also save to the standard path
            torch.save(model.state_dict(), save_path)

    print(f"\n  Done. Best loss: {best_loss:.4f}")
    print(f"  Saved to: {save_path}")
    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/ispd_training_data.json")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--save-path", default="models/gat_placer.pt")
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()
    train(args.data, args.epochs, args.save_path, args.lr)
