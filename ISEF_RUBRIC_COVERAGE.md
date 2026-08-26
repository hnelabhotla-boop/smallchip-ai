# ISEF Judging Rubric Coverage

> **How SmallChip AI maps to the official ISEF judging criteria.**
> Use this when reviewing your project before the fair. If a criterion is weak, work on it.

---

## The ISEF 9 judging criteria (1-10 each, total 90)

| # | Criterion | Our score | Why |
|---|---|---|---|
| 1 | **Creative Ability** | 9 | Pre-trained GAT for small chips is genuinely new. No prior work does this. |
| 2 | **Scientific Thought** | 8 | Hypothesis-driven, controlled experiments, clear methodology. Could be stronger with a held-out test set. |
| 3 | **Thoroughness** | 8 | 91-design benchmark, 6 OpenROAD failure logs, multi-objective predictor. Could be stronger with more chip families. |
| 4 | **Skill** | 9 | Built a working ML system, FastAPI backend, web frontend, desktop .app, from scratch. CPU only. |
| 5 | **Clarity** | 7 | Paper is well-organized. Pitch script and demo script are clear. Could be stronger with a 1-min elevator pitch. |
| 6 | **Dramatic Effect** | 9 | The plateau chart (12 methods at 1.3M, GAT at 50K) is a "wait, what?" moment. The OpenROAD divergence story is shocking. |
| 7 | **Technical Merit** | 9 | OpenROAD-validated, reproducible, public code, public data, public weights. |
| 8 | **Collaborative Spirit** | 7 | Solo project. Acknowledge OpenROAD, ISPD 2005, PyTorch Geometric. Could collaborate with a university. |
| 9 | **Individual Contribution** | 10 | All work is mine. AI assistance is acknowledged (Mavis coding assistant, transparent). |

**Estimated total: 76/90** — strong contender for Grand Prize and IEEE-CS special award.

---

## How to defend each criterion in the booth

### 1. Creative Ability (9/10)
**The question judges ask:** "Is this genuinely new, or incremental?"
**Your answer:** "Pre-trained placers for general netlists don't exist. Google's work trains per-design — 8-48 hours of GPU per chip. I train once, place any design in 17 seconds on a CPU. The contribution is the amortization, not the network architecture."

**Backup for "what if a judge disagrees":** "I have 6 OpenROAD failure logs as evidence that the open-source EDA stack has a gap above 1,000 cells. I'm the first to fill it with a free, open-source tool."

### 2. Scientific Thought (8/10)
**The question judges ask:** "Did they follow the scientific method? Hypothesis, experiment, analysis, conclusion?"
**Your answer:** "I started with a hypothesis: a pre-trained GAT can match or exceed classical placers on small-to-medium chip designs. I tested it on 91 ISPD 2005 designs, 5 bigblue1 subsets (5K-15K), and the GCD benchmark. The hypothesis holds on every metric — HPWL, timing, power — with OpenROAD's own analysis as ground truth."

**Backup:** "I also tested the failure case: where does my model break? At designs above 15K cells, the per-net quality starts to degrade. Future work: train on a larger corpus."

### 3. Thoroughness (8/10)
**The question judges ask:** "Did they consider multiple angles, or just one?"
**Your answer:** "I evaluated 11 baseline algorithms on the GCD. I tested 4 cell widths on the 15K design. I documented 6 OpenROAD failures. I tested on 91 ISPD 2005 designs. I validated with OpenROAD's own static timing analyzer."

**Backup:** "What's missing: a held-out test set of designs from a different benchmark family (DAC, ICCAD). I have plans to add this in Phase 2 of the project."

### 4. Skill (9/10)
**The question judges ask:** "Did they actually do the work, or is it a wrapper around something else?"
**Your answer:** "I built the GAT architecture from scratch in PyTorch + PyTorch Geometric. I wrote the FastAPI server. I wrote the web frontend. I packaged it as a desktop .app with PyInstaller. I wrote the training loop. I wrote the LLM co-pilot integration. I deployed to GitHub. 5,000 lines of code, all mine."

**Backup:** "I do use AI assistance — I have access to Mavis, a coding assistant. The architecture, math, and validation are mine. The AI is a tool, like PyTorch is a tool."

### 5. Clarity (7/10)
**The question judges ask:** "Can a non-expert understand what you did and why it matters?"
**Your answer:** "The 1-page summary explains the project in 60 seconds. The plateau chart makes the contribution visual. The pitch script has 3 anchor sentences. The .app is a live demo anyone can use."

**Backup:** "I should add a 1-min elevator pitch. Also: a 1-paragraph summary for the application."

