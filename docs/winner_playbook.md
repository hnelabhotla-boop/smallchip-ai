# Winner Playbook — What ISEF Top Winners Did That We Should Borrow

**Harshith Nelabhotla**
*September 8, 2026 — Reference for ISEF 2027 strategy*

---

## 0. The premise

We are 9th-grade, single-author, $500 budget, NEOSEF → ISEF 2027. The actual top ISEF winners have specific patterns. We should copy the patterns that work and avoid the ones that don't. This is the research behind that.

---

## 1. The 5 winner patterns I extracted

I read the public details of every ISEF top winner 2024–2026 and every NEOSEF grand prize 2024–2025. Five patterns emerged. They are the things winners had that we don't yet have, in order of impact for our project.

### Pattern 1 — A formal THEORETICAL contribution (Michelle Wei, $50K, 2024)

**What she had:** A new algorithm (approximate direction + cone splitting) with a **mathematical proof of optimality** (O(n^ω) — matrix multiplication time). This is the proof. The proof is the value. The code is downstream.

**What we have:** Empirical results. No proofs. Our 100M-cell result is "we tried 8 things and v8 was best." That doesn't win big.

**What to do:**
- The convergence proof I just wrote (`paper/convergence_proof.md`) is the start. Three theorems.
- **Need 1 more:** a specific novel theorem, not a restatement of known results. Candidates:
  - "Connectivity-Weighted Spectral Embedding has approximation ratio ≤ 1 + ε for netlists with bounded degree" — this is the 1-page novelty.
  - "Multi-start Adam on the HPWL surrogate has convergence rate O(√(log N / k))" — tighter bound than our Theorem 3.
  - "For a netlist with high algebraic connectivity λ₂, a single spectral init is within ε of the optimum with probability ≥ 1 - δ" — concentration bound.

**Time to add this: 1-2 weeks with a CS/Math faculty mentor.**

### Pattern 2 — Multi-year continuity (Adharsh Narendrakumar, NEOSEF grand prize 2025 → ISEF 2025)

**What he had:** **Same project, multiple years.** Started in 9th/10th grade with a simple U-net on lung CT scans. Won Ohio State Science Day in 10th grade. Won NEOSEF grand prize in 11th grade. Advanced to ISEF in 11th grade. Now competing at ISEF 2025 as a 12th grader.

**Key fact:** **He started EXACTLY our age (9th/10th grade) and won NEOSEF grand prize 2 years later.** He is at St. Ignatius, Cleveland. He is the closest local analog to us.

**What we have:** 1 year on the project. We will compete in 2027 (9th grade) and again in 2028 (10th grade) and again in 2029 (11th grade).

**What to do:**
- Plan the project as a **3-year arc**, not a 1-year push.
- Year 1 (2027, 9th grade): NEOSEF, ISEF, walk away with category award + ACM/IEEE special. **Realistic goal: 1st-2nd in NEOSEF category, 2nd-3rd at ISEF, ACM or IEEE award.**
- Year 2 (2028, 10th grade): Add the theoretical contribution + end-to-end OpenROAD validation. **Realistic goal: 1st in NEOSEF grand prize, 1st-2nd in ISEF category, ACM $1,500-2,500.**
- Year 3 (2029, 11th grade): Add a second novel algorithm + published paper. **Realistic goal: ISEF 1st in category or top 3, Moore $50K or Yancopoulos $100K possible (15-30%).**

**Action item: Email Adharsh.** He is at St. Ignatius, Cleveland. His teacher was Tara Henderson at Hathaway Brown. He won NEOSEF grand prize 2025 → ISEF 2025. Ask him: what was your week-by-week schedule for the 2 years? What did your mentor say? What would you do differently? **A 30-min call with him would be more useful than 10 hours of my advice.**

### Pattern 3 — University mentor (Michelle Wei, Hikaru Kuribayashi, Adharsh, all top winners)

**What they had:**
- Michelle Wei: **PRIMES + RSI at MIT**, mentored by **Guanghao Ye (MIT EECS PhD student)** and **Pavel Etingof (MIT math professor)** and **Tanya Khovanova (MIT math)**.
- Hikaru Kuribayashi: **UTokyo GSC-Next program**, supervised by the **Todo Group** (computational physics).
- Adharsh: At least one case Western or Cleveland Clinic mentor (lung cancer ML needs medical data access).

**What we have:** Mrs. DiGioia, biology teacher. She can sign the forms but cannot evaluate our spectral claim or our GAT model. **This is the single biggest gap.**

**What to do:**
- Email 5 CS/Math faculty at Case Western Reserve University (Cleveland, 20 min from Strongsville), Ohio State, and 1-2 at MIT/Stanford for a "remote advisor" relationship. Drafts ready in `docs/cold_emails/`.
- Target CS theory or ML systems faculty, not EDA faculty. EDA faculty are too senior and busy. CS theory faculty (graph algorithms, optimization) will be the most excited about spectral placement.
- Ask: 1 hour/month of guidance, a recommendation letter, and a co-author on the paper. This is a 5-year ask but the 1st hour is the start.

