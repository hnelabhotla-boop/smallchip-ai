# IEEE Computer Society Special Award Application

> **For the IEEE Computer Society special award at ISEF 2027.**
> Separate from the Grand Awards. Application is usually 1-2 pages of project summary + relevance statement.

---

## Project Title
**SmallChip AI: A Pre-Trained Graph Attention Network for Open-Source Chip Placement**

## Category
IEEE Computer Society — Computer Science (Embedded Systems / AI / EDA)

## Abstract (200 words)

Modern chip design relies on automated placement tools that cost $1M-$5M per license per year, locking out the 99% of real-world designs (hearing aids, microwave controllers, IoT sensors, car key fobs, phone PMICs) that contain only 100-15,000 cells. The leading open-source alternative, OpenROAD, fails on real industry designs above ~1,000 cells because its gradient-based placer (RePlAce) suffers from numerical instability on dense layouts — 4 of 4 attempts on a 15,000-cell design diverge at iteration 2,700 with cost function values exceeding 10³¹.

We present SmallChip AI, a pre-trained Graph Attention Network (GAT) that produces legal placements of 100-15,000-cell designs in 17 seconds on a single CPU core, with no per-design retraining. On the GCD benchmark (692 cells), our GAT achieves 99.7% lower wirelength (10,775 vs 3,987,080 HPWL) than OpenROAD's default placer — validated by OpenROAD's own static timing and power analysis, with identical timing (0.52 ns WNS) and power (1.06 mW). On 91 ISPD 2005 connected subsets, our model wins 89/91 with 75.2% average improvement. The system includes a multi-objective predictor (5 quality metrics in one inference) and an LLM co-pilot that translates natural-language design goals into tailored reports. Open source, BSD-licensed, with public training data and pre-trained weights.

## Relevance to IEEE Computer Society

SmallChip AI advances the state of the art in **three areas of computer science** that the IEEE Computer Society specifically recognizes:

### 1. **Machine Learning Systems** (core CS)
- Pre-trained graph neural network (GAT) applied to a combinatorial optimization problem
- Custom loss function (position MSE + HPWL + spread penalty) to prevent mode collapse
- Generalization analysis: trained on 100-1,858 cell designs, applied to 15,000-cell designs

### 2. **Software Engineering / Open-Source** (core CS)
- Production-grade Python package (`chipmind`), FastAPI backend, web frontend, desktop .app
- BSD-licensed, 100% open source on GitHub
- Public training data (ISPD 2005), public pre-trained weights, public benchmarks
- Full reproducibility: anyone with a laptop can run the entire pipeline

### 3. **Human-Computer Interaction** (core CS)
- LLM co-pilot translating natural language ("make it use less power") to multi-objective placement preferences
- Demonstrates that AI co-pilots can make complex ML systems accessible to non-experts

## Why this is novel

To our knowledge, SmallChip AI is the **first pre-trained placer for general netlists**. Prior work on learning-based placement (Mirhoseini et al., Nature 2021) trains per-design and requires 8-48 hours of GPU per chip. SmallChip AI is amortized: 10 hours of training once, then 17 seconds per inference for any design.

It is also the **first open-source placer that produces legal 15,000-cell placements**. OpenROAD's RePlAce diverges; the only working alternatives are $1M+/year proprietary tools (Cadence Innovus, Synopsys ICC).

## Validation

- **OpenROAD's own static timing and power analysis** on the GAT-placed GCD design
- **91-design benchmark** on real ISPD 2005 industry designs
- **End-to-end reproducibility** — open source, public data, public weights
- **Documented failures** — 6 OpenROAD divergence logs as evidence of the gap we fill

## Project Links

- **Source code:** https://github.com/hnelabhotla-boop/smallchip-ai
- **Pre-trained weights:** included in repo
- **Training data:** public ISPD 2005 Bookshelf benchmarks
- **Desktop app:** downloadable from GitHub Releases (BSD)
- **Paper:** draft included in this submission

## Author

**Harshith Nelabothla**
Strongsville High School, Strongsville, OH
Grade 9 (2026-2027 school year)
First-year ISEF participant (previously won 7-8 Grand Prize at NEOSEF 2026 with a separate project)

## Note to IEEE-CS Judges

If you want to evaluate the engineering rigor, the math section (§3.8 of the paper) gives the formal derivations: HPWL formal definition, GAT attention equations, loss function with all three terms, complexity comparison against SA/ePlace/PPO. The plateau chart shows that 12 classical methods are stuck at 1.3M HPWL on GCD while GAT drops to 50K — that's the algorithmic breakthrough, mathematically documented.

## Bonus points

The 5-metric multi-objective predictor + LLM co-pilot combination is a **demonstration of "AI helping humans use AI"** — a meta-application of ML that IEEE-CS finds especially compelling. No commercial EDA tool exposes all 5 metrics simultaneously; SmallChip AI does, and the LLM co-pilot makes the trade-offs accessible to a non-ML expert.
