# Win Strategy — Everything I Can Do

> **What else I can do to help you win, organized by impact and effort.**

---

## The 5 highest-impact moves for ISEF 2027

| # | Move | Impact | Effort | Status |
|---|---|---|---|---|
| 1 | **Real-routed GCD power** (OpenROAD placement → CTS → routing → power) | Replaces an un-defended claim with a defended one. +5-10% Grand Prize probability. | 4h | Not started — need OpenROAD installed |
| 2 | **Side-by-side routing congestion heatmap** (OpenROAD vs SmallChip) | ISEF booth wow-moment. +3-5% Grand Prize probability. | 1 day | Not started — need OpenROAD installed |
| 3 | **Held-out test set** (DAC or ICCAD benchmarks, separate from training) | Strengthens the multi-benchmark claim. +3-5% special award probability. | 1 day | Not started — need to download benchmarks |
| 4 | **A 1-min elevator pitch** | For casual conversations, interviews, admissions. | 1h | Done — see 5_MINUTE_PITCH.md |
| 5 | **Polish to <400K on 15K** (more cell widths, longer runs) | Better headline number for ISEF. +2% Grand Prize. | 1 day | 80-epoch V3 retrain running overnight |

**Total: ~5-6 days of focused work, no more than 1 week**

If we do moves 1-3, the project is bulletproof. Move 4 is done. Move 5 is in progress.

---

## Other high-value deliverables (in priority order)

| # | Deliverable | Time | Why |
|---|---|---|---|
| 6 | **OpenROAD install + full-flow GCD** | 4h | The single biggest undefended claim |
| 7 | **Side-by-side routing heatmap** | 1 day | Booth wow-moment |
| 8 | **DAC benchmark download + small-chip test** | 4h | Multi-benchmark claim |
| 9 | **1-min elevator pitch for admissions** | 30 min | For college apps |
| 10 | **Polish to <400K on 15K** (after V3 retrain) | 1 day | Better headline number |
| 11 | **A "day in the life" project video** (1-min, lifestyle) | 2h | For school PR, social media |
| 12 | **A "code architecture" walkthrough video** (5-min) | 3h | For ISEF booth loop |
| 13 | **An "interview rehearsal" with a tough judge** (recorded) | 2h | For practicing under pressure |
| 14 | **A "what would you do differently" self-critique doc** | 1h | Shows judges humility |
| 15 | **An "implications for the field" essay** (1 page) | 1h | Shows depth |
| 16 | **A "future work" 3-year plan** | 1h | Shows vision |
| 17 | **A "lessons for the next student" essay** | 1h | Forgiving, shows wisdom |
| 18 | **An "open issues" list** (honest limitations) | 1h | Shows intellectual honesty |
| 19 | **A "thank you" page** (parents, OpenROAD team, ISPD 2005) | 30 min | Shows gratitude |
| 20 | **A "1-page executive summary" for busy judges** | 1h | Different from the 1-page summary |

---

## What I can also do (less obvious)

### Conceptual
- **Generate counter-arguments to the project** — play devil's advocate. "If I were a judge trying to dismiss this, how would I do it?" Then you have answers ready.
- **Generate "what's missing" lists** — every paper has gaps. Identify them so judges don't have to.
- **Generate "what would make this stronger" lists** — for each criterion, what's the next step?
- **Generate "what other people have done in this space"** — competitor analysis, not just Mirhoseini 2021.

### Personal
- **Daily motivation messages** — quick pep talks
- **Mock interviews** — play judge, grill you on tough questions
- **A "what went well / what to improve" weekly review** — for continuous improvement
- **A "celebration log"** — every time you hit a milestone, log it. Read it on tough days.

### Technical
- **More detailed_placer improvements** — can we push 15K below 400K?
- **A "smarter" legalizer that uses LEF cell widths** — already in code, but could improve
- **A "fast-SA" implementation** for the polish step (Option B from 15K report)
- **A "polish + fast-SA" pipeline** (Option C) — could be a new headline number
- **A "ParetoGATPlacer"** — we rejected this, but it could be a "future work" note
- **A "cell width sweep" automation** — already have, but could be more thorough
- **A "training data augmentation"** — rotate / reflect / scale the training chips

### Documentation
- **API reference for chipmind** — auto-generated from docstrings
- **A "tutorial" notebook** — Jupyter walkthrough of the project
- **A "benchmark" notebook** — reproduces the 91-design results
- **A "model card"** — describes V3's intended use, limitations, ethics
- **A "data card"** — describes ISPD 2005, what it includes, what it doesn't

### Outreach
- **A README rewrite** for the GitHub repo
- **A CONTRIBUTING.md** for potential contributors
- **A CODE_OF_CONDUCT.md** for the open-source community
- **A CHANGELOG.md** for the v0.x releases
- **A blog post draft** — for posting on Medium or dev.to after NEOSEF
- **A Twitter thread** — for showing the project to the chip-design community
- **A "we're hiring / looking for collaborators" message** — for university labs
- **A "contact the OpenROAD team about integration" draft** — for actual collaboration

---

## The 3-month plan (Sep-Nov 2026)

| Week | Goal | Done by |
|---|---|---|
| Sep 1-7 | OpenROAD install + GCD full flow | Sat Sep 6 |
| Sep 8-14 | Routing heatmap + DAC benchmarks | Sat Sep 13 |
| Sep 15-21 | ISEF paper v0.5 | Sat Sep 20 |
| Sep 22-28 | IEEE-CS application submission | Sat Sep 27 |
| Sep 29-Oct 5 | Pitch + booth demo fully memorized | Sat Oct 4 |
| Oct 6-12 | NEOSEF paper v1.0 | Sat Oct 11 |
| Oct 13-19 | Mock judging × 3 | Sat Oct 18 |
| Oct 20-26 | Poster design + print | Sat Oct 25 |
| Oct 27-Nov 2 | Polish to 80-epoch V3 model | Sat Nov 1 |
| Nov 3-9 | Final paper edits | Sat Nov 8 |
| Nov 10-16 | NEOSEF practice × 3 | Sat Nov 15 |
| Nov 17-23 | NEOSEF booth setup | Sat Nov 22 |
| Nov 24-30 | Winter break | — |
| Dec 1-7 | Final polish | Sat Dec 6 |
| Dec 8-14 | Final rehearsal | Sat Dec 13 |
| Dec 15-31 | Holiday rest | — |

**End of December: ready for NEOSEF March 2027.**

---

## What I should NOT do

- **Don't overload the project.** Adding too many features dilutes the message. The story is "pre-trained GAT for small chips." Stick to it.
- **Don't apologize for the gaps.** Frame them as future work. "I haven't run post-routing power yet — that's in Phase 2 of the project."
- **Don't add features the user can't defend.** If you can't explain it in 60 seconds, it's a distraction.
- **Don't take on collaboration with universities mid-project.** It's a distraction. After ISEF, yes.
- **Don't write more documentation that won't be read.** Quality > quantity. STUDY_GUIDE.md is enough. Don't write 10 more glossaries.

---

## The one thing I'd prioritize

If I could do only ONE thing more, it would be:

> **Real-routed GCD power from OpenROAD's full flow (placement → CTS → routing → power analysis).**

This is the single biggest undefended claim. If you can show 0.52 ns WNS + 1.06 mW on the *fully routed* GCD, the validation story is bulletproof. IEEE-CS judges will love it.

**Effort:** 4 hours
**Reward:** +5-10% probability at NEOSEF Grand Prize
**When:** Saturday Aug 30

This is the move.
