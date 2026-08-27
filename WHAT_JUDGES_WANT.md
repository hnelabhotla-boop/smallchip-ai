# What Judges Want to Hear

> **Based on ISEF judging criteria, here's what judges are actually listening for.**
> Map each criterion to the line you should say.

---

## The 9 ISEF judging criteria, decoded

Judges score 1-10 on each. Total: 90 points. Threshold for special awards: usually 75+. Threshold for Grand Prize: usually 80+.

For each criterion, here's what they're listening for AND the line that nails it.

---

### 1. Creative Ability (target: 9/10)

**What they're listening for:** "Is this genuinely new, or is it an incremental improvement on prior work?"

**What they want to hear:** A specific statement of novelty. Not "this is a great project" — they want "this specific thing has never been done before."

**Your line:** "SmallChip AI is the first pre-trained placer for general netlists. Google's 2021 Nature paper trains per-design and takes 8-48 hours of GPU per chip. I train once, place any design in 17 seconds on a CPU. The contribution is the amortization, not the network architecture."

**Backed by:** Mirhoseini 2021 (Nature) — their prior work; no one has done pre-trained before.

---

### 2. Scientific Thought (target: 9/10)

**What they're listening for:** "Did this student follow the scientific method? Hypothesis, experiment, analysis, conclusion?"

**What they want to hear:** A clear hypothesis-driven narrative. "I hypothesized X, tested Y, found Z, concluded W."

**Your line:** "I hypothesized that a pre-trained Graph Attention Network could match or exceed classical placers on small-to-medium chip designs. I tested this on 91 ISPD 2005 connected subsets, 5 bigblue1 subsets (5K-15K cells), and the GCD benchmark. The hypothesis holds: 99.7% / 370× better on GCD, 89/91 wins on the multi-design benchmark, 31.8 µm per net on 15K (better than the 734-cell reference)."

**Backed by:** Clear methodology in §3 of the paper.

---

### 3. Thoroughness (target: 8/10)

**What they're listening for:** "Did this student consider multiple angles, or just one?"

**What they want to hear:** A list of angles explored. "I tested X, Y, and Z. I considered A, B, and C."

**Your line:** "I evaluated 11 baseline algorithms on the GCD. I tested 5 cell widths on the 15K design. I documented 6 OpenROAD failures. I tested on 91 ISPD 2005 designs. I validated with OpenROAD's own static timing and power analysis. I considered 7 alternative architectures before settling on the 3-layer 64-hidden 4-head GAT."

**Backed by:** §4 of the paper has all the tables.

---

### 4. Skill (target: 9/10)

**What they're listening for:** "Did this student actually do the work, or is this a wrapper around something else?"

**What they want to hear:** A specific list of what you built. "I wrote 5,000 lines of code, designed the architecture, trained the model, packaged the .app, deployed to GitHub."

**Your line:** "I built the GAT architecture from scratch in PyTorch + PyTorch Geometric. I wrote the FastAPI server. I wrote the web frontend. I packaged it as a desktop .app with PyInstaller. I wrote the training loop. I wrote the LLM co-pilot integration. I deployed to GitHub. 5,000 lines of code, all mine. I do use AI assistance for some parts of the workflow, which I acknowledge transparently — but the architecture, math, and validation are mine."

**Backed by:** GitHub repo with commit history showing 6+ months of work.

---

### 5. Clarity (target: 9/10)

**What they're listening for:** "Can a non-expert understand what I did and why it matters?"

**What they want to hear:** A clear, simple explanation. "I built X. It does Y. It matters because Z."

**Your line:** "I built a free, open-source AI chip placer. The 99% of chip designs that can't afford $1M EDA licenses can now use my pre-trained AI to get the same quality placement as the industry tools. On the standard GCD benchmark, I'm 99.7% better than OpenROAD — validated by OpenROAD's own analysis."

**Backed by:** 1-page summary, pitch script, demo video.

---

### 6. Dramatic Effect (target: 9/10)

**What they're listening for:** "Will I remember this project 6 hours from now? Is there a moment?"

**What they want to hear:** A "wait, what?" moment. A counter-intuitive finding. A visual.

**Your line:** [Point at the plateau chart] "12 classical methods — simulated annealing, ePlace, PPO, memetic, genetic — they all get stuck at 1.3 million HPWL on the GCD benchmark. Our pre-trained GAT drops to 50,000. After OpenROAD's own legalizer, we hit 10,775. OpenROAD's default gets 3.99 million. **That's 370 times better, validated by OpenROAD's own static timing and power analysis.**"

**Backed by:** Plateau chart, scaling chart, OpenROAD divergence logs.

---

### 7. Technical Merit (target: 9/10)

**What they're listening for:** "Is the science sound? Is the validation real?"

**What they want to hear:** A specific validation claim. "I used the industry standard tool to validate, and the numbers match."

**Your line:** "OpenROAD's own static timing analyzer confirms 0.52 ns WNS, 2097 MHz max frequency, 1.06 mW total power. Identical to OpenROAD's default placement. The chip still works. 89/91 wins on the multi-design benchmark. 31.8 µm per net at 15K. All open source, BSD-licensed, public training data, public pre-trained weights. Anyone can reproduce the result in a weekend."

**Backed by:** §4.1 of the paper, the ISEF paper.

---

### 8. Collaborative Spirit (target: 7/10)

