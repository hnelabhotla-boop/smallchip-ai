# Annotated Bibliography

> **The 15 papers you need to know for ISEF. Read abstracts first, then deep-dive the 5 starred.**

---

## 1. ★ Mirhoseini et al., "A graph placement methodology for fast chip design" — *Nature*, 2021

**The paper that started the learning-based placement field.** Google used deep RL to place TPU blocks.

**Key claims:**
- 8-48 hours of GPU per chip
- Per-design training (no transfer)
- Beats human experts on TPU designs
- Used policy gradient + reward shaping

**Why it matters for you:** This is the prior work. Your contribution is amortizing across designs with a pre-trained GAT.

**One thing to know:** They use 0 reward for illegal placements. This is a known weakness. You use spread penalty instead.

**Link:** https://www.nature.com/articles/s41586-021-03544-w

---

## 2. ★ Veličković et al., "Graph Attention Networks" — *ICLR*, 2018

**The paper that introduced GATs.** Used for node classification on citation networks.

**Key claims:**
- Attention-based aggregation of node features
- Multi-head attention
- Outperforms GCN on standard benchmarks
- Inductive (generalizes to new graphs)

**Why it matters:** Your GAT placer uses this architecture (3 layers, 64 hidden, 4 heads).

**One thing to know:** The attention equation is:
α_ij = softmax_j(LeakyReLU(a^T [Wh_i || Wh_j]))

**Link:** https://arxiv.org/abs/1710.10903

---

## 3. ★ Cheng et al., "OpenROAD: Toward a Self-Driving, Open-Source Digital Layout Implementation Tool Chain" — *Proc. GLSVLSI*, 2022

**The OpenROAD paper.** Describes the open-source EDA toolchain.

**Key claims:**
- 24-hour turnaround from RTL to GDSII
- RePlAce for global placement
- Open-source, BSD-licensed
- Used in DARPA programs

**Why it matters:** OpenROAD is your baseline comparison. You can cite this paper when explaining the toolchain.

**One thing to know:** RePlAce diverges on designs above ~1K cells. This is the "wall" you fill.

**Link:** https://dl.acm.org/doi/10.1145/3524557.3529552

---

## 4. ★ Lu et al., "ePlace: Electrostatics-based Placement Using Fast Fourier Transform" — *ICCAD*, 2015

**The RePlAce paper (essentially).** The original electrostatics-based placer.

**Key claims:**
- Models cells as 2D Gaussian densities
- Uses density gradient as "force"
- Smooth surrogate of HPWL
- Converges in ~2,500 iterations

**Why it matters:** RePlAce is built on ePlace's ideas. Both have the same numerical instability issue.

**One thing to know:** The density penalty becomes a stiff constraint at high cell density. This is the root cause of the divergence.

**Link:** https://ieeexplore.ieee.org/document/7373573

---

## 5. ★ Mirhoseini et al., "Chip Placement with Deep Reinforcement Learning" — *arXiv*, 2020 (preprint of Nature paper)

**Earlier version of the Google work.** More detail than the Nature paper.

**Key claims:**
- 28 chips, up to 1M cells
- Policy gradient with reward shaping
- 24-hour training per chip

**Why it matters:** Same as #1, but with more technical detail. Cite this for technical questions.

**Link:** https://arxiv.org/abs/2004.10746

---

## 6. Agnesina et al., "AutoDMP: Automated Macro Placement" — *ISPD*, 2023

**Macro placement (not standard cell).** Reinforcement learning for placing large IP blocks.

**Why mention:** Different problem (macros vs standard cells) but related approach. ISEF judges may compare.

**Link:** https://dl.acm.org/doi/10.1145/3569262

---

## 7. Chang et al., "A Practical Methodology for Early Wirelength Estimation" — *TODAES*, 2003

**Why HPWL is a good proxy for routed wire length.** Statistical study on real designs.

**Why mention:** When judges ask "is HPWL really meaningful?" cite this. It validates the metric.

**Link:** https://dl.acm.org/doi/10.1145/762471.762473

---

## 8. ISPD 2005 Contest Benchmarks

**The training and evaluation data.** 8 industrial designs in Bookshelf format.

**Why mention:** This is the data you trained and tested on. Public, citable.

**Link:** https://drive.google.com/drive/folders/1MVIOZp2rihzIFK3C_4RqJs-bUv1TW2YT

---

## 9. BBOPlace-Bench (Black-Box Optimization Placement Benchmark)

**A benchmark for black-box placement optimization.** Used in evolutionary algorithm comparisons.

**Why mention:** Your SA, GA, Memetic baselines come from this benchmark family.

**Link:** https://github.com/lamda-bbo/BBOPlace-Bench

---

## 10. PyTorch Geometric Documentation

**The library you use for GAT.**

**Why mention:** When judges ask "how do you implement GAT?" cite PyG.

**Link:** https://pytorch-geometric.readthedocs.io

---

## 11. Vaswani et al., "Attention Is All You Need" — *NeurIPS*, 2017

**The Transformer paper.** The original attention mechanism.

**Why mention:** When judges ask "what's attention?" start here. Then point to GAT (#2) for the graph version.

**Link:** https://arxiv.org/abs/1706.03762

---

## 12. GATConv source code in PyTorch Geometric

**The implementation of GAT you actually use.**

**Why mention:** When judges ask "how does GAT work in code?" point to this.

**Link:** https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.GATConv.html

---

## 13. Sigl et al., "VLSI Physical Design: From Graph Partitioning to Timing Closure" — *Springer*, 2011

**The textbook on VLSI physical design.** Covers placement, routing, CTS, optimization.

**Why mention:** When judges want a textbook reference. Most chip design textbooks are behind paywalls; this one is widely cited.

**Link:** https://link.springer.com/book/10.1007/978-90-481-9351-2

---

## 14. Khatkhate et al., "Generation of Synthetic Benchmark Circuits for Evaluating Physical Design Tools" — *ICCAD*, 2002

**How to generate synthetic circuits for testing placers.** Methodology paper.

**Why mention:** When judges ask "how do you generate the 5K/8K/10K/15K subsets?" cite this for the connected-subset extraction.

**Link:** https://ieeexplore.ieee.org/document/1168589

---

## 15. Kim et al., "A Simple Yet Effective Timing-Driven Detailed Placement Algorithm" — *ICCAD*, 2012

**Timing-driven detailed placement.** How to optimize for timing, not just HPWL.

**Why mention:** Future work for SmallChip AI. Currently we only optimize HPWL; timing-driven is next.

**Link:** https://ieeexplore.ieee.org/document/6386794

---

## How to use this bibliography

1. **Before ISEF:** Read the abstracts of all 15 papers. Read the intro + method sections of the 5 starred ones.

2. **During ISEF:** When a judge asks a question, say "There's a paper on that — let me cite it." Have a quick mental list of which paper addresses which topic:
   - "How does GAT work?" → Veličković 2018
   - "What's the prior work in learning-based placement?" → Mirhoseini 2021
   - "Why does RePlAce diverge?" → Lu 2015 (ePlace)
   - "What's OpenROAD?" → Cheng 2022
   - "Why use HPWL?" → Chang 2003

3. **After ISEF:** Add the bibliography to the paper's References section. Most are already cited; check completeness.