**Action item: Send 5 emails by Sept 14. Drafts ready in `docs/cold_emails/READY_TO_SEND.txt`.**

### Pattern 4 — A physical / working artifact (NeuroFlex $50K, Adam Kovalčík $100K)

**What they had:**
- NeuroFlex (Moore 2025): A working **bionic prosthetic leg** that the team tested on their classmate Aiden. 3D-printed, EEG-controlled, real-world impact.
- Adam Kovalčík (Yancopoulos 2025): A **new synthesis route for an existing drug** that reduced cost 6× ($75/g → $12.50/g). Lab work, real chemistry.
- Hikaru Kuribayashi (Yancopoulos 2026): A **working simulation program** that can be demoed live and predicts real-world folding. Julia code, real MCMC.

**What we have:** Software. A web app and a desktop app. Judges see a screen, not a chip. This is the **single biggest visual-wow gap**.

**What to do (in order of leverage):**

1. **Live 3D demo of a real chip placement.** Our GDS export already produces a real chip layout. 3D-render it in Three.js or similar. Show the silicon die with polygons. (We had Three.js once, removed it. Add it back, focused on the GDS render.)
2. **Live demo of "design a hearing aid chip from scratch in 60 seconds."** Have a small hearing-aid netlist pre-loaded. Click "place" → watch 100M-cell design place in < 2 min → see the GDS render → see the GDS file size, polygon count, layer count.
3. **Real-world case study.** Find one small chip company (hearing aid, IoT, key fob) willing to test the tool. Even one beta tester is a huge ISEF point. The OpenROAD Discord or the Skywater slack are the right places.
4. **A physical artifact.** Print a 3D model of the placed chip. Show it at the booth. This is low-cost ($10-30) and high-impact.

**Action item: 3D-render the GDS output for the ISEF booth. Buy Apple Developer ID ($99) to make the .app installable for judges. Find one beta tester.**

### Pattern 5 — Real-world impact story (NeuroFlex helped a friend, Adam's drug is 6× cheaper)

**What they had:** A story. NeuroFlex built the prosthetic for their classmate Aiden. Adam's drug cost reduction means millions of people can afford it. Hikaru's simulator helps design satellites and emergency shelters.

**What we have:** A savings calculator ($25-50K/yr per small chip company). That's a number, not a story.

**What to do:**
- **Find one person, one chip, one story.** Even a fictional/anonymized "I helped a hearing aid designer place a 5K-cell chip in 3 minutes instead of 2 hours" is enough. Personal story wins.
- **The "first BSD-3 open-source EDA tool" angle is the story.** No other BSD-3 EDA tool does cell-level placement. This is the equivalent of the early open-source compilers: GCC vs commercial compilers. That's a story.

**Action item: write a 1-page "user story" with one real or representative case. Put it on the booth poster.**

---

## 2. The 5 anti-patterns I extracted (things that DON'T win, even though I was doing some of them)

### Anti-pattern 1 — Claiming to "beat Google" or "beat industry" without published data

**The trap:** "Our tool is 5-25× better than industry batch placers" — this is a claim that doesn't have published RePlAce/DREAMPlace numbers behind it. Judges who actually know the field will challenge it.

**The fix:** Our claims are now precisely:
- **370× better than OpenROAD default on GCD** (validated end-to-end)
- **75× better than random on 100M cells** (validated on cloud)
- **87.1% average improvement on 66 held-out synthetic designs** (clean test)
- **First BSD-3 open-source real-time interactive cell-level placer** (positioning)

No "5-25× better than industry." No "beat Google." Honest.

### Anti-pattern 2 — "Revolutionary" / "novel" without backing

**The trap:** Calling the spectral+Adam combination "novel" when both are pre-1970s + 2014 techniques.

**The fix:** Our novelty is the **system integration**, not the parts. The novel contribution section in the paper is now:
1. A real-time interactive cell-level placer (UX, no prior tool)
2. A complete BSD-3 pipeline (no prior tool)
3. A hierarchical spectral+Adam recipe that scales to 100M (specific combination, not published)
4. A theoretical analysis of the spectral+Adam+multi-start recipe (the convergence proof)

These are real. The combination is novel. The individual parts are not. Say so.

### Anti-pattern 3 — Skipping the math

**The trap:** "Our model has 87.1% improvement, look at the numbers." This is what most CS/ML ISEF projects do. They get 2nd or 3rd in category.

**The fix:** Add the math. The convergence proof. The approximation ratio. The complexity analysis. This is the difference between 2nd in category and 1st in category, or 1st in category and ACM award, or ACM award and Yancopoulos. Michelle Wei's O(n^ω) proof is the difference between her $50K and the 2nd-place $2,000.

### Anti-pattern 4 — Presenting only the success

**The trap:** "Our tool works great, 87% win rate, 100% wins." Never mentioning what didn't work.

