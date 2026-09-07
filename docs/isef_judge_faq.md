# ISEF Judge FAQ — anticipated questions and good answers

Use this to study. Every line is something a judge might ask. The answers are short, precise, and use the real numbers.

## Q1: "What does your project do, in 30 seconds?"

> SmallChip AI is a free, BSD-3 open-source tool that places cells on a chip in real time. The user uploads a chip netlist, types plain English like "make this faster", and the chip gets re-placed in 150 milliseconds. They can also drag cells on a canvas and see the chip re-place in 14ms. It's the missing piece in the open-source EDA ecosystem — Skywater, OpenROAD, Yosys, KLayout, and RISC-V are all open, but no one had a free interactive placer until this.

## Q2: "What is cell-level placement?"

> After a chip is designed in Verilog, synthesis turns the code into a netlist of logical cells. Placement is the step where each cell gets physical coordinates on the silicon die. For a 5K-cell design, that's 5,000 (x, y) positions. Placement quality affects timing, power, and area of the final chip. This is one of the hardest optimization problems in chip design — design space is 2N-dimensional.

## Q3: "How is this different from OpenROAD?"

> OpenROAD is a full RTL-to-GDS flow with batch placement (5-30 min per placement, no interaction, no LLM). SmallChip AI is a focused, real-time interactive placer with an LLM co-pilot. They're complementary — for designs >15K, we recommend using SmallChip AI for fast interactive iteration, then handing off to OpenROAD for detailed routing. We document that OpenROAD's RePlAce placer actually fails to converge on the 15K-cell bigblue1 subset, so for that size, SmallChip AI is currently the only working BSD-3 option.

## Q4: "How is this different from DREAMPlace?"

> DREAMPlace is GPU-accelerated batch placement. ~30 minutes on a V100. We use the GAT single-pass with smart legalizer, completing in 150ms on CPU. DREAMPlace wins on raw quality per pass; SmallChip AI wins on iteration speed and human-in-the-loop. We cite DREAMPlace in our paper as the academic state-of-the-art.

## Q5: "How is this different from Cadence or Synopsys?"

> Cadence Innovus and Synopsys IC Compiler II are the commercial gold standard. They cost $500K-$1M per year per seat. They run as batch jobs (20-60 min per placement). They have a GUI but it's not interactive at the cell level — you can view the result but not drag cells. SmallChip AI is BSD-3 free, runs on a laptop, and is interactive at the cell level with 14ms response.

## Q6: "Are there other tools that have interactive drag-to-replace?"

> In the cell-level placement space (where this project focuses), no. Related tools exist in adjacent layers: Chipmind has interactive drag-to-replace for RTL design (you drag modules, the AI writes Verilog); Altium and Cadence Allegro have drag-to-replace for PCB design (circuit boards, not chips); Quadcept has it for schematic capture. But cell-level placement on a silicon die has been exclusively batch-only in commercial, academic, and open-source tools. That's the gap SmallChip AI fills.

## Q7: "How accurate is your HPWL? Have you validated it?"

> Yes. On the GCD benchmark (734 cells, Nangate45 PDK), our placement goes through OpenROAD's own legalization and OpenROAD's own static timing analyzer. The result: 99.7% HPWL reduction (3,987,080 → 10,775 DBU, 370× improvement) with identical timing (0.52 ns WNS, 2097 MHz Fmax) and identical power (1.06 mW). This is end-to-end validated, not just the placer output.

## Q8: "How do you know your held-out test isn't contaminated?"

> We use a hash-based 80/20 split: each design gets a SHA-256 hash, we sort by hash, and take the bottom 20% as held-out. We verified 0% overlap with the training set before reporting the 100% / 87.1% number. We caught and removed an earlier 75.2% number on 91 designs that turned out to be 100% contaminated. The current 87.1% is on a clean test.

## Q9: "What is the LLM co-pilot for?"

