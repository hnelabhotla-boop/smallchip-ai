# Open Issues — Honest Limitations

> **What's NOT done. What I would do with more time. Why ISEF judges will respect this doc.**
> Intellectual honesty = ISEF credibility.

---

## The 7 open issues (ranked by impact)

### Issue 1: Post-routing power on 15K

**Status:** ❌ Not done
**What it is:** OpenROAD's full flow (placement → CTS → routing → power analysis) on the 15K bigblue1 subset.
**Why it matters:** The current "identical power" claim on GCD is from static analysis, not post-routing. On 15K, we don't have any power number yet (because OpenROAD can't place 15K to start the routing flow).
**What I plan to do:** Get the 15K routed by our own GAT-placed output using a custom router, or use industry tools via a university partner.
**Time estimate:** 4-8 hours with custom router, 1+ month with university collaboration.

**Why I'm telling you this:** So the paper has a clear "future work" section. So judges don't have to ask. So the project looks honest.

---

### Issue 2: Held-out test set from a different benchmark family

**Status:** 🟡 Partial (GCD is held out, but from same source family)
**What it is:** DAC 2012 or ICCAD 2015 benchmarks, completely separate from ISPD 2005.
**Why it matters:** The 91-design benchmark is ISPD 2005 connected subsets. To prove the model truly generalizes, we need to test on a different benchmark family.
**What I plan to do:** Download DAC 2012 and ICCAD 2015, run the V3 GAT on the largest designs, report win rates.
**Time estimate:** 4-6 hours.

**Why I'm telling you this:** When a judge asks "have you tested on anything besides ISPD 2005?", the answer is "GCD, which is from OpenROAD's own test suite, and that's 99.7% better. DAC/ICCAD is in Phase 2 of the project."

---

### Issue 3: Timing-driven placement

**Status:** ❌ Not done
**What it is:** Currently the V3 loss function optimizes HPWL only. Industry tools optimize HPWL + timing simultaneously.
**Why it matters:** A timing-driven placer can avoid critical path violations. For real chip designs, this is essential.
**What I plan to do:** Add a timing term to the V3 loss. Compute timing from estimated wire RC, add as a constraint. Retrain.
**Time estimate:** 2-3 weeks of work (timing analysis is non-trivial).

**Why I'm telling you this:** This is the most important "future work" item. It's why ISEF judges will say "this is a PhD-level project" — there's a clear research path forward.

---

### Issue 4: Real-routed GCD power (full OpenROAD flow)

**Status:** 🟡 In progress (planned for Saturday)
**What it is:** Run OpenROAD's full flow (placement → CTS → routing → power analysis) on the GCD with our GAT-placed DEF as input. Get the routed power number, not the placement-stage estimate.
**Why it matters:** Replaces an un-defended claim with a defended one. The current "1.06 mW" is from OpenROAD's static analyzer, not a routed power simulation.
**What I plan to do:** Install OpenROAD locally (brew install), run the full flow on both OpenROAD-placed and SmallChip-AI-placed GCD, compare routed power.
**Time estimate:** 4 hours.

**Why I'm telling you this:** This is the next 1 thing on my list. The single highest-leverage move left.

---

### Issue 5: Fast-SA polish after detailed placement

**Status:** ❌ Not done
**What it is:** Run fast simulated annealing (numpy-vectorized) on top of the GAT + detailed placer output. Could push 15K legal HPWL below 400K.
**Why it matters:** Better headline number. The 15K report's "Option B+C" plan: fast SA on top of V3+detailed-placer.
**What I plan to do:** Rewrite the SA in numpy, run polish loop, see if it improves.
**Time estimate:** 1-2 days.

**Why I'm telling you this:** The 418,115 result is great, but there's room to push lower. SA is the next tool to try.

---

### Issue 6: Training on a larger corpus (DAC + ICCAD)

**Status:** ❌ Not done
**What it is:** V3 is trained on 510 ISPD 2005 connected subsets (max 1,858 cells). DAC 2012 and ICCAD 2015 have larger designs.
**Why it matters:** Larger training corpus = better generalization to larger designs. The 80-epoch V3 retrain overnight uses the same 510 chips.
**What I plan to do:** Download DAC 2012 (~5-10 GB), extract connected subsets, retrain V3 on the combined corpus.
**Time estimate:** 1 week (download + extract + retrain + evaluate).

**Why I'm telling you this:** This is Phase 2 of the project. The current 510-chip corpus is a starting point. Scaling to 5,000+ chips is the path to 100K-cell designs.

---

### Issue 7: Visualizing per-net quality (vs cell count)

**Status:** 🟡 Partial (scaling chart done, per-net-by-size plot done)
**What it is:** A plot showing per-net HPWL vs design size, demonstrating that per-connection quality improves as designs get bigger.
**Why it matters:** This is the counter-intuitive finding. The current scaling chart shows it, but a separate "per-net quality" plot with more granularity would be more compelling.
**What I plan to do:** Add a 5K-15K sweep with more data points (6K, 7K, 9K, 11K, 12K, 13K, 14K).
**Time estimate:** 2-3 hours of compute.

**Why I'm telling you this:** Visualizations are ISEF ammunition. A "per-net quality improves as designs get bigger" plot is the kind of "wait, what?" moment judges remember.

---

## What's NOT in the project (and why)

### ❌ Tape-out / fabricated chip
- **Why not:** Costs $1M+ and requires foundry access.
- **Impact:** None — placement tools are validated by simulation, not fabrication.

### ❌ Comparison to Cadence Innovus or Synopsys ICC
- **Why not:** Industry tools cost $1M+ per license. I can't legally run them.
- **Impact:** Could strengthen the comparison, but not blocking NEOSEF.

### ❌ RL fine-tuning on specific designs
- **Why not:** Per-design RL takes 8-48 hours of GPU. Not feasible for a high school project.
- **Impact:** Future work. Mirhoseini 2021 does this; we don't.

### ❌ Cross-benchmark validation
- **Why not:** DAC and ICCAD benchmarks need to be downloaded and preprocessed. Time.
- **Impact:** Would strengthen the multi-benchmark claim. In Phase 2.

### ❌ Learned legalization
- **Why not:** Open research problem. The current hand-coded detailed placer works fine.
- **Impact:** Could push 15K below 400K. Future work.

### ❌ Timing-driven placement
- **Why not:** Requires integrating OpenROAD's STA into the training loop. Non-trivial.
- **Impact:** Required for ISEF special awards. In Phase 2.

---

## The intellectual-honesty move

If a judge asks about any of these, the answer is:

> "I haven't done that yet. Here's why: [reason]. Here's my plan: [future work]. Here's what I did do: [what's done]."

That's the move. Don't fake it. Don't overclaim. State the limitation, explain the plan, and pivot to what's done.

---

## How to use this doc

1. **Read it before NEOSEF.** So you know what to say when judges ask.
2. **Cite it in the paper's future work section.** So the paper's gaps are documented.
3. **Update it after the fair.** As you close issues, mark them done.

---

## What I will do (committed)

- [ ] Saturday Aug 30: Real-routed GCD power (Issue 4)
- [ ] Sunday Aug 31: Side-by-side routing heatmap (booth wow)
- [ ] September 1-7: DAC benchmarks (Issue 2)
- [ ] September 8-14: Fast-SA polish (Issue 5)
- [ ] September 15-21: Per-net quality plot with more data points (Issue 7)
- [ ] Phase 2 (post-NEOSEF): Timing-driven placement (Issue 3)
- [ ] Phase 2: Training on larger corpus (Issue 6)
- [ ] Phase 2: Learned legalization
