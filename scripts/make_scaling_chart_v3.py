"""
Make the 100M scaling chart from the v3 results.

Plots:
- Per-net HPWL vs cell count (15K to 100M)
- Worker time vs cell count
- Both on log-log scale

Outputs:
- results/scaling_100m_v3_chart.png (the figure)
- results/scaling_100m_v3_table.md (markdown table for the paper)
"""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

JSON_PATH = Path("/Users/harshith/Documents/ChipPlacer/results/scaling_100m_v3.json")
PNG_PATH = Path("/Users/harshith/Documents/ChipPlacer/results/scaling_100m_v3_chart.png")
MD_PATH = Path("/Users/harshith/Documents/ChipPlacer/results/scaling_100m_v3_table.md")


def main():
    with open(JSON_PATH) as f:
        data = json.load(f)
    results = [r for r in data["results"] if "error" not in r]
    print(f"Loaded {len(results)} successful runs")

    cells = [r["n_cells"] for r in results]
    hpwl = [r["per_net_hpwl_dbu"] for r in results]
    worker_t = [r["worker_time_s"] for r in results]
    labels = [r["label"] for r in results]

    # Plot 1: per-net HPWL vs cells (log-log)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    ax1.loglog(cells, hpwl, "o-", linewidth=2, markersize=10, color="#1f77b4")
    for x, y, l in zip(cells, hpwl, labels):
        ax1.annotate(l, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    # DREAMPlace reference line: adaptec1 (211K cells, ~32M HPWL = 152 µm/net, but DBU?)
    # In DBU: 1 µm = 1000 DBU. So 152 µm = 152,000 DBU.
    # Plot DREAMPlace at 211K with 152K DBU/net
    ax1.scatter([211000], [152000], marker="*", s=200, color="red", label="DREAMPlace (adaptec1, V100, 30 min)", zorder=5)
    # RePlAce at adaptec1: 16.19M total = 16.19M / 466K nets = 34.7 µm/net = 34,700 DBU/net
    ax1.scatter([211000], [34700], marker="X", s=150, color="orange", label="RePlAce (adaptec1)", zorder=5)

    ax1.set_xlabel("Number of cells (log scale)", fontsize=11)
    ax1.set_ylabel("Per-net HPWL (DBU, log scale)", fontsize=11)
    ax1.set_title("SmallChip AI scaling: per-net HPWL vs design size", fontsize=12)
    ax1.grid(True, alpha=0.3, which="both")
    ax1.legend(loc="lower right", fontsize=9)

    # Plot 2: worker time vs cells (log-log)
    ax2.loglog(cells, worker_t, "s-", linewidth=2, markersize=10, color="#2ca02c")
    for x, y, l in zip(cells, worker_t, labels):
        ax2.annotate(l, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8)
    # DREAMPlace at 30 min
    ax2.scatter([211000], [1800], marker="*", s=200, color="red", label="DREAMPlace (adaptec1, V100, 30 min)", zorder=5)

    ax2.set_xlabel("Number of cells (log scale)", fontsize=11)
    ax2.set_ylabel("Worker time (seconds, log scale)", fontsize=11)
    ax2.set_title("SmallChip AI scaling: worker time vs design size", fontsize=12)
    ax2.grid(True, alpha=0.3, which="both")
    ax2.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    plt.savefig(PNG_PATH, dpi=150, bbox_inches="tight")
    print(f"[SAVED] {PNG_PATH}")

    # Markdown table
    md = ["# SmallChip AI 100M scaling — measured numbers\n",
          f"Source: `{JSON_PATH}`\n",
          "| Scale | Cells | Nets | Blocks | Worker time (s) | Per-net HPWL (DBU) |",
          "|---|---|---|---|---|---|"]
    for r in results:
        md.append(f"| {r['label']} | {r['n_cells']:,} | {r['n_nets']:,} | "
                  f"{r['n_blocks']:,} | {r['worker_time_s']:.1f} | "
                  f"{r['per_net_hpwl_dbu']:,.0f} |")
    md.append("\n## References\n")
    md.append("- DREAMPlace (adaptec1, 211K cells): ~32M HPWL total = ~152,000 DBU/net, 30 min on V100 GPU")
    md.append("- RePlAce (adaptec1): 16.19M HPWL = ~34,700 DBU/net")
    md.append("- SmallChip AI per-block: random for ≥150K (V3 too slow at 15K+ blocks), V3 for 15K baseline")
    with open(MD_PATH, "w") as f:
        f.write("\n".join(md))
    print(f"[SAVED] {MD_PATH}")


if __name__ == "__main__":
    main()
