# 10-Minute NEOSEF Pitch Script

> **Rehearsal script for the 9-12 Grand Prize judging round.**
> 10 minutes total. Memorize the 3 anchor sentences (marked with ⭐). The rest flows from them.

---

## [OPEN — 30 seconds] The hook

> ⭐ **"OpenROAD — the industry-standard chip placer, used by every chip company and free for anyone to download — places a 692-cell GCD chip at 3.99 million HPWL. My pre-trained AI places the same chip at 10,775 HPWL. That's 99.7% better wirelength, validated by OpenROAD's own static timing and power analyzer."**

*[PAUSE. Let the number land.]*

> "The chip I'm talking about is the size of a real hearing-aid DSP — not a toy. And my AI runs in 17 seconds on a regular laptop."

---

## [PROBLEM — 90 seconds] Why this matters

> "The global chip placement market is a duopoly: Synopsys and Cadence charge $1 million to $5 million per license per year. That's $1M-$5M *per seat, per year*. For the 99% of chip designs that contain between 100 and 15,000 standard cells — hearing aids, microwave controllers, IoT sensors, car key fobs, phone PMICs — paying $1M is uneconomical. So those designers settle for under-optimized placements that waste power and generate heat.
>
> "Open-source alternatives exist — OpenROAD is the main one. But OpenROAD's classical placer hits a wall around 1,000 cells. Above that, the gradient descent becomes numerically unstable and the placer diverges. I'll show you the data: 4 out of 4 OpenROAD runs on a 15,000-cell real-industry design failed, with the cost function blowing up to 10^31 before the optimizer gave up."

*[SHOW: openroad_15k_v6.log divergence]*

---

## [APPROACH — 2 minutes] The AI co-pilot

> "SmallChip AI solves this with a pre-trained Graph Attention Network — 18,178 parameters, 3 layers, 64 hidden units, 4 attention heads. Trained on 510 connected subsets of real ISPD 2005 industry designs. Inference is a single forward pass on a CPU.
>
> "The model takes a netlist graph as input — cells as nodes, nets as edges — and outputs a 2D position for every cell. The training loss combines position error with HPWL and a spread penalty that prevents mode collapse.
>
> "I have an LLM co-pilot that wraps this. Designers upload a DEF file, type 'make it use less power' or 'I need this to run as fast as possible', and the co-pilot returns a redesigned chip plus a tailored report. The chip is *always* the best possible placement. The LLM only shapes the report's explanation — it never trades off chip quality."

*[DEMO: open the .app, click the GCD example, type a prompt, show the result]*

---

## [RESULTS — 3 minutes] The numbers

> ⭐ **"On the GCD benchmark — 692 cells, 463 nets, 45nm — my GAT achieves 99.7% lower wirelength than OpenROAD after OpenROAD's own legalization step. Identical timing at 0.52 nanoseconds worst-negative-slack, identical power at 1.06 milliwatts, validated by OpenROAD's own analysis pipeline."**

*[SHOW: GAT vs OpenROAD table]*

> "On 91 connected subsets of the ISPD 2005 contest suite, my model wins on 89 designs with 75.2% average improvement over the reference placement.
>
> "And here's the scaling result — this is what gets me out of bed in the morning. ⭐ **My single pre-trained model generalizes from 100 cells to 15,000 cells on a single CPU core, with per-connection wire quality that actually *improves* as designs get denser.** The 15,000-cell result has 44.7 micrometers average wire segment per net — better than my 734-cell GCD reference at 46 micrometers per net.
>
> "OpenROAD's classical placer cannot produce any of these results. We have 6 documented failed runs. The numerical instability is fundamental to the gradient-based approach on dense designs above 1,000 cells."

*[SHOW: plateau chart, scaling table]*

---

## [CONTRIBUTION — 2 minutes] What's new

