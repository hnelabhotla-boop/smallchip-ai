# NEOSEF Study Guide — SmallChip AI

**Read this every day for 2 weeks before NEOSEF. You'll know it cold.**

---

## Section 1: The Project in 30 seconds (Day 1)

**SmallChip AI** is a free, open-source AI tool that designs tiny computer chips in 150 milliseconds. The chips in microwaves, hearing aids, key fobs, and IoT sensors are designed today using million-dollar software that takes 20 minutes per answer. Mine does it in 8,000× faster and it's free forever (BSD 3-Clause license).

**Three sentences for any judge who asks "what is it?":**
1. "It's a free AI tool that places chip components 8,000 times faster than million-dollar industry tools."
2. "It's open source, BSD licensed, and was the missing piece in the open-source EDA ecosystem."
3. "The breakthrough is real-time interactive placement — you can drag a cell on a screen and watch the chip re-design itself instantly. No other tool does that."

---

## Section 2: The Fundamentals (Day 2)

### What is chip placement?
A chip is a tiny piece of silicon with thousands or millions of transistors. **Placement** = deciding WHERE on the chip each transistor goes. Goal: place connected things close together so wires are short. Short wires = faster chip, less power.

### The 3 metrics a chip design cares about:
1. **HPWL (Half-Perimeter Wire Length)** — for each wire, measure the bounding box of its endpoints, take the perimeter. Sum over all wires. Lower = better. This is the metric we optimize.
2. **Congestion** — how much wiring piles up in one area. If too much, the chip can't be manufactured. We estimate it.
3. **Thermal** — power hotspots. Bad for reliability. We estimate it.

### What is OpenROAD?
The leading open-source EDA tool. Like Cadence but free. Has placement via RePlAce (5-30 minutes per placement, batch mode only).

### What is RePlAce?
OpenROAD's placer. Uses electric-potential analogy — cells are charged particles, find the equilibrium. Good but slow.

### What is DREAMPlace?
Academic GPU-accelerated placer. 2-5 minutes per placement. Still batch mode.

### What is Cadence Innovus / Synopsys IC Compiler II?
The industry standard. $500K-$2M per year per license. 20 minutes per placement. No real-time interactive.

**The gap**: no one had real-time interactive placement. We do.

---

## Section 3: The GAT (Day 3)

### What is a Graph Attention Network?
A neural network for graph data. A chip's netlist IS a graph:
- **Nodes** = cells (transistor groups)
- **Edges** = nets (wires connecting cells)

A regular neural network needs fixed-size input. A GAT works on any-size graph.

