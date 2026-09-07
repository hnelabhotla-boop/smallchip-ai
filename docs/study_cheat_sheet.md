# SmallChip AI — 5-min Study Cheat Sheet

Read this on the bus ride to school. Memorize these 12 numbers. You'll be asked every one of them.

---

## THE 12 NUMBERS (memorize these)

| # | What | Number |
|---|---|---|
| 1 | GCD improvement | **99.7% / 370×** (3,987,080 → 10,775) |
| 2 | GCD timing | 0.52 ns WNS, 2097 MHz (identical to OpenROAD) |
| 3 | GCD power | 1.06 mW (identical to OpenROAD) |
| 4 | Held-out test | **100% win rate, 87.1% avg, 87.5% median, 66 designs** |
| 5 | Inference on 15K cells | **150ms** (CPU) |
| 6 | Partial re-place (drag) | **14ms for 71 cells** |
| 7 | Hierarchy proven | **30,000,000 cells** in 50s |
| 8 | Hierarchy projected | 100,000,000 cells |
| 9 | Model size | **18,000 parameters** |
| 10 | Training data | 510 designs (synthetic + ISPD 2005) |
| 11 | Per-company value | $37,500/yr (1 engineer) to $67,500/yr (5 engineers) |
| 12 | License | **BSD 3-Clause** (commercial use OK, no copyleft) |

## THE 4 CLAIMS (memorize these)

1. **First free, BSD-3 open-source real-time interactive cell-level chip placement tool** (Chipmind does RTL, Altium/Allegro do PCB, no one does cell-level placement interactively)
2. **First BSD-3 placer with an LLM co-pilot** (no other tool has this)
3. **First end-to-end open-source chip design flow with free interactive placement** (Skywater + Yosys + OpenROAD + KLayout + RISC-V were all open; we fill the placement gap)
4. **First end-to-end proof that interactive placement scales to 30M cells** (50 seconds)

## THE 5 NAMES YOU MIGHT BE ASKED ABOUT

- **Cadence Innovus** ($500K-$1M/yr, batch, 20-60 min)
- **Synopsys IC Compiler II** ($500K-$1M/yr, batch)
- **OpenROAD** (BSD-3 free, but batch, often diverges on hard designs)
- **DREAMPlace** (academic SOTA, GPU-accelerated, 30 min on V100, batch)
- **RePlAce** (the placer inside OpenROAD; we document it fails to converge on 15K bigblue1)

## THE 5 TOOLS YOU MIGHT BE ASKED ABOUT (in adjacent layers)

- **Chipmind** — RTL design with drag-to-replace. Different layer (we do placement, they do RTL).
- **Altium Designer** — PCB design, not chips. Different domain.
- **Cadence Allegro X** — PCB design, not chips.
- **Quadcept** — Schematic capture, not placement.
- **Siemens EDA** — PCB + schematic, not cell-level placement.

## THE 3 TOOLS IN OUR ECOSYSTEM (open source)

- **Skywater 130nm** — open PDK
- **Yosys** — open synthesis
- **OpenROAD** — open place-and-route (we complete this layer with interactive)

## THE 4 THINGS WE'RE MISSING (honest weaknesses)

1. **5K V3 HPWL plateau at 243K** (V4 retrain fixes this, in progress)
2. **No academic co-author** (50 cold emails planned)
3. **No physical chip in hand** (efabless pending)
4. **No DREAMPlace head-to-head on same hardware** (DREAMPlace not installed locally yet)

## THE 5 THINGS YOU MUST SAY IF ASKED "WHAT IS NEW?"

1. "First free real-time interactive cell-level placer" (no commercial or academic tool has this for placement)
2. "First BSD-3 placer with an LLM co-pilot"
3. "First end-to-end open-source chip design flow with free interactive placement"
4. "First interactive placement proven to scale to 30 million cells"
5. "99.7% GCD improvement, identical timing + power, validated by OpenROAD's own analyzer"

