# 6-Month Sprint Plan: Aug 26 2026 → NEOSEF March 2027 → ISEF May 2027

> **Working schedule. ~25 weeks from now until ISEF judging.**
> Goal: Win NEOSEF Grand Prize → ISEF IEEE-CS Special Award → $35K for BMW Z4 G29.

---

## Phase 1: Close the gaps (Aug 26 – Sep 30) — 5 weeks

**Week 1 (Aug 26 – Sep 1)** — Highest-leverage
| Day | Action | Hours |
|---|---|---|
| Wed (today) | 15K polish loop running; §3.8, §4.7 merged; pitch drafted; IEEE-CS app drafted | ✅ done |
| Thu | Write 1-page project summary for NEOSEF booth; rehearse pitch once | 2 |
| Fri | Install OpenROAD locally (brew install openroad or build from source) | 2 |
| Sat | Run OpenROAD full flow on GCD (placement → CTS → routing → power); save real routed power | 3 |
| Sun | Begin building side-by-side routing congestion heatmap (OpenROAD vs SmallChip) | 3 |
| Mon-Sun | Train V3 on combined 510-chip corpus for 80 epochs (overnight runs) | 12 |

**Week 2 (Sep 2 – Sep 8)** — Wow demo
| Day | Action | Hours |
|---|---|---|
| Mon | Finish routing congestion heatmap; integrate into web app | 4 |
| Tue | Rebuild desktop .app v0.3.0 with new visualizations | 2 |
| Wed | Test .app on 3 machines; write INSTALL.md update | 2 |
| Thu | Run new V3 80-epoch model on 5K, 8K, 10K, 15K; capture new scaling curve | 4 |
| Fri | Begin §5 Discussion polish (math references, IEEE-CS framing) | 3 |
| Sat | Submit paper draft v0.4 to advisor (parents, science teacher) for review | 1 |
| Sun | Rest / Carnatic practice / school | — |

**Week 3 (Sep 9 – Sep 15)** — Polish + scale
| Day | Action | Hours |
|---|---|---|
| Mon | Try fast-SA on 15K (numpy-vectorized) — Option B from 15K report | 4 |
| Tue | Polish loop: V3 → legalize → fast-SA → re-legalize — Option C | 3 |
| Wed | Capture new best 15K number; update §4.3.1 | 2 |
| Thu | Begin building pitch demo video (3 min, for ISEF booth) | 3 |
| Fri | NEOSEF registration opens — register project | 1 |
| Sat | Begin first draft of full ISEF paper (incorporate §3.8, §4.7) | 4 |
| Sun | Rest | — |

**Week 4 (Sep 16 – Sep 22)** — Paper + paper
| Day | Action | Hours |
|---|---|---|
| Mon-Wed | Polish full ISEF paper draft to v0.5 | 8 |
| Thu | Send to 2 outside readers (a chip designer if you can find one) | 1 |
| Fri-Sat | Incorporate feedback; paper v0.6 | 4 |
| Sun | Rest | — |

**Week 5 (Sep 23 – Sep 30)** — Mid-month check
| Day | Action | Hours |
|---|---|---|
| Mon | Push new .app v0.3 + paper v0.6 to GitHub | 1 |
| Tue | Start IEEE-CS special award application (we have a draft) | 2 |
| Wed | Start NEOSEF booth materials (poster draft, business cards) | 3 |
| Thu | Practice pitch (10 min, 5 times) | 2 |
| Fri | Run polish on 15K one more time; save new best | 2 |
| Sat-Sun | Rest | — |

---

## Phase 2: Polish (Oct 1 – Oct 31) — 4 weeks

**Focus:** ISEF paper to v1.0; .app v0.4; wow demo to production quality; pitch to memorized.

| Week | Goal |
|---|---|
| Oct 1-7 | ISEF paper to v0.8; submit to school science teacher for review |
| Oct 8-14 | Pitch memorized (record self, watch, refine); booth poster v1 |
| Oct 15-21 | .app v0.4 with wow demo (routing heatmap) + LLM co-pilot polish |
| Oct 22-28 | NEOSEF practice round (mock judging with parents) |
| Oct 29-31 | First NEOSEF paper v0.9; push to GitHub |

---

## Phase 3: Pre-NEOSEF (Nov 1 – Dec 31) — 9 weeks

| Week | Goal |
|---|---|
| Nov 1-7 | NEOSEF paper v1.0; abstract 200 words |
| Nov 8-14 | Practice pitch 10x; record; refine |
| Nov 15-21 | .app final v0.4.0; release on GitHub |
| Nov 22-28 | Mock judging sessions (3x, with different people) |
| Nov 29-Dec 5 | Polish based on mock judging; finalize poster |
| Dec 6-12 | Final rehearsals; print poster; pack booth materials |
| Dec 13-19 | Winter break — light work only |
| Dec 20-26 | Holiday rest |
| Dec 27-31 | Final preparation |

---

## Phase 4: NEOSEF (Jan 1 – Mar 31 2027) — 13 weeks

| Date | Event |
|---|---|
| Jan 1-15 | Final paper edits; back-up booth materials |
| Jan 16-31 | Spring semester starts; balance school + project |
| Feb 1-15 | Rehearsals: 3 full mock judging sessions |
| Feb 16-28 | Final poster print; final .app test on 3 machines |
| **Mar 1-15** | **NEOSEF 2027 (typically second week of March)** |
| Mar 16-31 | If win Grand Prize: ISEF prep. If not: regroup, identify gap |

---

## Phase 5: ISEF (Apr 1 – May 31 2027) — 9 weeks

| Date | Event |
|---|---|
| Apr 1-15 | ISEF abstract submission |
| Apr 16-30 | Poster final; booth materials; pitch polish |
| May 1-15 | Final rehearsals; IEEE-CS application (if not already submitted) |
| **May 12-17** | **ISEF 2027 (typically mid-May, ~$9M+ in prizes)** |
| May 18-31 | Win $$$ → order BMW Z4 G29 |

---

## What I'm doing for you this week

| When | What |
|---|---|
| Tonight | Polish loop running, math + divergence sections merged, pitch + IEEE-CS drafted, git committed |
| This week | Side-by-side routing congestion heatmap; 1-page booth summary; GCD full-flow |
| Next 2 weeks | New V3 training run (80 epochs); .app v0.3.0; scaling curve refresh |
| By Sep 30 | ISEF paper v0.6; .app v0.4; pitch memorized |

---

## Risk register (what could derail us)

| Risk | Probability | Mitigation |
|---|---|---|
| Polish loop doesn't beat 587K | 60% | Pivot to "OpenROAD divergence" as the story (already drafted) |
| GCD full-flow fails | 30% | Have 1.06 mW placement-stage estimate as fallback; mention limitation |
| 9th grade schedule conflict (marching band, school) | 100% | Front-load work in Aug-Sep; use school breaks for big tasks |
| Other NEOSEF 2027 project is also an AI+chip | 5% | Acceptable — both can win; multiple categories |
| You (Harshith) get sick or burned out | 30% | Schedule rest days; don't do "death march" weeks |
| GitHub token in chat gets revoked mid-project | 5% | Already noted in PROJECT_STATE.md; rotate before push |

---

## The BMW Z4 G29 line in the sand

Every decision in this plan should be tested against: **"Does this move us toward $35K?"**

If yes → do it.
If no → defer it.
If "maybe" → put it in Phase 5 and re-evaluate after NEOSEF.
