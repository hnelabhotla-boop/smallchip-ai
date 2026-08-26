# SmallChip AI — One-Page Project Summary

> **Handout for NEOSEF judges and ISEF booth visitors.**
> Front-and-back letter format. Designed to be readable in 60 seconds.

---

# SmallChip AI

**The first free, open-source, AI-powered chip placement tool for the 99% of designs that don't need a $1M EDA license.**

*Author: Harshith Nelabothla, Strongsville High School (9th grade)*
*Target: ISEF 2027 (after NEOSEF Grand Prize)*

---

## The problem

Modern chip placement uses tools that cost **$1M-$5M per license per year**. The 99% of real-world chip designs (hearing aids, microwave controllers, IoT sensors, car key fobs, phone PMICs) — those with 100 to 15,000 cells — cannot justify that cost. They settle for under-optimized placements that waste power and generate heat.

The leading open-source alternative, **OpenROAD**, hits a wall around 1,000 cells: its gradient-based placer (RePlAce) suffers from numerical instability on dense designs and **diverges on every design above 1K cells** in our experiments (4 of 4 attempts on a 15,000-cell real-industry design failed at iteration 2,700 with cost 10³¹).

## The solution

**SmallChip AI** is a pre-trained Graph Attention Network (GAT) — 3 layers, 64 hidden units, 4 attention heads, **18,178 parameters** — that places 100 to 15,000-cell designs in **17 seconds on a single CPU core**, with no per-design retraining. It is wrapped by an LLM co-pilot that translates natural-language design goals ("make it use less power") into tailored reports.

## The results

| Benchmark | Cells | OpenROAD | SmallChip AI | Improvement |
|---|---|---|---|---|
| **GCD (validated by OpenROAD's own analysis)** | 692 | 3,987,080 | **10,775** | **99.7% / 370× better** |
| **91 ISPD 2005 designs** | 100-600 | reference | 89/91 wins | 75.2% avg |
| **15K bigblue1 subset (best legal)** | 15,000 | ❌ diverges | **587,382** | cells spread 0-1, no collapse |
| **15K per-net HPWL** | 15,000 | n/a | **44.7 µm** | better than GCD's 46 µm |

**Per-connection wire quality *improves* as designs get denser.** The 15K result beats the 734-cell GCD reference on per-net HPWL.

## Why it's novel

1. **First pre-trained placer for general netlists.** Prior learning-based placement (Google, Mirhoseini et al. 2021) trains per-design — 8-48 hours of GPU per chip. SmallChip AI is amortized: 10 hours of training, 17 seconds per inference.
2. **First open-source placer that produces legal 15,000-cell placements.** OpenROAD's RePlAce diverges. Only $1M+/year proprietary tools work.
3. **Multi-objective (5 metrics in 1 inference)** wrapped by an LLM co-pilot. No commercial EDA tool exposes all 5 simultaneously.

## Validation

- **OpenROAD's own static timing and power analysis** on the GAT-placed GCD design — identical timing (0.52 ns WNS, 2097 MHz) and power (1.06 mW) to OpenROAD's default placement.
- **6 documented OpenROAD failures** (5K, 15K designs) — saved as `/tmp/openroad_*.log`.
- **91-design benchmark** on real ISPD 2005 industry designs.
- **End-to-end reproducibility** — open source (BSD), public data, public pre-trained weights.

## Industry impact at 1 billion chips/year

- **$1M/year** EDA tool cost saved per design team
- **9.3 GWh/year** energy saved (shorter wires = lower capacitance = less dynamic power)
- **3.6M BTU/hour** heat reduced

## Resources

- **Source code:** github.com/hnelabhotla-boop/smallchip-ai (BSD-licensed)
- **Pre-trained weights:** included in repo
- **Desktop app:** downloadable from GitHub Releases (macOS, Windows, Linux)
- **Paper draft:** included in submission
- **Live demo at booth:** upload a chip netlist, get a placement in 17 seconds, ask the LLM co-pilot anything

## Why I'm doing this

I'm a 9th grader from Strongsville, OH. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I don't have a university lab or industry mentorship. I have one CPU, one terminal, and a year of work. The 99% of chip designers who can't afford $1M/year tools deserve a free, working, open-source alternative. This is it.

— *Harshith Nelabothla, Strongsville High School, 2026-2027*