## THE PITCH (60 sec, memorize)

> "Every chip in the world needs placement. Industry tools cost $500K to $1M per year per seat. The open-source tool, OpenROAD, is free but it runs as a batch job that takes 5 to 30 minutes per placement and often diverges on hard designs. There is no free, real-time, interactive placer for cells on a chip die.
>
> I'm a 14-year-old and I built SmallChip AI. It uses a graph attention network with 18,000 parameters — small enough to run on a laptop, fast enough to give a 150-millisecond response. You can drag a cell on a canvas and see the chip re-place in 14 milliseconds. You can type 'make this faster' in plain English and the chip re-places.
>
> On the GCD benchmark with 734 cells, after OpenROAD's own legalization and static timing analysis, our placement achieves 99.7% wirelength reduction — that's 370 times better — with identical timing and identical power. On a clean held-out test of 66 designs, we win on 100% of them, with 87.1% average improvement.
>
> The architecture scales to 30 million cells, proven end-to-end. The whole thing is BSD-3 open source on GitHub, free for anyone to use. We're the missing piece in the open-source EDA ecosystem — Skywater, Yosys, OpenROAD, KLayout, and RISC-V were all open, but no one had a free interactive placer until now."

## THE Q&A SHORTCUTS

**"How is this different from Chipmind?"**
"Chipmind does RTL design — they help you write Verilog by dragging modules. We do cell-level placement — we put cells on the die after the code is written. Different layer, different problem. Both are AI for chip design, but they're complementary."

**"How is this different from OpenROAD?"**
"OpenROAD is a full RTL-to-GDS flow with batch placement. We do real-time interactive placement. We're complementary — for detailed routing and CTS, OpenROAD is still the way. For interactive placement, we win."

**"How is this different from DREAMPlace?"**
"DREAMPlace is GPU-accelerated batch placement. ~30 minutes on a V100 for 211K-cell adaptec1. We're CPU + small model, real-time, with an LLM co-pilot. Different optimization regime."

**"How do you know your test isn't contaminated?"**
"We use a hash-based 80/20 split — each design gets a SHA-256 hash, we sort by hash, take the bottom 20% as held-out. We verified 0% overlap with training before reporting the 100% number. We caught and removed an earlier 75.2% number on 91 designs that turned out to be 100% contaminated. The current 87.1% is on a clean test."

**"What is your biggest weakness?"**
"5K V3 HPWL plateau at 243K with cell_w=6 microns. V4 multi-objective retrain in progress. Also: no academic co-author yet, no physical chip in hand, no DREAMPlace head-to-head on same hardware. All of these are being worked on."

## NUMBERS YOU MIGHT BE ASKED

- 8,000× faster than industry: based on 30 min industry vs 150ms ours on 15K cells
- 5K-15K scaling: 355K-540K HPWL, 41-85 µm/net (monotonically decreasing)
- 66 designs in held-out: 8 small (<200 cells, 93.9% avg), 56 medium (200-600, 86.1% avg), 2 large (≥600, 88.0% avg)
- 30M scaling: 1,281,714 DBU/net, 50.6s workers, 12GB peak memory
- BSD-3 license: no copyleft, no "share-alike", use commercially for free
- Per-company value: $37,500/yr (1 engineer) to $67,500/yr (5 engineers), $200K/yr (10-student university lab)

## WHAT TO DO IF YOU DON'T KNOW

"It's a good question. I haven't measured that specifically, but the closest data we have is [X]. I'd want to come back with a real number rather than guess."

NEVER make up a number. NEVER say "I think" without a citation. If you don't know, say so and offer to follow up.

## AFTER ISEF (if you win, what comes next)

- V4 retrain
- 100M head-to-head with DREAMPlace
- efabless chip tapeout
- 1+ academic co-author
- 5+ beta testers
- arXiv submission
- Demo video
- 50 cold emails
- ISEF paper polish
- NEOSEF Feb 2027 → ISEF May 2027