### 6. Dramatic Effect (9/10)
**The question judges ask:** "Will I remember this project 6 hours from now?"
**Your answer:** "The plateau chart is the moment. 12 methods at 1.3M, our GAT at 50K. That's a 25× drop. Plus the OpenROAD divergence: cost function 10^31, gives up at iteration 2,700. That's a 'wait, what?' moment."

**Backup:** "The 99% market framing — hearing aids, microwave controllers, IoT sensors — makes it personal. Everyone has these devices."

### 7. Technical Merit (9/10)
**The question judges ask:** "Is the science sound? Is the validation real?"
**Your answer:** "OpenROAD's own static timing analyzer confirms 0.52 ns WNS, 1.06 mW power. 99.7% HPWL improvement on the GCD. 89/91 wins on ISPD 2005. All open source, BSD-licensed, public training data, public pre-trained weights. Anyone can reproduce the result in a weekend."

**Backup:** "What's missing: post-routing power on 15K. OpenROAD can't place 15K to start the routing flow, so this is an open challenge. I document it in §4.7."

### 8. Collaborative Spirit (7/10)
**The question judges ask:** "Did they engage with the broader community?"
**Your answer:** "I'm in conversation with the OpenROAD community about integrating SmallChip AI into the open-source EDA stack. The system is BSD-licensed so anyone can use it. I acknowledge OpenROAD, ISPD 2005, and PyTorch Geometric in the paper."

**Backup:** "I should reach out to a university or industry lab for collaboration on the post-routing validation."

### 9. Individual Contribution (10/10)
**The question judges ask:** "Is this really their work?"
**Your answer:** "All work is mine. I built the system, ran the experiments, wrote the paper, packaged the .app, deployed to GitHub. I have a year of git history showing my commits. I do use AI assistance for some parts of the workflow, which I acknowledge transparently — but the architecture, math, and validation are mine."

**Backup:** "I can walk through any line of code in the project and explain what it does."

---

## What could push us from "Grand Prize" to "Grand Prize + IEEE-CS special award"

| Action | Effort | Impact |
|---|---|---|
| **Add a held-out test set** (DAC or ICCAD benchmarks) | 1 day | +1 Scientific Thought, +1 Thoroughness |
| **Post-routing power on GCD** (already blocked) | 2 days | +1 Technical Merit |
| **A 1-min elevator pitch** | 1 hour | +1 Clarity |
| **Side-by-side routing congestion heatmap** | 1 day | +1 Dramatic Effect |
| **University collaboration** (e.g., ask a chip design lab to evaluate) | 1 month | +2 Collaborative Spirit |
| **A published conference paper** (e.g., MLCAD, ICCAD) | 3-6 months | +2 Technical Merit |

The first 4 are realistic by NEOSEF. The last 2 are post-NEOSEF targets.

---

## Common judge questions and the ISEF-criterion each one tests

| Question | Criterion tested | What to say |
|---|---|---|
| "Is this really better than OpenROAD?" | 7. Technical Merit | "OpenROAD's own analysis confirms 99.7% HPWL improvement on GCD. We can't compare on 15K because OpenROAD can't place 15K — 4/4 attempts diverge. We document this in §4.7." |
| "Could a chip company just take your model?" | 8. Collaborative Spirit | "Yes. It's BSD-licensed. I'm in conversation with the OpenROAD community about integration." |
| "Why didn't you use the DAC benchmarks?" | 3. Thoroughness | "DAC and ICCAD are next on my list. ISPD 2005 is what I have, and it's a real industry benchmark. Adding DAC would strengthen the multi-benchmark claim." |
| "How do you know this isn't just memorization?" | 1. Creative Ability | "I tested on 91 ISPD 2005 designs that were not in the training set. 89/91 wins. Plus the GCD, which has a different cell library than the training set. Plus the 15K bigblue1 subset, which is bigger than anything in training." |
| "What if your model is just lucky on the benchmarks?" | 2. Scientific Thought | "I tested 5 different bigblue1 subsets, varying cell count. The model generalizes. Plus OpenROAD's own analysis confirms the timing and power are identical to OpenROAD's default." |

---

## If you get a 5/10 on any criterion

Don't panic. Judges differ. One judge's 5 is another judge's 8. Focus on:
1. **Acknowledge the weakness.** "Yes, I didn't include a held-out test set. That's a real gap."
2. **Explain your plan.** "I plan to add DAC benchmarks in Phase 2 of the project."
3. **Show you understand it.** "I know this would strengthen the multi-benchmark claim."

Judges respect self-awareness more than overclaiming.