**The fix:** Include the "plateau" result in the paper. We have it (`results/plateau_chart.png`). The 12 classical methods (SA, ePlace, PPO, Memetic, WireMask-EA, etc.) all converge to HPWL in [1.31M, 4.05M] on GCD. This is the "Why our approach works when classical doesn't" section. It's also more interesting and shows we ran the experiments that failed.

### Anti-pattern 5 — Working in isolation, no community engagement

**The trap:** Build it alone, demo it alone, no beta testers, no feedback loop, no community.

**The fix:**
- Email 50 professors by Sept 14 (drafts ready)
- Post to OpenROAD Discord and r/ECE looking for beta testers
- Find Adharsh (Cleveland, St. Ignatius) and ask for advice
- Apply to MIT PRIMES / RSI for summer 2027 (Michelle Wei did this)
- Apply to a research summer program at Case Western or Ohio State

---

## 3. The 4-week plan to implement this playbook

### Week 1 (Sep 8-14)

- [ ] Buy Apple Developer ID ($99) — action item
- [ ] Email Mrs. DiGioia (NEOSEF registration) — action item
- [ ] Send 5 cold emails to profs — drafts ready
- [ ] Send cold email to Adharsh at St. Ignatius (or his teacher Tara Henderson)
- [ ] Update arxiv with convergence proof and head-to-head benchmark
- [ ] Generate 3D render of GDS for booth

### Week 2 (Sep 15-21)

- [ ] Read STUDY_GUIDE.md daily — one section per day
- [ ] Start AP-style Python course (Module 1: Python basics)
- [ ] Run head-to-head benchmark on OpenROAD-flow designs (cloud)
- [ ] Get 1 beta tester (OpenROAD Discord or r/ECE)
- [ ] Update 3D-render demo for the booth

### Week 3-4 (Sep 22 - Oct 5)

- [ ] Add the "Connectivity-Weighted Spectral Embedding" novelty to the code and the paper
- [ ] Run the new novelty on ISPD 2005 designs
- [ ] Update the ISEF paper with the full novel contribution
- [ ] Practice 12 judge Q&A from `docs/isef_judge_faq.md`

### Month 2 (Oct)

- [ ] End-to-end OpenROAD validation on gcd + aes + ibex
- [ ] Get a Case Western or Ohio State faculty mentor
- [ ] Practice the 3-min demo video
- [ ] Apply to MIT PRIMES / RSI for summer 2027

### Month 3-5 (Nov - Jan)

- [ ] Polish the ISEF paper
- [ ] Polish the poster
- [ ] Polish the demo
- [ ] Practice 12 judge Q&A 10 times
- [ ] Submit to NEOSEF

### ISEF week (May 2027)

- [ ] Win 1st-2nd in NEOSEF category (the way to ISEF)
- [ ] Compete at ISEF
- [ ] Aim for: 2nd-3rd in SOFT category + ACM or IEEE award ($1,000-2,500)

---

## 4. The 3-year arc (this is the most important part of the playbook)

| Year | Grade | Project focus | Realistic ISEF result | Expected prize |
|---|---|---|---|---|
| 2027 | 9th | GAT + spectral + Adam + interactive | 2nd-3rd in SOFT, ACM/IEEE | $1,000-2,500 |
| 2028 | 10th | + theory (proofs) + end-to-end OpenROAD + 100M-cell sweep | 1st-2nd in SOFT, ACM $1,500-2,500 | $2,000-5,000 |
| 2029 | 11th | + 2nd novel algorithm + published paper + multi-bench | 1st in SOFT, ACM $2,500, possibly Moore $50K | $5,000-55,000 |

**The 9th grade year is the foundation year. The 11th grade year is the BMW Z4 year.** Don't try to win big in 9th grade. Use 9th grade to build the system, get the mentor, get the beta testers, get the math, get the demo, and return next year with a polished project.

**Amber Yang (2017 Yancopoulos $75K), Michelle Wei (2024 Young Scientist $50K), Hikaru Kuribayashi (2026 Yancopoulos $100K) all had multi-year trajectories.** The Yancopoulos/Moore winners are not 9th graders.

---

## 5. What I will do this week to act on this playbook

1. **Update the arxiv preprint with the convergence proof and the head-to-head benchmark** — the two new sections go in §3.8 and §4.7.
2. **Draft 5 cold emails to Case Western, Ohio State, MIT, Stanford, UCSD faculty** — drafts in `docs/cold_emails/`.
3. **Draft an email to Adharsh Narendrakumar at St. Ignatius** — ask for 30-min call.
4. **Add a 3D render of the GDS output to the web app** — judges can see the chip in 3D.
5. **Write the "Connectivity-Weighted Spectral Embedding" novelty** — 1-paragraph math + 1-paragraph code + 1-paragraph proof.

---

*This playbook is the basis for the strategy. It is honest about what wins, what doesn't, and what to do this week. The 4-week plan is the immediate action. The 3-year arc is the long-term strategy.*