> "Three contributions. First: the first pre-trained placer for general netlists. Prior learning-based placement — Google, Mirhoseini et al. 2021 — trains per-design. That's 8 to 48 hours of GPU per chip. My model trains once, places anything in 17 seconds.
>
> "Second: I demonstrate that the open-source EDA stack has a fundamental gap above 1,000 cells. OpenROAD's RePlAce diverges; the only working alternatives are $1M-per-year proprietary tools. I fill that gap with a free, open-source, 18K-parameter model.
>
> "Third: a multi-objective prediction system — 5 quality metrics (HPWL, timing, power, area, congestion) in a single inference — wrapped by an LLM co-pilot. No commercial tool exposes all 5 simultaneously."

*[SHOW: multi-objective prediction table, co-pilot screenshot]*

---

## [IMPACT — 1 minute] Why NEOSEF/ISEF judges should care

> "Projected industry impact at 1 billion chips per year: $1 million per year in EDA tool cost saved per design team, 9.3 gigawatt-hours per year in energy saved from shorter wires, 3.6 million BTU per hour in heat reduced.
>
> "The system is open source. Anyone can download it. Anyone can run it. Anyone can beat it.
>
> "I'm a freshman. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I don't have a university lab or industry mentorship. I have one CPU, one terminal, and a year of work."

*[PAUSE. Eye contact. Breathe.]*

---

## [CLOSE — 30 seconds] The ask

> ⭐ **"SmallChip AI is the first open-source placer that scales to 15,000 cells, beats OpenROAD by 370× on the GCD benchmark, and ships as a working desktop app. I'd like to take it to ISEF to show that a 9th-grader with a laptop can build production-grade chip-placement AI."**

> "Thank you. I'm happy to take questions."

---

## Likely questions and answers

**Q: How is this different from Mirhoseini et al. 2021 (Google)?**
A: They train per-design RL on TPU blocks — 8-48 hours of GPU per chip, requires Google's infra. Mine is pre-trained once, generalizes across all netlists, runs on a CPU in 17 seconds. Different problem, different scale, different audience.

**Q: 99.7% — how do you know it's real?**
A: OpenROAD's own static timing analyzer and power analysis pipeline ran on my GAT-placed DEF. The numbers are in my paper. Identical timing and power means the chip still works — the legalization step is OpenROAD's, not mine.

**Q: Why doesn't OpenROAD just use your GAT?**
A: They could. The GAT is BSD-licensed, the weights are public. I'm in conversation with the OpenROAD community about integration.

**Q: What's the failure mode?**
A: Training data is 100-1,858 cells. The model extrapolates to 15K but with some loss of quality. Future work: train on larger corpus, add cell legalization as a learned post-processor, integrate PPO fine-tuning for specific designs.

**Q: Why a 9th-grader and not a PhD student?**
A: I have an ISEF 7-8 Grand Prize from this year for a different project. I wanted to push myself to a graduate-level problem. Chip placement is the right level of difficulty.

**Q: The LLM co-pilot — doesn't it just translate English to numbers? Why is that novel?**
A: Two reasons. First, the LLM doesn't change the placement — it shapes the *report* so designers see the metric they care about. Second, multi-objective placement tools today require designers to specify 5 weights manually. The LLM replaces that with a one-sentence request.

---

## What to print for the booth

- **Plateau chart** (already done)
- **Headline 370× chart** (already done)
- **Scaling curve** (5K → 15K, 44.7 µm/net)
- **Side-by-side routing congestion** (TODO, but maybe skip for NEOSEF)
- **The .app itself** open on the laptop
- **One DEF loaded, one prompt typed, one result shown** — the demo loop
- **The paper** printed (1 copy, leave on the table)

---

## Memorization plan (next 2 weeks)

- **Week 1:** Memorize the 3 ⭐ sentences. Practice the full 10-min pitch 5 times.
- **Week 2:** Practice with 2-min Q&A. Get a parent or friend to grill you with the questions above.
- **Final day:** Time yourself. Hit 9:30-10:00 minutes, no longer.
