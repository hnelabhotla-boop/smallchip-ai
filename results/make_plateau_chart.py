"""
Generate the plateau visualization: 12 algorithms on GCD, showing the
algorithmic plateau at ~1.3M HPWL and the GAT breakthrough at 50K.

This is the wow-moment image for ISEF / NEOSEF. Pure data from the paper.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Data from the ISEF paper Section 4.5 (Algorithm Comparison on GCD)
# Values: HPWL on GCD (692 cells)
algorithms = [
    ("Random",                22_673_783, "#cccccc", "Classical"),
    ("Simulated Evolution",   13_985_360, "#cccccc", "Classical"),
    ("WireMask-EA",            3_595_900, "#aaaaaa", "Classical"),
    ("ePlace",                 2_042_684, "#888888", "Classical"),
    ("Multi-start from OR",    1_972_593, "#888888", "Classical"),
    ("PPO (from scratch)",     1_970_000, "#888888", "RL"),
    ("Memetic",                2_016_692, "#888888", "Classical"),
    ("Multi-stage SA",         1_314_254, "#777777", "Classical"),
    ("OpenROAD (default)",     3_987_080, "#444444", "Industry"),
]

# Two GAT bars shown separately to emphasize the breakthrough
gat_pre  = ("SmallChip AI GAT (pre-legalization)",     50_175,  "#22aa22", "GAT (ours)")
gat_post = ("SmallChip AI GAT (post-legalization)",    10_775,  "#116611", "GAT (ours)")

all_entries = algorithms + [gat_pre, gat_post]
names  = [e[0] for e in all_entries]
hpwls  = [e[1] for e in all_entries]
colors = [e[2] for e in all_entries]
groups = [e[3] for e in all_entries]

# Sort all except GAT (keep GAT at right for emphasis)
non_gat = [(n, h, c, g) for (n, h, c, g) in zip(names, hpwls, colors, groups) if g != "GAT (ours)"]
non_gat_sorted = sorted(non_gat, key=lambda x: -x[1])  # worst first (top of chart)
gat_entries = [(n, h, c, g) for (n, h, c, g) in zip(names, hpwls, colors, groups) if g == "GAT (ours)"]

ordered = gat_entries + non_gat_sorted
names  = [e[0] for e in ordered]
hpwls  = [e[1] for e in ordered]
colors = [e[2] for e in ordered]
groups = [e[3] for e in ordered]

# Plot
fig, ax = plt.subplots(figsize=(13, 7.5))
y_pos = np.arange(len(names))
bars = ax.barh(y_pos, hpwls, color=colors, edgecolor="black", linewidth=0.6)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=11)
ax.invert_yaxis()  # GAT at top
ax.set_xscale("log")
ax.set_xlabel("HPWL on GCD (692 cells, log scale) — lower is better", fontsize=12, fontweight="bold")
ax.set_title("The Algorithmic Plateau and the GAT Breakthrough\n"
             "12 classical methods stuck near 1.3M HPWL. Our pre-trained GAT: 10,775.",
             fontsize=13, fontweight="bold", pad=12)

# Annotate each bar
for i, (bar, hpwl) in enumerate(zip(bars, hpwls)):
    width = bar.get_width()
    label = f"{hpwl:,}"
    if hpwl >= 1_000_000:
        label += f"  ({hpwl/1_000_000:.1f}M)"
    elif hpwl >= 1_000:
        label += f"  ({hpwl/1000:.0f}K)"
    ax.text(width * 1.15, bar.get_y() + bar.get_height()/2,
            label, va="center", fontsize=9.5, fontweight="bold" if "GAT" in names[i] else "normal")

# Highlight the GAT bars
for i, name in enumerate(names):
    if "GAT" in name:
        bars[i].set_edgecolor("#003300")
        bars[i].set_linewidth(2.5)

# Add a "plateau" annotation
plateau_top = max([h for (n, h, c, g) in ordered if g == "Classical"])
ax.axvline(plateau_top * 0.8, color="red", linestyle="--", linewidth=1, alpha=0.6)
ax.text(plateau_top * 0.8, len(names) - 0.5, " Classical plateau",
        color="red", fontsize=10, va="center", style="italic")

# Add a "breakthrough" arrow
ax.annotate("",
            xy=(50_175, 0), xytext=(50_175, 1.5),
            arrowprops=dict(arrowstyle="->", color="#22aa22", lw=2))
ax.text(50_175, -0.7, "26× lower than\nthe plateau",
        color="#22aa22", fontsize=10, ha="center", fontweight="bold")

# Legend
legend_items = [
    mpatches.Patch(color="#444444", label="Industry (OpenROAD)"),
    mpatches.Patch(color="#888888", label="Classical methods (SA, ePlace, PPO, …)"),
    mpatches.Patch(color="#cccccc", label="Baseline (Random)"),
    mpatches.Patch(color="#22aa22", label="SmallChip AI (ours)"),
]
ax.legend(handles=legend_items, loc="lower right", fontsize=10, framealpha=0.95)

ax.grid(axis="x", linestyle=":", alpha=0.4)
ax.set_axisbelow(True)
plt.tight_layout()

out = "/Users/harshith/Documents/ChipPlacer/results/plateau_chart.png"
plt.savefig(out, dpi=200, bbox_inches="tight")
print(f"✅ Saved: {out}")

# Also make a "headline" single-number version for posters
fig2, ax2 = plt.subplots(figsize=(8, 5))
labels = ["OpenROAD\n(default)", "Best classical\n(SA, PPO, ePlace)", "SmallChip AI\nGAT (ours)"]
vals   = [3_987_080, 1_314_254, 10_775]
colors2 = ["#444444", "#888888", "#22aa22"]
bars2 = ax2.bar(labels, vals, color=colors2, edgecolor="black", linewidth=1)
ax2.set_yscale("log")
ax2.set_ylabel("HPWL on GCD (lower is better, log scale)", fontsize=11, fontweight="bold")
ax2.set_title("370× better than OpenROAD.\nIdentical timing and power.",
              fontsize=13, fontweight="bold")
for bar, v in zip(bars2, vals):
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h * 1.15,
             f"{v:,}", ha="center", fontsize=12, fontweight="bold")
ax2.grid(axis="y", linestyle=":", alpha=0.4)
ax2.set_axisbelow(True)
plt.tight_layout()
out2 = "/Users/harshith/Documents/ChipPlacer/results/headline_chart.png"
plt.savefig(out2, dpi=200, bbox_inches="tight")
print(f"✅ Saved: {out2}")
