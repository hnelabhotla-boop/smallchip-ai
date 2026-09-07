"""
train_v5_aggressive.py — V5 trainer. Same V4 GATv2 arch, but:
  - 200 epochs (vs V4's 50)
  - Larger training data (combined + augmented)
  - Re-balanced loss with stronger thermal weight
  - Saves best model by HPWL on validation set (not just training loss)

Usage:
  python train_v5_aggressive.py --data data/combined_training_data.json --epochs 200

Goal: get a model that pushes 100M HPWL down from 15.7M to <12M DBU/net.
"""
import sys
import json
import time
import math
import random
import argparse
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch_geometric.nn import GATv2Conv
from torch_geometric.data import Data

sys.path.insert(0, str(Path(__file__).parent))


def soft_max(x, dim=-1, temperature=0.1):
    return torch.logsumexp(x / temperature, dim=dim) * temperature


def soft_min(x, dim=-1, temperature=0.1):
    return -soft_max(-x, dim=dim, temperature=temperature)


def soft_hpwl(positions, nets, temperature=0.1):
    """Soft HPWL — normalized."""
    total = positions.new_zeros(())
    n = max(len(nets), 1)
    for net in nets:
        if len(net["components"]) < 2:
            continue
        idx = torch.tensor(net["components"], dtype=torch.long, device=positions.device)
        p = positions[idx]
        total = total + (soft_max(p[:, 0], temperature=temperature) - soft_min(p[:, 0], temperature=temperature))
        total = total + (soft_max(p[:, 1], temperature=temperature) - soft_min(p[:, 1], temperature=temperature))
    return total / n


def congestion_loss(positions, nets, grid_n=10):
    n = positions.size(0)
    if n == 0:
        return positions.new_zeros(())
    gx = ((positions[:, 0] + 0.5) * grid_n).clamp(0, grid_n - 1).long()
    gy = ((positions[:, 1] + 0.5) * grid_n).clamp(0, grid_n - 1).long()
    grid_idx = gx * grid_n + gy
    counts = torch.zeros(grid_n * grid_n, device=positions.device)
    counts.scatter_add_(0, grid_idx, torch.ones_like(grid_idx, dtype=torch.float32))
    mean = counts.mean() + 1e-6
    std = ((counts - mean) ** 2).mean().sqrt()
    return std / mean


def thermal_loss(positions, nets, grid_n=8):
    n = positions.size(0)
    if n == 0:
        return positions.new_zeros(())
    gx = ((positions[:, 0] + 0.5) * grid_n).clamp(0, grid_n - 1).long()
    gy = ((positions[:, 1] + 0.5) * grid_n).clamp(0, grid_n - 1).long()
    grid_idx = gx * grid_n + gy
    power = torch.ones(n, device=positions.device, dtype=torch.float32)
    counts = torch.zeros(grid_n * grid_n, device=positions.device)
    counts.scatter_add_(0, grid_idx, power)
    mean = counts.mean() + 1e-6
    std = ((counts - mean) ** 2).mean().sqrt()
    return std / mean


def spread_penalty(positions, target_std=0.25):
    std_x = positions[:, 0].std()
    std_y = positions[:, 1].std()
    avg_std = (std_x + std_y) / 2
    return F.relu(target_std - avg_std) / target_std


def compute_features_v5(chip):
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}

    net_count = {n: 0 for n in cell_names}
    net_sizes = {n: [] for n in cell_names}
    neighbor_set = {n: set() for n in cell_names}
    for net in nets:
        comps = [c for c in net["components"] if c in name_to_idx]
        for c in comps:
            net_count[c] += 1
            net_sizes[c].append(len(comps))
        for i, c1 in enumerate(comps):
            for c2 in comps[i+1:]:
                neighbor_set[c1].add(c2)
                neighbor_set[c2].add(c1)

    die_w = max(die["x2"] - die["x1"], 1)
    die_h = max(die["y2"] - die["y1"], 1)
    n_cells = len(cell_names)
    avg_net_count = sum(net_count.values()) / max(1, n_cells)

    feats = []
    for c in cell_names:
        pos = components[c]
        ns = net_sizes[c] or [0]
        nc = net_count[c]
        neighbor_count = len(neighbor_set[c])
        f = [
            nc,
            sum(ns) / len(ns),
            max(ns),
            min(ns),
            nc / max(avg_net_count, 1),
            neighbor_count,
            neighbor_count / max(nc, 1),
            pos["x"] / die_w,
            pos["y"] / die_h,
            (pos["x"] - die["x1"]) / die_w,
            (pos["y"] - die["y1"]) / die_h,
            math.log1p(nc) / 10.0,
        ]
        feats.append(f)
    return torch.tensor(feats, dtype=torch.float32), name_to_idx


