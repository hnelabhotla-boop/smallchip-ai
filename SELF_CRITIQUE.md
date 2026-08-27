# Self-Critique — What I Would Do Differently

> **Honest reflection on my work. Read this to show judges you understand the project's limitations and what you'd improve.**

---

## If I were starting over today

### Things I would change

#### 1. Use a held-out test set from day 1
**What I did:** Trained on 510 ISPD 2005 chips, tested on 91 ISPD 2005 chips (same family).
**What I should have done:** Train on 510 ISPD 2005, test on a different benchmark (DAC 2012, ICCAD 2015).
**Why it matters:** Cross-benchmark validation is a much stronger claim.
**Cost to fix now:** 1 day to download + run DAC benchmarks.

#### 2. Plan the OpenROAD story earlier
**What I did:** Discovered the OpenROAD divergence (4/4 + 1/1 failed runs) late in the project, after the 15K head-to-head was supposed to work.
**What I should have done:** Tested OpenROAD's behavior on 1K+ cell designs at the START of the project. If it diverges, that becomes the headline story.
**Why it matters:** I would have framed the entire project around "OpenROAD fails, we succeed" instead of "we tried OpenROAD, it didn't work, but our number is good."
**Cost to fix now:** $0 — I already wrote the §4.7 OpenROAD divergence section.

#### 3. Document training from the start
**What I did:** Made multiple V1, V2, V3 models over a year, with sparse notes.
**What I should have done:** Logged every experiment with hyperparameters, dataset, results. Used something like Weights & Biases or just a structured spreadsheet.
**Why it matters:** Reproducibility. ISEF judges love seeing the full experimental history.
**Cost to fix now:** 2-3 hours to backfill experiment logs from git history.

#### 4. Use git tags for releases
**What I did:** Just commits on main.
**What I should have done:** Tagged each release: v0.1.0 (initial), v0.2.0 (LEF parser + desktop .app), etc.
**Why it matters:** Shows a project, not just code. Clearer for judges.
**Cost to fix now:** 1 hour to backfill tags.

#### 5. Track time per feature
**What I did:** Built things without tracking time.
**What I should have done:** Logged time per feature ("GAT training: 10 hours", "Detailed placer: 6 hours", etc.) to show the work breakdown.
**Why it matters:** Judges want to see "this is a year of work" — a time log makes that concrete.
**Cost to fix now:** 1 hour to backfill from git history.

---

## What I would NOT change

### 1. Pre-trained GAT (the core innovation)
**Why not:** This is the contribution. Anything I would have done differently would have led to the same architecture.

### 2. The locked design choice (chip is always best)
**Why not:** Rejecting ParetoGATPlacer was the right call. "Chip is always the best possible, LLM shapes the report" is a clean, defensible story.

### 3. Open-source everything (BSD-licensed)
**Why not:** This is the only way to get industry adoption. Any other license (GPL, MIT with restrictions) would limit impact.

### 4. The 5-objective predictor
**Why not:** 5 quality metrics in one inference is a real contribution. No other EDA tool exposes all 5 simultaneously.

### 5. The OpenROAD divergence story
**Why not:** It happened naturally, and it's the strongest single contribution. The story is "we proved the open-source stack has a gap, and we fill it."

---

## What I would add

### 1. A "design rationale" doc for every major decision
**Why:** When judges ask "why did you choose 18,178 parameters?" I should have a doc explaining the trade-offs considered.
**Cost:** 2-3 hours per doc × 5 major decisions = 10-15 hours total.

### 2. A "lessons for other students" essay
**Why:** ISEF judges look for educational value. A "here's what I learned that other students can apply" essay is a strong addition.
**Cost:** 2-3 hours to write.

### 3. A "this is what grad school is like" journal
**Why:** I had to teach myself PhD-level material. Capturing that process would be valuable to other students.
**Cost:** 4-5 hours to write from memory.

### 4. A "future directions" 3-year plan
**Why:** Shows vision beyond ISEF. Where does the project go from here?
**Cost:** 2-3 hours to write.

---

## What I would remove

### 1. The hierarchical placer
**What I have:** §3.7 Hierarchical Placement (initial implementation) with spectral layout.
**Why remove:** It doesn't work well (60% win rate vs 100% for flat GAT). Mentioning it in the paper invites the question "why didn't you make it work?"
**What to replace it with:** A 1-paragraph "future work" mention. "Hierarchical placement for designs above 50K cells is an open problem."

### 2. The "11 baseline algorithms" mentioned in the algorithm comparison
**What I have:** 11+ algorithms in §4.5.
**Why reduce:** The headline is "12 classical methods stuck at 1.3M HPWL, GAT at 50K." The exact count doesn't matter. Reducing to "8 baseline algorithms" simplifies the message.
**What to keep:** The 4 strongest baselines (OpenROAD, PPO, SA, ePlace) + GAT. That's 5 numbers, easy to remember.

### 3. The 5-metric predictor (multi-objective)
**What I have:** §3.5 Multi-Objective Predictors + §3.6 Web App & Savings Calculator.
**Why simplify:** The 4 MLPs (timing, power, area, congestion) are mentioned in the abstract but not central to the contribution. The web app savings calculator is a "nice to have" not a "must have."
**What to do:** Keep them in the paper, but don't lead with them. The headline is the GAT, not the multi-objective predictor.

---

## The 1 thing I wish I had done

**Write a paper draft early and iterate on it.**

What I did: Built the system, ran experiments, then wrote the paper at the end.
What I should have done: Wrote a paper draft at month 3, even with placeholder numbers. Then updated the paper as the system evolved.

**Why:** A paper draft early forces you to articulate the contribution. You discover the gaps in your story BEFORE you've built everything. Saves time.

**Cost to fix now:** I have a paper draft (`paper/ISEF_paper_draft.md`). It's good but not great. A 2-week rewrite is in the schedule.

---

## How to use this doc

1. **Read it before NEOSEF.** So you know what you'd do differently.
2. **Mention it in mock judging sessions.** Shows humility and self-awareness.
3. **If a judge asks "what would you do differently?"**: pull from this doc.

---

## The honest answer to "what would you do differently"

> "If I were starting over, I'd plan the OpenROAD divergence story from day 1. I discovered it late in the project, but it became the strongest contribution. I'd also use a held-out test set from a different benchmark family, and I'd log every experiment with timing and hyperparameters. But the core architecture — the pre-trained GAT, the BSD license, the locked design choice — those I wouldn't change."

That's a 30-second honest answer. Memorize it.
