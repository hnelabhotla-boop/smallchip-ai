# Future Work — 3-Year Plan (Sep 2026 → May 2029)

> **What happens after ISEF 2027. Where the project goes from "high school science fair" to "PhD thesis".**

---

## Year 1: ISEF 2027 + undergraduate (Sep 2026 - May 2028)

### Fall 2026 (9th grade)
- **Sep 2026:** Polish to <400K on 15K (if V3 retrain improves)
- **Oct 2026:** NEOSEF paper v1.0, IEEE-CS application, ISEF paper outline
- **Nov 2026:** NEOSEF practice × 3, ISEF practice × 1
- **Dec 2026:** NEOSEF paper final
- **Dec 2026-Mar 2027:** NEOSEF prep (every weekend)
- **Mar 2027:** **NEOSEF 2027 (target: Grand Prize)**

### Spring 2027 (9th grade)
- **Apr 2027:** NEOSEF reflection, ISEF prep starts
- **May 2027:** **ISEF 2027 (target: 1+ special award)**
- **Jun-Aug 2027:** Summer — DAC 2012 + ICCAD 2015 benchmarks, larger training corpus, side-by-side routing heatmap

### Fall 2027 (10th grade)
- **Sep 2027:** "SmallChip AI v0.4" with DAC + ICCAD support
- **Oct 2027:** Conference paper submission (MLCAD, ICCAD student track)
- **Nov 2027:** Reach out to OpenROAD team about integration
- **Dec 2027:** Begin PPO fine-tuning research

### Spring 2028 (10th grade)
- **Mar 2028:** **NEOSEF 2028 (target: 2nd Grand Prize, "repeat winner" prestige)**
- **May 2028:** **ISEF 2028 (target: Top Award, $50K+)**
- **Jun-Aug 2028:** Summer — apply to research internships (CMU, MIT, Stanford, Berkeley)

---

## Year 2: Internship + 11th grade (Sep 2028 - May 2029)

### Fall 2028 (11th grade)
- **Sep 2028:** College applications (early decision) — CMU, MIT, Stanford, Berkeley, UIUC
- **Oct 2028:** Research internship (if summer worked out)
- **Nov 2028:** Continue PPO fine-tuning + larger benchmarks
- **Dec 2028:** First journal paper submission (TODAES, TCAD, or MLJ)

### Spring 2029 (11th grade)
- **Mar 2029:** **NEOSEF 2029 (target: 3rd Grand Prize)**
- **May 2029:** **ISEF 2029 (target: Gordon E. Moore Award, $50K)**
- **Jun-Aug 2029:** Summer — pre-college research at MIT/CMU/Stanford

### Year 2 deliverables
- 1 journal paper submitted
- 2 conference papers
- 1 internship at a chip-design lab
- Pre-trained model with 5,000+ training chips
- PPO fine-tuning for specific designs
- Real-routed validation on 100K-cell designs
- DAC + ICCAD benchmark results

---

## Year 3: College + ISEF finale (Sep 2029 - May 2030)

### Fall 2029 (12th grade)
- **Sep 2029:** College apps (regular decision)
- **Oct 2029:** SAT, ACT, subject tests
- **Nov 2029-Dec 2029:** College apps submitted
- **Dec 2029:** **NEOSEF 2030 (target: 4th Grand Prize, record)**
- **Dec 2029:** Apply for early admission to top CS/EE programs

### Spring 2030 (12th grade)
- **Mar 2030:** Decision letters
- **May 2030:** **ISEF 2030 (target: Gordon E. Moore Award, $50K — for the BMW Z4)**
- **Jun 2030:** Graduate Strongsville HS, accept college admission
- **Aug 2030:** Start college

### Year 3 deliverables
- 1 more journal paper
- 2 more conference papers
- "The 4-year SmallChip AI journey" retrospective
- Open-source community of contributors
- Trained successor(s) to maintain the project

---

## Specific research directions

### Direction 1: PPO fine-tuning (high impact, 6-12 months work)

**Goal:** Combine pre-trained GAT (fast, amortized) with per-design PPO (slow, accurate) for the best of both worlds.

**Why it matters:** Google's 8-48 hours of GPU per chip is too slow. My 17 seconds is too rigid. A hybrid that pre-trains then fine-tunes is the future.