> The user types plain English — "make this faster", "spread the analog cells", "reduce power". The LLM (Ollama phi3:mini, local) translates the prompt to a 5-dimensional preference vector (HPWL, Power, Area, Timing, Congestion). The placer uses this as a guide. Critically, the chip is always the best possible version of itself — the LLM shapes the report, not the placement. This way the user gets both correctness (always-optimized chip) and usability (plain English interface).

## Q10: "What about congestion, timing, thermal?"

> V3 currently optimizes only HPWL. V4 (in development) has multi-objective loss: HPWL + congestion + thermal + spread, with rebalanced weights. The infrastructure is in place; the retrain is in progress. We also have separate congestion and thermal estimators in `chipmind/ml/quality.py`.

## Q11: "Have you fabricated a chip?"

> Not yet. The GDS export is working (94KB valid GDSII v2.88 for the GCD design). The next step is efabless Skywater 130nm shuttle submission, which is free and takes 2-4 months for the chip to come back. That's planned for Phase 2.

## Q12: "Will this work for big chips like GPUs?"

> No. We target 1-15K cells (90% of the world's chips — hearing aids, key fobs, IoT, etc.). For 1M+ cell GPUs, our hierarchy + OpenROAD works but isn't yet as polished as Cadence. The architecture is the same; the polish is missing.

## Q13: "How long did this take?"

> About 6 months of work, ~500 hours of code. Most of that was debugging, not coding. The breakthrough was the 18K-parameter GAT + the hierarchical extension to 30M cells.

## Q14: "Who paid for this?"

> Nobody. BSD-3 open source. Built by a 14-year-old in Strongsville, OH. $0 spent on tools (BSD-3 license, free Python libs, free cloud GPU for V4 retrain). The only costs are the optional Apple Developer ID ($99) for signing the desktop .app, and cloud compute for the 100M-cell scaling proof.

## Q15: "What is the real-world impact?"

> Per our savings calculator:
> - 1-engineer company: $37,500/year saved (engineering time + EDA tool replacement)
> - 2-engineer company: $45,000/year
> - 5-engineer company: $67,500/year
> - University ECE lab (10 students): $200,000/year in seat-license savings
>
> Total addressable market: 1,000+ small chip companies × ~$40K = $40M/yr in the US; 5,000+ university courses × $50K = $250M/yr.

## Q16: "Why BSD-3 license?"

> BSD-3 lets anyone use the code commercially for free, modify it, and redistribute. No copyleft, no "share-alike" requirement. This maximizes adoption — small chip companies, universities, developing countries can all use it without legal complications. We want this to be the default open-source interactive placer, not a product.

## Q17: "What's the open-source EDA ecosystem missing?"

> Before SmallChip AI, every step in the chip design flow had a free, open-source tool:
> - PDK: Skywater 130nm (open)
> - Synthesis: Yosys (open)
> - Floorplan: (no good open option, but tools exist)
> - Placement: RePlAce (in OpenROAD, batch only, diverges on hard designs)
> - CTS, Routing, DRC: OpenROAD, KLayout
> - Cores: RISC-V
>
> The "interactive placement" layer was the missing piece. SmallChip AI fills it.

## Q18: "What's your biggest weakness?"

> The 5K-cell V3 HPWL plateau at ~243K (cell_w=6.0 µm) — we know this is a hard wall for the current V3 model. V4 is being retrained with multi-objective loss to push below 200K. Also: no physical chip in hand yet (efabless pending), no academic co-author (50 cold emails planned), no DREAMPlace head-to-head on same hardware (DREAMPlace not installed locally).

## Q19: "Can I try it?"

> Yes. github.com/hnelabhotla-boop/smallchip-ai. BSD-3. Clone, install, run. The web app is at localhost:8000/copilot. The desktop .app is in the releases. The arxiv preprint is in /paper/.

## Q20: "What's next?"

> V4 multi-objective retrain (this week). 100M-cell head-to-head with DREAMPlace on adaptec1 + bigblue1 (next week). efabless chip submission (next month). 1+ academic co-author (50 cold emails by Sept 14). arXiv preprint submission. Beta testers (5+ students). ISEF paper polish. NEOSEF Feb 2027 → ISEF May 2027.