def chip_to_data_v5(chip, randomize_input=True, seed=None):
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]
    cell_names = list(components.keys())
    name_to_idx = {n: i for i, n in enumerate(cell_names)}

    if randomize_input and seed is not None:
        rng = random.Random(seed)
        for c in cell_names:
            components[c] = {
                "x": rng.randint(die["x1"], die["x2"]),
                "y": rng.randint(die["y1"], die["y2"]),
            }

    edges = []
    for net in nets:
        cells_in_net = [name_to_idx[c] for c in net["components"] if c in name_to_idx]
        for i in range(len(cells_in_net)):
            for j in range(i + 1, len(cells_in_net)):
                edges.append([cells_in_net[i], cells_in_net[j]])
                edges.append([cells_in_net[j], cells_in_net[i]])

    x, _ = compute_features_v5(chip)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous() if edges else torch.zeros((2, 0), dtype=torch.long)

    die_w = max(die["x2"] - die["x1"], 1)
    die_h = max(die["y2"] - die["y1"], 1)
    targets = []
    for c in cell_names:
        pos = components[c]
        targets.append([(pos["x"] - die["x1"]) / die_w, (pos["y"] - die["y1"]) / die_h])
    y = torch.tensor(targets, dtype=torch.float32)

    indexed_nets = []
    for net in nets:
        idxs = [name_to_idx[c] for c in net["components"] if c in name_to_idx]
        if len(idxs) >= 2:
            indexed_nets.append({"components": idxs})

    return x, edge_index, y, indexed_nets, die, name_to_idx


class GATPlacerV5(nn.Module):
    """V5: same as V4 but with stronger head (3-layer MLP), residual head, and EMA."""
    def __init__(self, in_dim=12, hidden=128, out_dim=2, num_layers=3, heads=4, dropout=0.1):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden)
        self.input_norm = nn.LayerNorm(hidden)
        self.gat_layers = nn.ModuleList([
            GATv2Conv(hidden, hidden // heads, heads=heads, concat=True, dropout=dropout)
            for _ in range(num_layers)
        ])
        self.layer_norms = nn.ModuleList([nn.LayerNorm(hidden) for _ in range(num_layers)])
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2),
            nn.GELU(),
            nn.Linear(hidden // 2, out_dim),
            nn.Tanh(),
        )

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        h = self.input_norm(F.gelu(self.input_proj(x)))
        for gat, ln in zip(self.gat_layers, self.layer_norms):
            h_new = gat(h, edge_index)
            h = ln(h + h_new)
            h = F.gelu(h)
            h = self.dropout(h)
        return self.head(h)


def tanh_to_die(tanh_pos, die):
    die_w = die["x2"] - die["x1"]
    die_h = die["y2"] - die["y1"]
    x = (tanh_pos[:, 0] + 1) / 2 * die_w + die["x1"]
    y = (tanh_pos[:, 1] + 1) / 2 * die_h + die["y1"]
    return torch.stack([x, y], dim=1)