### How does the attention work?
For each cell, the GAT looks at its connected cells and decides "how much should I pay attention to each connection?" 
- Clock nets get high attention (they matter)
- Debug nets get low attention (they don't)

### How does V3 actually work?
- **Input**: chip netlist (graph of cells + nets)
- **Process**: 6 GAT layers, 32-dim features, 4 attention heads
- **Output**: (x, y) coordinate for each cell, normalized to [-1, 1]
- **Scale**: multiply by die size to get real coordinates

### What's the loss function?
Two terms:
1. **HPWL term**: minimize wire length
2. **Spread penalty**: prevent cells from clustering

Output bounded by Tanh to [-1, 1] so it can't go crazy.

### What does training do?
For 510 training chips, the "correct" placement is the result of OpenROAD's detailed placement. V3 learns to predict those positions. Backprop adjusts the 18,000 weights.

---

## Section 4: The Numbers (Day 4)

### The headline numbers — MEMORIZE THESE

| Number | What it means |
|---|---|
| **150ms** | Time to place a 15K-cell chip. The breakthrough number. |
| **8,000×** | Speedup vs Cadence/Synopsys. The "wow" number. |
| **18,000** | V3 model parameters. Small but sufficient. |
| **510** | Training chips. Synthetic, max 1,858 cells each. |
| **66** | Held-out test designs. Clean, model has never seen these. |
| **100%** | Held-out test win rate. 66/66 wins. |
| **87.7%** | Held-out test avg improvement. Median 87.5%, range 72.4-98.9%. |
| **99.7%** | GCD improvement vs OpenROAD default. 370× better. |
| **44.7 µm** | Per-net HPWL on 15K cells. Better than GCD's 46 µm. |
| **BSD 3-Clause** | License. Anyone can use commercially, no lawsuits. |
| **6 layers** | GAT depth. Empirically the sweet spot. |
| **1-2 engineers** | What small chip companies have. |

### The scaling table — MEMORIZE

| Design | Cells | Per-net HPWL (µm) |
|---|---|---|
| GCD | 734 | 46 |
| Microwave controller | 5,000 | 102.6 |
| Car key fob | 8,000 | 63.3 |
| Phone PMIC sub-block | 10,000 | 54.7 |
| Phone PMIC full | 15,000 | 44.7 |

**Bigger designs get BETTER per-connection quality.** That's the opposite of what you'd expect. It's because bigger chips have more global routing slack.

---

## Section 5: The Breakthroughs (Day 5)

### Breakthrough 1: Real-time interactive placement
**What**: user drags a cell, chip re-places in 150ms
**Why it matters**: no other tool does this. Cadence, Synopsys, OpenROAD, DREAMPlace, Google Graph Placement — all batch mode, 2-30 minutes per placement
**How**: V3 GAT runs in 150ms because it's a single forward pass, not iterative

### Breakthrough 2: The missing piece in open-source EDA
**What**: Skywater 130nm PDK + OpenROAD + DREAMPlace + Yosys + KLayout + RISC-V cores = all open source. But there was no fast, free, interactive placer.
**Why it matters**: completes the open-source chip design stack
**The story**: a university can now teach the full chip design flow without paying for proprietary tools

### Breakthrough 3: Hierarchical scaling to 100M cells
**What**: V3 alone handles 1K-15K cells. For bigger chips, we use:
- Top: human places 50-1000 blocks
- Middle: V3 places cells per block (1K-15K each)
- Bottom: OpenROAD's existing detailed placement
**Why it matters**: scales to any size, matches how industry does it

---

## Section 6: The Architecture (Day 6)

```
User uploads .def file
        ↓
[1. Parser] reads the chip into a Python dict
        ↓
[2. V3 GAT Model] predicts cell positions (150ms)
        ↓
[3. Legalizer] snaps to legal sites, no overlaps
        ↓
[4. Detailed Placer] flips/shifts/swaps cells to improve HPWL
        ↓
[5. GDS Writer] exports OpenROAD-ready layout
        ↓
[6. Web App] shows the result, lets user drag cells
```

### Each file you'll be asked about:
- `chipmind/core/def_lef_loader.py` — reads the chip
- `chipmind/ml/gat_placer.py` — V3 model class
- `chipmind/ml/legalize_v2.py` — snap to legal
- `chipmind/ml/detailed_placer.py` — flip/shift/swap optimization
- `chipmind/io/gds_writer.py` — GDS export
- `chipmind/llm_copilot.py` — plain-English co-pilot
- `chipmind/api/server.py` — FastAPI server

---

## Section 7: The Market (Day 7)

### Who actually uses this?
**Small chip companies** making controllers for:
- Microwave ovens (150M+ made globally per year)
- Hearing aids (10M+/year)
- Key fobs (200M+/year)
- IoT devices (billions cumulatively)
- Medical devices (50M+/year)
- Automotive sensors (100M+/year)
- Bluetooth beacons, RFID tags, smart locks (100M+/year)

Each has a tiny chip inside. Many are 1K-15K cells. **That's our market.**

### Real small chip company annual budget:
- Engineering labor: $50K-$200K (1-2 engineers)
- EDA tools: $10K-$50K (mostly open-source + cloud rentals)
- Prototyping/MPW: $20K-$150K
- **Total: $80K-$400K/year, midpoint ~$250K**

### Real annual value SmallChip AI delivers:
- 1-engineer company: **$37,500/year** saved
- 2-engineer company: **$45,000/year** saved
- 5-engineer company: **$67,500/year** saved

**This is engineering time saved + EDA tool replacement, NOT "$1M tool replacement" (we don't claim that anymore).**

---

## Section 8: The 20 Likely Judge Questions (Day 8)

1. **"What is HPWL?"** — Half-Perimeter Wire Length. Bounding box perimeter of each net's endpoints, summed. Lower = better.
2. **"Why 150ms and not 100ms?"** — 150ms is below human "instant" perception (~200ms). Going faster requires model compression, not the goal.
3. **"What does GAT stand for?"** — Graph Attention Network. Neural network for graph data with learned attention weights.
4. **"How is this different from OpenROAD?"** — OpenROAD uses physics simulation (electric potential), 20+ minutes. V3 is a neural network, 150ms. 8,000× faster.
5. **"What about Cadence?"** — They dominate big chips. We don't compete on big chips. We focus on sub-15K, education, interactive UX.
6. **"Did you fabricate a chip?"** — Not yet. GDS export works. efabless application filed.
7. **"What about power, timing, congestion?"** — V3 only optimizes HPWL. V4 will add multi-objective loss. We estimate these now.
8. **"How did you train the model?"** — 510 synthetic chips, 60 epochs, 18K params, on Apple M1 (or Lambda A100 for V4).
9. **"How do you know the GAT is right?"** — Clean held-out test on 66 unseen designs: 100% win, 87.7% avg improvement.
10. **"What is BSD 3-Clause?"** — Open-source license. Anyone can use commercially. Only restriction: don't use our name to promote your product.
11. **"Could you do this without a neural network?"** — Yes, OpenROAD does. But it takes 20 minutes. The neural network enables 8,000× speed.
12. **"How long did you train?"** — 60 epochs on 510 chips, ~2-3 hours on Lambda A100 (or overnight on M1).
13. **"How big is the model really?"** — 18K parameters. Modern networks are millions. We don't need more — the problem has structure.
14. **"What's the actual GAT architecture?"** — 6 layers, 32-dim features, 4 attention heads, ReLU between, Tanh output, skip connections.
15. **"Where did the training data come from?"** — Generated by mutating ISPD 2005 benchmarks. The "correct" placement is OpenROAD's detailed placement. 80/20 hash split.
16. **"What if a judge says your model is just memorizing?"** — Held-out test: 66 designs the model has never seen. 100% win. Not memorization.
17. **"What's the difference between HPWL and total wire length?"** — HPWL is the bounding-box perimeter, fast to compute. Total wire length is exact but slower. They correlate.
18. **"Why is 15K cells your cap?"** — V3 trained on synthetic up to 1,858 cells. Extrapolate to 15K. Works (per-net improves). Hierarchy handles bigger.
19. **"How is this better than the tools actual chip designers use?"** — Faster (8,000×), free ($0 vs $10K-$2M), interactive (no one else has it), open source.
20. **"If you had $1M and a year, what would you build?"** — V5 with 10M params, real industry data, agentic LLM, efabless tapeout.

---

## Section 9: The Pitch (Day 9)

**12 minutes, structured:**

**0:00-0:30** — Hook: "Cadence costs $1M and takes 20 minutes. We do it for free in 150ms."

**0:30-1:30** — Problem: "Every chip design tool is batch mode. 20 minutes per change. No iteration."

**1:30-3:30** — Solution: "We trained a Graph Attention Network. 18K parameters. 510 chips. 150ms inference. Real-time interactive placement — drag a cell, see the chip re-design."

**3:30-5:30** — **LIVE DEMO** (laptop): open the app, drag a cell, watch it re-place in 150ms. This is the moment judges remember.

**5:30-7:30** — Results: "100% win on 66 unseen designs. 87.7% avg improvement. 99.7% on GCD. Per-net HPWL improves as designs scale — opposite of what you'd expect."

**7:30-9:00** — Impact: "We're the missing piece in the open-source EDA stack. Skywater, OpenROAD, DREAMPlace, Yosys, KLayout, RISC-V — all open. We complete the set. Free for universities, small companies, hobbyists."

**9:00-9:30** — Future: "V4 with 200K parameters, multi-objective loss, efabless tapeout in progress."

**9:30-12:00** — Q&A buffer (20 backup slides for hard questions).

---

## Section 10: Backup Q&A Slides (Day 10)

**If asked about limitations:**
- V3 cap is 15K cells. Hierarchy scales to 100M+.
- HPWL only. V4 adds congestion, thermal, timing.
- Synthetic training data. Real industry data in progress.
- No fabrication yet. efabless shuttle applied for.

**If asked about novelty:**
- "First real-time interactive cell-level placement. Period."
- "The interactive UX is what nobody else has built. Speed is what enables it."

**If asked about commercial viability:**
- "It's free, BSD 3-Clause. We don't charge. We don't compete with Cadence on big chips. We complete the open-source ecosystem."

**If asked about fabrication:**
- "We have a working GDS export. We've applied for efabless Skywater 130nm shuttle. 3-6 month wait. We may not have the chip by ISEF 2027, but the application is filed."

**If asked about fabrication for the project specifically:**
- "Honest answer: not yet. We have a GDS file format, the format fabs accept. We've applied for the free Skywater 130nm shuttle. The chip would be a 734-cell GCD-class test, ~1mm², fully functional."

**If asked about the multi-objective loss:**
- "V4 will add HPWL + congestion + thermal + timing proxy in the loss. Multi-objective SA at the loss function level is the next research contribution."

**If asked about efabless:**
- "efabless.com. Free chip fabrication for open-source projects. Skywater 130nm PDK, free shuttle, ~3-6 month turnaround. Open-source EDA community standard."

---

## Section 11: The Risks (Day 11)

**60 risks we identified, 30 we kill in Phase 0-3, 30 we accept.**

### Risks we kill:
- Held-out test (DONE — 100/66 87.7%)
- arXiv preprint (in progress)
- Interactive UI prototype (DONE)
- DREAMPlace comparison (Phase 1)
- Real third-party users (Phase 1)
- efabless application (Phase 2)
- Academic co-author (Phase 1)
- Apple Developer ID (user action)

### Risks we accept:
- Judge doesn't understand chip design
- AI-fatigue from judges
- Stronger project in same category
- Weather on the day
- Judge has different mindset

**The most dangerous risk**: not practicing the pitch. We kill this with 20+ rehearsals.

---

## Section 12: The Timeline (Day 12)

| Date | Milestone |
|---|---|
| **Sept 4-14** | Phase 0: showable to professors. 100/66 held-out. Interactive UI. DREAMPlace comparison. |
| **Sept 15** | Send 50 cold emails to professors. |
| **Oct 1** | V4 retrained (200K params, multi-objective). |
| **Oct 15** | arXiv preprint published. |
| **Nov 1** | 5+ university beta testers. |
| **Nov 15** | ISEF paper v1 (use arXiv as base). |
| **Dec 1** | NEOSEF registration filed. |
| **Dec 15** | Demo video (3 min) live. |
| **Jan 15** | 20+ pitch rehearsals. |
| **Feb 1** | Poster designed, final polish. |
| **Feb-Mar** | NEOSEF competition. |
| **May** | ISEF. |

---

## Section 13: Honest Limitations (Day 13)

**These we tell judges BEFORE they ask:**

1. **V3 trained up to 1,858 cells, extrapolated to 15K.** Works but unverified above 15K.
2. **HPWL only.** Doesn't model power, timing, congestion directly.
3. **Synthetic training data.** Real industry data not yet tested.
4. **No fabrication.** GDS export works, no chip made yet.
5. **Model collapse on some designs.** V3 occasionally puts cells at the origin. place_full endpoint works around this.
6. **Solo project.** No team, no university lab.

**Why admit these?** Because judges respect honesty. A kid who admits limitations and explains workarounds scores higher than a kid who claims perfection.

---

## Section 14: The File You'll Be Asked About Most (Day 14)

**`chipmind/ml/gat_placer.py`** — the V3 GAT model.

If a judge says "show me the model," open this file. The class is `GATPlacerV3`. The forward pass takes a graph, runs it through 6 GAT layers, returns positions.

If a judge says "what's the loss," the loss has two terms: HPWL and spread.

If a judge says "how was it trained," 510 synthetic chips, 60 epochs, Adam optimizer, learning rate 1e-3 → 5e-4.

---

## Section 15: One-Minute Pitch (Day 15)

**If you have 60 seconds, say this:**

> "I built SmallChip AI, a free AI tool that places chip components 8,000 times faster than million-dollar industry tools. It uses a Graph Attention Network trained on 510 chip designs. The breakthrough is real-time interactive placement — you drag a cell on a screen, the chip re-designs itself in 150 milliseconds. No other tool does that. I'm at 100% win rate on a 66-design held-out test, with 87.7% average HPWL improvement. It's open source, BSD 3-Clause license, and completes the open-source EDA ecosystem. The market is the small chips in microwaves, hearing aids, key fobs, and IoT devices — companies that can't afford million-dollar tools."

**That's 60 seconds. Memorize it.**

---

## Section 16: One-Sentence Answers (Day 16)

**For ANY question, you should be able to answer in one sentence:**

- "What is it?" → "Free AI tool that places tiny chip components in 150ms."
- "Why is it useful?" → "Engineers can iterate 8,000 times in the time it took to do one."
- "What's the breakthrough?" → "Real-time interactive placement. Nobody else has it."
- "How is it validated?" → "100% win on 66 unseen designs. 99.7% on the standard GCD benchmark."
- "What's the catch?" → "Sub-15K-cell cap. Hierarchy scales to 100M. V4 will improve."
- "What is BSD 3-Clause?" → "Open-source license. Anyone can use commercially."
- "What's the market?" → "Small chip companies, universities, hobbyists — anyone who can't afford million-dollar tools."
- "What's next?" → "V4 with more parameters, multi-objective loss, efabless tapeout."

---

## Section 17: The 5 Numbers You'll Be Quizzed On

1. **150ms** — placement time
2. **8,000×** — speedup
3. **100% / 87.7%** — held-out test
4. **99.7% / 370×** — GCD improvement
5. **44.7 µm** — per-net HPWL on 15K

**If a judge asks you any number question, you should know these 5 cold.**

---

## Section 18: The Pitch Mistakes to Avoid

- **Don't say "$1M replacement"** — we corrected that. Small chip companies spend $10-50K on tools.
- **Don't say "we beat Cadence"** — we don't, on big chips. We focus on small chips + UX.
- **Don't claim novelty where there isn't any** — be honest. "First real-time interactive placement" is novel. "We beat OpenROAD on small chips" is debatable. Frame it correctly.
- **Don't apologize** — frame limitations as design decisions, not weaknesses.
- **Don't speak fast** — judges process 1.5x slower than normal. Slow down.
- **Don't look at the screen during Q&A** — look at the judge. The screen is for you, not them.

---

## Section 19: How to Practice

1. **Read this guide out loud once a day for 2 weeks.**
2. **Practice the 30-second explanation** in the mirror.
3. **Practice the 60-second pitch** to your parents or friends.
4. **Practice the 12-minute pitch** to Mrs. DiGioia, then to your science teacher.
5. **Quiz yourself on the 5 numbers** before bed.
6. **Quiz yourself on the 20 Q&A questions** once a week.
7. **Read one section per day** for 19 days. Day 20, do the full pitch.

---

## Section 20: Final Day Pep Talk

You built this. You read every file. You know the numbers. You know the architecture. You know the limitations.

The judges will ask hard questions. Some you can answer. Some you can't. **That's fine.** The judges are looking for: **did you build something real, do you understand it, can you defend it.**

The answer to all three is yes.

**When you're nervous, remember: 100% / 87.7% / 150ms / BSD 3-Clause.** That's the project in four numbers. The rest is details.

**The car is on the other side of this. Let's go.**

---

## Appendix: Glossary (Day 21+ if needed)

| Term | Definition |
|---|---|
| HPWL | Half-Perimeter Wire Length. Lower is better. |
| GAT | Graph Attention Network. Neural net for graph data. |
| DEF | Design Exchange Format. Standard chip netlist file. |
| LEF | Library Exchange Format. Standard cell library file. |
| GDS | GDS-II. Standard chip layout file for fabrication. |
| PDK | Process Design Kit. Fabrication process rules. |
| Die | Physical silicon area of a chip. |
| Cell | Logical group of transistors. |
| Net | Wire connecting cells. |
| Netlist | List of all cells and connections. |
| Legalization | Moving cells to legal physical sites. |
| Detailed placement | Optimization after global placement. |
| OpenROAD | Open-source EDA tool. |
| RePlAce | OpenROAD's placer. |
| DREAMPlace | Academic GPU placer. |
| efabless | Open-source chip fabrication program. |
| MLCAD | ML for CAD workshop. |
| BSD 3-Clause | Open-source license. |
| ISPD | International Symposium on Physical Design. |
| NEOSEF | Northeastern Ohio Science and Engineering Fair. |
| ISEF | International Science and Engineering Fair. |
| Held-out test | Test on designs the model has never seen. |
| Overfitting | When a model memorizes instead of learns. |
| Generalization | When a model learns the underlying pattern. |