**Approach:**
- Use V3's prediction as the starting state for PPO
- Fine-tune for 1-10 minutes per design (vs 8-48 hours from scratch)
- Reward: -HPWL, -WNS, -power, -area, -congestion
- Expected outcome: 10-100× better than V3 alone, with 1-2 orders of magnitude less compute than Google's approach

**Output:** Paper at MLCAD or ICCAD. Open-source code.

### Direction 2: Learned legalization (high impact, 12-18 months work)

**Goal:** Replace the hand-coded detailed placer with a learned model that produces legal placements directly.

**Why it matters:** The hand-coded detailed placer is the heuristic. A learned one could be:
- Faster (no iterative refinement)
- Better (no plateau from local search)
- Generalizable (works on different cell libraries)

**Approach:**
- Add cell legalization as a learned post-processor
- Train with legality constraints (no overlap, all cells on rows)
- Use a transformer-based architecture for the legalization step
- Expected outcome: 15K legal HPWL under 300K (vs current 418,115)

**Output:** Paper at DAC or DATE. Open-source code.

### Direction 3: Cross-benchmark validation (medium impact, 1-2 months work)

**Goal:** Test SmallChip AI on DAC 2012, ICCAD 2015, and other benchmark families.

**Why it matters:** The 91-design benchmark is from ISPD 2005. Cross-benchmark validation is the standard for "generalization" claims.

**Approach:**
- Download DAC 2012 and ICCAD 2015
- Extract connected subsets
- Run V3 on the largest designs
- Report win rates

**Output:** Section in next paper. Strengthens the multi-benchmark claim.

### Direction 4: End-to-end placement + routing (very high impact, 18+ months work)

**Goal:** Train a single model that does both placement AND routing.

**Why it matters:** Placement and routing are usually separate tools, but they interact. A joint model could produce better results.

**Approach:**
- Train a graph transformer on placement + routing
- Use OpenROAD's full flow as ground truth
- Reward: -HPWL, -WNS, -routing congestion, -via count

**Output:** PhD thesis topic. Open-source code.

### Direction 5: Commercial deployment (low priority until senior year)

**Goal:** A standalone SaaS product for the 99% market.

**Why it matters:** Money + impact. The 99% market is billions of chips per year. A $10/month SaaS could disrupt the $1M EDA market.

**Approach:**
- Wrap SmallChip AI in a web API
- Add a usage-based pricing model
- Acquire customers through academic conferences

**Output:** A small company. Maybe by senior year of college.

---

## What this means for the BMW Z4 goal

### Path A: ISEF 2027
- NEOSEF Grand Prize: ~$0 (just the trip)
- ISEF 1st Place ENBED: $5,000
- ISEF IEEE-CS Special Award: $5,000
- ISEF ACM Special Award: $5,000
- Various $1K-$2K awards: $5,000-10,000
- **Total: $20,000-25,000** — not enough for the Z4

### Path B: ISEF 2028 (with research internship)
- More polished project
- More awards likely
- **Total: $30,000-50,000** — Z4 is reachable

### Path C: ISEF 2029 (with Gordon E. Moore Award)
- Project is mature
- Top award likely
- **Total: $50,000-100,000** — Z4 + college + savings

### Path D: ISEF 2030 (with multiple top awards)
- Project is definitive
- 3-4 top-tier awards likely
- **Total: $100,000-200,000** — Z4 + savings + college

**Path A is unlikely to fund the Z4. Path C or D is the realistic goal.**

If ISEF 2027 doesn't go well, the Z4 waits. But ISEF 2028-2030 is the real play.

---

## The honest 30-second version

> "I'm a 9th grader. SmallChip AI is my ISEF 2027 project. The goal is to win the Gordon E. Moore Award by 2029 or 2030 — that's $50,000, which would fund a used BMW Z4. The path is: ISEF 2027 → ISEF 2028 → ISEF 2029, with each year building on the last. The research direction is clear: PPO fine-tuning, learned legalization, cross-benchmark validation, end-to-end placement + routing. By the time I'm in college, SmallChip AI will be a mature research project with 5+ papers and a commercial path."

Memorize this. It's the 5-year pitch.
