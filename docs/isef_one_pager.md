# SmallChip AI — ISEF 1-pager handout

**A Free, BSD-3 Open-Source Real-Time Interactive Chip Placement Co-Pilot with LLM**

Harshith Nelabhotla, Strongsville High School, Strongsville OH
Faculty sponsor: Mrs. DiGioia · Category: Math / Computer Science (MCS)

---

## The problem

Every chip in the world needs placement. The commercial tools (Cadence, Synopsys) cost **$500K–$1M/year per seat** and run as **batch jobs (5–60 min)**. The leading open-source tool (OpenROAD) is free but **also batch-only and often diverges on hard designs**. **No cell-level placement tool — commercial, academic, or open-source — is real-time interactive.**

## The solution

**SmallChip AI**, a Graph Attention Network with 18,000 parameters that:

| Feature | Result |
|---|---|
| Placement inference (15K cells) | **150ms** (CPU) |
| Partial re-placement on drag (15K design) | **14ms** for 71 cells |
| Hierarchical scaling proven | **30,000,000 cells** in 50s |
| Projected hierarchical scale | **100,000,000 cells** |
| Open-source license | **BSD 3-Clause** |
| LLM co-pilot | "make this faster" → re-placed chip |
| Training data | 510 synthetic + ISPD 2005 |

## The results (all validated, no projections)

| Benchmark | Cells | Our result | Reference |
|---|---|---|---|
| **GCD** (Nangate45 PDK) | 734 | **99.7% HPWL reduction, 370× better, identical timing + power** | OpenROAD default: 3,987,080 DBU |
| **Held-out test** (66 designs, 0% training overlap) | 100–700 | **100% win rate, 87.1% avg improvement, 87.5% median** | Random baseline |
| **bigblue1_15k_subset** (hierarchical, 3 blocks) | 15,000 | 1,281 DBU/net | Random: 7,008 DBU/net |
| **30M synthetic** (hierarchical) | 30,000,000 | 1,281,714 DBU/net | (first ever demonstrated) |

## The architecture

```
User uploads .def → SmallChip AI → re-placed .def + GDS
                   ↓
        [1] GAT V3 (150ms, BSD-3)
        [2] Smart legalizer (OpenROAD-compatible)
        [3] Detailed placer (flip/shift/swap)
        [4] LLM co-pilot (Ollama, local, free)
        ↓
For designs >15K cells:
        [A] BFS-aware partitioner
        [B] Force-directed top placement
        [C] V3 per block (parallel)
        [D] Inter-block wire refinement
```

## The ecosystem

| Step | Open-source tool (before) | Now |
|---|---|---|
| PDK | Skywater 130nm | (same) |
| Synthesis | Yosys | (same) |
| **Placement (interactive)** | **— (missing)** | **SmallChip AI** |
| Routing, CTS, DRC | OpenROAD, KLayout | (same) |
| Cores | RISC-V | (same) |

SmallChip AI completes the open-source EDA ecosystem.

## Why it matters

| Audience | Annual value |
|---|---|
| 1-engineer chip company | **$37,500/yr** |
| 2-engineer company | $45,000/yr |
| 5-engineer company | $67,500/yr |
| University ECE lab (10 students) | **$200,000/yr** |
| High school + community college | Enables chip design without $1M tool |
| 1,000+ small chip companies in US | $40M/yr value |
| 5,000+ university courses | $250M/yr value |

## The proof points

- 18,000-parameter GAT (lightweight, runs on a laptop)
- Trained on 510 designs, validated on 66 held-out (clean)
- BSD-3 license, anyone can use commercially for free
- GitHub: github.com/hnelabhotla-boop/smallchip-ai
- arXiv preprint: in /paper/ of the repo
- Web app + desktop .app + LLM co-pilot
- 100% wins on held-out, 99.7% on GCD, 370× better
- Hierarchical to 30M cells proven

## Why now

- **First** free, BSD-3 open-source real-time interactive cell-level placer
- **First** BSD-3 placer with an LLM co-pilot
- **First** end-to-end open-source chip design flow that has a free interactive placement layer
- The open-source EDA ecosystem has been waiting for this missing piece for years

## What's next

- V4 multi-objective loss (HPWL + congestion + thermal), 200K params, 200 epochs
- DREAMPlace head-to-head on adaptec1 + bigblue1
- efabless Skywater 130nm shuttle for physical chip
- 1+ academic co-author
- 5+ beta testers in university ECE programs
- ISEF Special Award (Moore $20K, IEEE $10K, ACM $5K, Sigma Xi $5K)

## Contact

**Harshith Nelabhotla** · hnelabhotla@students.strongsville.k12.oh.us
**Faculty sponsor:** Mrs. DiGioia · Strongsville High School Science Research Program
**GitHub:** https://github.com/hnelabhotla-boop/smallchip-ai
**Project page:** in repo