**What they're listening for:** "Did this student engage with the broader community?"

**What they want to hear:** Specific collaborations or community engagement. "I cite X, Y, Z. I built on prior work. I plan to integrate with OpenROAD."

**Your line:** "I built on Google's 2021 Nature paper, Veličković's 2018 GAT paper, OpenROAD's toolchain, and the ISPD 2005 benchmarks. I'm in conversation with the OpenROAD community about integrating SmallChip AI into the open-source EDA stack. The system is BSD-licensed so anyone can use it, including commercial chip companies."

**Backed by:** §6 References in the paper, ANNOTATED_BIBLIOGRAPHY.md.

---

### 9. Individual Contribution (target: 10/10)

**What they're listening for:** "Is this really their work?"

**What they want to hear:** Unambiguous ownership. "I built this. All of it. With AI assistance acknowledged."

**Your line:** "All work is mine. I built the system, ran the experiments, wrote the paper, packaged the .app, deployed to GitHub. I have a year of git history showing my commits. I do use AI assistance for some parts of the workflow, which I acknowledge transparently — but the architecture, math, and validation are mine. I can walk through any line of code in the project and explain what it does."

**Backed by:** GitHub commit history, ability to defend any line of code.

---

## The composite: what wins the Grand Prize

To win Grand Prize (80+ out of 90), you need:

1. **Strong on the 5 high-weight criteria** (Creative Ability, Scientific Thought, Skill, Clarity, Dramatic Effect) — aim for 9/10 each.
2. **Solid on the 3 medium-weight criteria** (Thoroughness, Technical Merit, Collaborative Spirit) — aim for 8/10 each.
3. **Perfect on the 1 mandatory criterion** (Individual Contribution) — aim for 10/10.
4. **A memorable moment** — the plateau chart, the OpenROAD divergence, the 99.7% / 370× number.

Score: 9×5 + 8×3 + 10 = 79. Push to 85 with the wow moment.

---

## What judges HATE

- **Faking depth.** If you can't explain the math, don't put it in the paper.
- **Apologizing.** Frame limitations as future work.
- **Reading from notes.** Memorize the pitch.
- **"I think maybe possibly..."** Be definitive. You have data.
- **Burying the headline.** Lead with the 99.7% / 370× number.
- **Lying about scale.** "Industry-changing" is a strong claim. Have the evidence.
- **Forgetting the human element.** "I'm a 9th grader, one CPU, one year" is your superpower.

---

## What judges LOVE

- **A "wait, what?" moment.** The plateau chart. The OpenROAD divergence. The per-connection quality improvement.
- **Honest limitations.** "I haven't done X yet. Here's why. Here's my plan."
- **A working system.** A judge who clicks a button and sees a result is a happy judge.
- **A clear contribution.** "I am the first to do X. Here's the evidence."
- **Open source.** "Anyone can verify. Anyone can build on my work."
- **The personal story.** "I'm a 9th grader. I built this with one CPU and a year of work."

---

## The 30-second "elevator" version

If a judge has 30 seconds, say this:

> "I'm Harshith. I built SmallChip AI, a free, open-source AI chip placer. The 99% of chip designs that can't afford $1M EDA licenses can now use my pre-trained AI. On the GCD benchmark, I'm 99.7% / 370× better than OpenROAD — validated by OpenROAD's own analyzer. The system is BSD-licensed, public data, public weights, downloadable as a macOS app. I'm a 9th grader with one CPU and a year of work."

That's the entire story. Memorize it. Adapt the details for different judges.

---

## The 5-min "moderator" version

If a judge has 5 minutes:

1. **Headline** (30 sec): 99.7% / 370× on GCD, 31.8 µm per net at 15K.
2. **Problem** (1 min): 99% of chip designs can't afford $1M EDA. OpenROAD fails above 1K cells.
3. **Solution** (1 min): Pre-trained GAT, 18,178 params, 17 sec on CPU, BSD-licensed.
4. **Demo** (1 min): Click GCD, click compare, show 99.7% improvement. Type "less power" in co-pilot, show tailored report.
5. **Close** (30 sec): I'm a 9th grader. One CPU. A year of work. Open source. Anyone can use it. Anyone can beat it.

---

## The 10-min "deep" version

If a judge has 10 minutes, do the 5-min version, then add:

- **The scaling story** (1 min): per-connection quality improves as designs get bigger. 31.8 µm at 15K vs 46 µm at GCD.
- **The plateau chart** (1 min): 12 classical methods stuck at 1.3M, GAT at 50K. The visual wow.
- **The OpenROAD divergence** (1 min): 4/4 + 1/1 = 6/6 OpenROAD runs fail on 1K+ cell designs. The numerical story.
- **The LLM co-pilot** (1 min): Natural language → 5-dim preference vector → tailored report. The chip is always the best possible.

That's the full pitch. Memorize the structure, not the words.

---

## How to use this doc

1. **Read it once.** So you know the structure.
2. **Pick 1-2 lines per criterion** that resonate with you. Make them your own.
3. **Practice the 30-second, 5-min, and 10-min versions** with a friend.
4. **Time yourself.** 30 sec, 5 min, 10 min. Target: 25 sec, 4:30, 9:30.
5. **Record yourself** (audio). Listen back. Look for "um", pauses, fast speech.

The pitch is muscle memory. Build it before NEOSEF.
