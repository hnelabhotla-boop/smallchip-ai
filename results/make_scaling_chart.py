"""
Generate the 15K scaling curve: per-net HPWL across 5K-15K designs,
showing the per-connection quality IMPROVES as designs get bigger.
"""
import matplotlib.pyplot as plt
import numpy as np

# Data from the ISEF paper Section 4.3.1 (with the polish-updated 15K result)
designs = ["5K", "8K", "10K", "15K"]
cells = [5000, 8000, 10000, 15000]
hpwl = [427545, 420146, 461939, 418115]
per_net = [102.6, 63.3, 54.7, 31.8]  # µm
per_cell = [85.5, 52.5, 46.2, 27.9]  # µm
gcd_per_net = 46.0  # µm (the 734-cell GCD reference)
gcd_per_cell = 15.0  # µm

# Plot 1: per-net HPWL
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

# Left: per-net HPWL
ax1.plot(cells, per_net, "o-", color="#22aa22", linewidth=2.5, markersize=12,
         label="SmallChip AI (per-net HPWL)")
ax1.axhline(y=gcd_per_net, color="red", linestyle="--", linewidth=1.5, alpha=0.7,
            label=f"GCD reference ({gcd_per_net} µm at 734 cells)")
ax1.set_xlabel("Design size (cells)", fontsize=12, fontweight="bold")
ax1.set_ylabel("Per-net HPWL (µm) — LOWER IS BETTER", fontsize=12, fontweight="bold")
ax1.set_title("Per-connection quality IMPROVES as designs get bigger",
              fontsize=13, fontweight="bold")
ax1.legend(loc="upper right", fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xticks(cells)
ax1.set_xticklabels([f"{c//1000}K" for c in cells])

# Annotate each point
for c, pn in zip(cells, per_net):
    ax1.annotate(f"{pn} µm", (c, pn), textcoords="offset points",
                 xytext=(0, 12), ha="center", fontsize=10, fontweight="bold")

# Right: legal HPWL by design size
ax2.bar(designs, hpwl, color=["#88cc88", "#66bb66", "#44aa44", "#228822"],
        edgecolor="black", linewidth=1)
ax2.set_ylabel("Legal HPWL on bigblue1 subset (DBU) — LOWER IS BETTER",
              fontsize=12, fontweight="bold")
ax2.set_xlabel("Design size", fontsize=12, fontweight="bold")
ax2.set_title("V3 + detailed placer scaling curve (all under 500K)",
              fontsize=13, fontweight="bold")
for i, (d, h) in enumerate(zip(designs, hpwl)):
    ax2.text(i, h + 5000, f"{h:,}", ha="center", fontsize=10, fontweight="bold")
ax2.axhline(y=500_000, color="red", linestyle="--", linewidth=1, alpha=0.6,
            label="500K target")
ax2.legend(loc="upper left", fontsize=10)
ax2.grid(axis="y", alpha=0.3)

plt.suptitle("SmallChip AI — 5K-15K scaling on bigblue1 connected subsets",
             fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()

out = "/Users/harshith/Documents/ChipPlacer/results/scaling_chart.png"
plt.savefig(out, dpi=200, bbox_inches="tight")
print(f"✅ Saved: {out}")