def train_v5(
    data_path, epochs=200, save_dir="results/gat_v5",
    log_every=5, lr=1e-3, hidden=128, num_layers=3, heads=4, dropout=0.1,
    hpwl_weight=1.0, congestion_weight=0.3, thermal_weight=0.1, spread_weight=1.5,
    soft_temp=0.1, seed=42, device="cpu",
):
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    best_path = save_dir / "gat_v5_model_best.pt"
    last_path = save_dir / "gat_v5_model.pt"

    print("=" * 60)
    print("  ChipMind — GAT Placer V5 (aggressive, 200ep, multi-objective)")
    print("=" * 60)

    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    print(f"\nLoading: {data_path}")
    with open(data_path) as f:
        chips = json.load(f)
    print(f"  {len(chips)} chips")

    # 80/20 train/val split (deterministic by hash)
    chips_sorted = sorted(chips, key=lambda c: hash(c.get("name", "")) % (10**8))
    val_n = max(20, len(chips_sorted) // 5)
    val_chips = chips_sorted[:val_n]
    train_chips = chips_sorted[val_n:]
    print(f"  Train: {len(train_chips)}, Val: {len(val_chips)}")

    print("Building data...")
    train_data = [chip_to_data_v5(c) for c in train_chips]
    val_data = [chip_to_data_v5(c) for c in val_chips]
    print(f"  Built {len(train_data)} train, {len(val_data)} val")

    model = GATPlacerV5(in_dim=12, hidden=hidden, out_dim=2, num_layers=num_layers, heads=heads, dropout=dropout)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"\n  Model: GATv2 {num_layers} layers × {hidden} hidden × {heads} heads = {n_params:,} params")
    print(f"  Device: {device}")
    print(f"  Loss: HPWL({hpwl_weight}) + cong({congestion_weight}) + therm({thermal_weight}) + spread({spread_weight})")

    model = model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    warmup_epochs = 10
    def lr_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        progress = (epoch - warmup_epochs) / max(1, epochs - warmup_epochs)
        return 0.5 * (1 + math.cos(math.pi * progress))
    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    print(f"  Training: {epochs} epochs, lr={lr}")
    start_time = time.time()
    best_val_hpwl = float("inf")

    for epoch in range(epochs):
        model.train()
        rng = random.Random(42 + epoch)
        rng.shuffle(train_data)

        epoch_loss = 0
        epoch_hpwl = 0
        epoch_cong = 0
        epoch_therm = 0
        epoch_spread = 0
        n_batches = 0

        for x, edge_index, y, indexed_nets, die, name_to_idx in train_data:
            data = Data(x=x, edge_index=edge_index)
            positions = tanh_to_die(model(data), die)
            target_pos = tanh_to_die(y, die)

            hpwl = soft_hpwl(positions, indexed_nets, temperature=soft_temp)
            cong = congestion_loss(positions, indexed_nets)
            therm = thermal_loss(positions, indexed_nets)
            spread = spread_penalty(positions)

            loss = hpwl_weight * hpwl + congestion_weight * cong + thermal_weight * therm + spread_weight * spread

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_loss += loss.item()
            epoch_hpwl += hpwl.item()
            epoch_cong += cong.item()
            epoch_therm += therm.item()
            epoch_spread += spread.item()
            n_batches += 1

        scheduler.step()

        # Validation
        if (epoch + 1) % log_every == 0 or epoch == epochs - 1:
            model.eval()
            val_hpwl_total = 0
            with torch.no_grad():
                for x, edge_index, y, indexed_nets, die, name_to_idx in val_data[:20]:
                    data = Data(x=x, edge_index=edge_index)
                    positions = tanh_to_die(model(data), die)
                    for net in indexed_nets:
                        idxs = net["components"]
                        p = positions[idxs]
                        val_hpwl_total += (p[:, 0].max() - p[:, 0].min()).item() + (p[:, 1].max() - p[:, 1].min()).item()
            val_hpwl_avg = val_hpwl_total / max(1, 20)
            elapsed = time.time() - start_time
            cur_lr = scheduler.get_last_lr()[0]
            print(f"  Ep {epoch+1:3d}/{epochs} loss={epoch_loss/n_batches:.4f} hpwl={epoch_hpwl/n_batches:.4f} "
                  f"cong={epoch_cong/n_batches:.3f} therm={epoch_therm/n_batches:.3f} "
                  f"spread={epoch_spread/n_batches:.4f} val_hpwl={val_hpwl_avg:.2f} "
                  f"lr={cur_lr:.5f} ({elapsed:.0f}s)")

            if val_hpwl_avg < best_val_hpwl:
                best_val_hpwl = val_hpwl_avg
                torch.save({
                    "model_state_dict": model.state_dict(),
                    "args": {"hidden": hidden, "num_layers": num_layers, "heads": heads, "dropout": dropout},
                    "epoch": epoch + 1,
                    "val_hpwl": val_hpwl_avg,
                }, best_path)
                print(f"    -> saved best (val_hpwl={val_hpwl_avg:.2f})")

        # Save last every epoch
        torch.save({
            "model_state_dict": model.state_dict(),
            "args": {"hidden": hidden, "num_layers": num_layers, "heads": heads, "dropout": dropout},
            "epoch": epoch + 1,
        }, last_path)

    print(f"\nDone in {time.time()-start_time:.0f}s. Best val HPWL: {best_val_hpwl:.2f}")
    print(f"Best model: {best_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/combined_training_data.json")
    p.add_argument("--epochs", type=int, default=200)
    p.add_argument("--save-dir", default="results/gat_v5")
    p.add_argument("--hidden", type=int, default=128)
    p.add_argument("--num-layers", type=int, default=3)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--log-every", type=int, default=5)
    args = p.parse_args()
    train_v5(args.data, args.epochs, args.save_dir, args.log_every, args.lr,
             args.hidden, args.num_layers, args.heads)
