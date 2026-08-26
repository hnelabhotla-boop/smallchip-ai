# Study Plan — Week by Week

> **From "I get the gist" to "I can defend this at ISEF" in 8 weeks.**
> Total: 4-6 hours/week. Designed around school + marching band.

---

## Calendar constraint

You have:
- **NEOSEF:** ~March 15, 2027 (~7 months from now)
- **ISEF:** ~May 12-17, 2027 (~9 months from now)
- **School:** Mon-Fri 8 AM - 3 PM + homework
- **Carnatic class:** Tues/Fri 6:30 AM
- **Gym:** Mon/Tue/Thu/Fri 5:30-7:00 PM
- **Sandhya:** Daily sunrise + sunset
- **Solo practice:** 30 min/day
- **Weekend sports:** Sat pickleball 8:30-10:30, Sun soccer 7:00-9:30
- **Marching band:** Aug 18 - Nov (varies)

**Available study time:** ~5-7 hours/week (weeknights + weekend afternoon)

---

## Week 1: Foundation (Aug 27 - Sep 2)

**Goal:** Understand the project at a 30,000-foot level. Be able to explain the headline.

| Day | Time | Task | File |
|---|---|---|---|
| Wed | 30 min | Read STUDY_GUIDE.md Part 1 (The Problem) | STUDY_GUIDE.md |
| Wed | 30 min | Read STUDY_GUIDE.md Part 2 (GAT) | STUDY_GUIDE.md |
| Thu | 30 min | Read STUDY_GUIDE.md Part 3 (Benchmark) | STUDY_GUIDE.md |
| Thu | 30 min | Read STUDY_GUIDE.md Part 4 (OpenROAD wall) | STUDY_GUIDE.md |
| Fri | 30 min | Read STUDY_GUIDE.md Part 5 (Detailed placer) | STUDY_GUIDE.md |
| Sat | 60 min | Read STUDY_GUIDE.md Parts 6-8 + Part 9 (Memorization) | STUDY_GUIDE.md |
| Sun | 60 min | Take the 100-question quiz, score yourself | 100_QUESTIONS.md |

**End-of-week check:** Can you recite the 3 anchor sentences without notes? Can you explain HPWL to your mom?

---

## Week 2: Code (Sep 3 - Sep 9)

**Goal:** Read the 5 most important code files. Understand the data flow.

| Day | Time | Task | File |
|---|---|---|---|
| Mon | 60 min | Read def_parser.py + hpwl.py | CODE_WALKTHROUGH.md Walkthroughs 1-2 |
| Tue | 60 min | Read gat_placer.py (the GAT model) | CODE_WALKTHROUGH.md Walkthrough 3 |
| Wed | 60 min | Read detailed_placer.py (the legalizer) | CODE_WALKTHROUGH.md Walkthrough 4 |
| Thu | 60 min | Read server.py + app.js (the web layer) | CODE_WALKTHROUGH.md Walkthroughs 5-6 |
| Fri | 60 min | Read llm_copilot.py (the LLM) | CODE_WALKTHROUGH.md Walkthrough 7 |
| Sat | 60 min | Try the python examples in CODE_WALKTHROUGH.md on your laptop | CODE_WALKTHROUGH.md |
| Sun | 60 min | Re-take the 100-question quiz, focus on weak spots | 100_QUESTIONS.md |

**End-of-week check:** Can you draw the data flow diagram (chip → DEF parser → GAT → detailed placer → legal DEF) from memory? Can you explain what each of the 5 files does?

---

## Week 3: Math (Sep 10 - Sep 16)

**Goal:** Understand the math behind V3. Be able to derive the loss function.

| Day | Time | Task | File |
|---|---|---|---|
| Mon | 60 min | Read STUDY_GUIDE.md Part 2 again, this time write out the GAT attention equation | STUDY_GUIDE.md §2.3 |
| Tue | 60 min | Read the V3 loss function, derive each term | STUDY_GUIDE.md §2.5 |
| Wed | 60 min | Read the math section of the paper (§3.8) | paper/ISEF_paper_draft.md |
| Thu | 60 min | Re-read with a friend, take turns explaining | paper/ISEF_paper_draft.md |
| Fri | 60 min | Re-read the OpenROAD divergence section (§4.7) | paper/ISEF_paper_draft.md |
| Sat | 60 min | Practice explaining why RePlAce diverges (stiff PDE) | STUDY_GUIDE.md §4.3 |
| Sun | 60 min | Re-take the 100-question quiz, target 90+ | 100_QUESTIONS.md |

**End-of-week check:** Can you derive the GAT attention equation on a whiteboard? Can you explain the V3 loss function with all 3 terms? Can you explain why RePlAce diverges without notes?

---

## Week 4: Pitch + Demo (Sep 17 - Sep 23)

**Goal:** Memorize the pitch. Practice the demo. Be booth-ready.

| Day | Time | Task | File |
|---|---|---|---|
| Mon | 60 min | Read PITCH_10MIN.md, memorize the 3 anchor sentences | PITCH_10MIN.md |
| Tue | 60 min | Practice the 10-min pitch out loud, 3 times | PITCH_10MIN.md |
| Wed | 60 min | Read BOOTH_DEMO_SCRIPT.md, walk through the .app | BOOTH_DEMO_SCRIPT.md |
| Thu | 60 min | Practice the 3-min booth demo, 3 times | BOOTH_DEMO_SCRIPT.md |
| Fri | 60 min | Record yourself doing the pitch, watch, refine | (your phone camera) |
| Sat | 60 min | Read FAQ.md, practice answering 5 random questions | FAQ.md |
| Sun | 60 min | Mock judging with a parent or friend | (use PITCH + FAQ) |

**End-of-week check:** Can you do the 10-min pitch without notes, 10 minutes, 0 ums? Can you do the 3-min booth demo without skipping steps? Can you answer 5 random FAQ questions?

---

## Week 5: Polish + Iterate (Sep 24 - Sep 30)

**Goal:** Refine the pitch. Strengthen weak spots. Practice tough questions.

| Day | Time | Task |
|---|---|---|
| Mon | 60 min | Mock judging #2 (different person from Week 4) |
| Tue | 60 min | Read ISEF_RUBRIC_COVERAGE.md, score yourself on each criterion |
| Wed | 60 min | Work on the 1-2 weakest criteria |
| Thu | 60 min | Read PRESS_TALKING_POINTS.md, practice the 5 lead messages |
| Fri | 60 min | Mock interview (treat as press interview) |
| Sat | 60 min | Final pitch refinement, 5 takes |
| Sun | 60 min | Rest day, watch a chip-design video for fun |

**End-of-week check:** 2 different people have given you mock judging feedback. You've addressed the top 2 weaknesses.

---

## Week 6: Paper Finalization (Oct 1 - Oct 7)

**Goal:** ISEF paper draft v1.0. Tight, complete, math-correct.

| Day | Time | Task |
|---|---|---|
| Mon | 90 min | Read paper §1-3, fix any rough edges |
| Tue | 90 min | Read paper §4-6, especially §4.7 (OpenROAD) |
| Wed | 90 min | Send paper to a parent or science teacher for review |
| Thu | 90 min | Read the ANNOTATED_BIBLIOGRAPHY.md, verify all citations |
| Fri | 90 min | Re-read full paper out loud, time yourself |
| Sat | 90 min | Final edits, save as v1.0 |
| Sun | Rest | - |

**End-of-week check:** Paper v1.0 is on the GitHub repo. Citations are correct. Math is right.

---

## Week 7: Booth Prep (Oct 8 - Oct 14)

**Goal:** Booth setup. Poster design. Materials.

| Day | Time | Task |
|---|---|---|
| Mon | 60 min | Read ISEF_BOOTH_CHECKLIST.md, get the hardware list |
| Tue | 90 min | Design the poster (use plateau chart, scaling table) |
| Wed | 60 min | Print 1-page summary, business cards |
| Thu | 60 min | Test the .app on 3 different machines |
| Fri | 60 min | Record the demo video (3 min) |
| Sat | 60 min | Practice booth setup (lay out the table) |
| Sun | Rest | - |

**End-of-week check:** Poster is print-ready. Demo video is on YouTube. Booth materials are in a box.

---

## Week 8: Full Dress Rehearsal (Oct 15 - Oct 21)

**Goal:** Everything works. You're ready for NEOSEF.

| Day | Time | Task |
|---|---|---|
| Mon | 90 min | Full dress rehearsal: 10-min pitch + 5-min Q&A |
| Tue | 90 min | Full dress rehearsal #2: 3-min demo + 5-min Q&A |
| Wed | 60 min | Read ALL the docs (FAQ, rubric, press) one more time |
| Thu | 60 min | Read the paper end-to-end one more time |
| Fri | 60 min | Final polish on poster and 1-page summary |
| Sat | Rest | - |
| Sun | Rest | - |

**End-of-week check:** You're ready.

---

## Daily minimum (every day, even when busy)

- 1 minute: Recite the 3 anchor sentences
- 5 minutes: Skim the latest commit on GitHub
- 10 minutes: Re-read 1 page of GLOSSARY.md

That's 16 minutes. Even on a school night with marching band, you can do 16 minutes.

---

## What to do when you forget a concept

1. Open STUDY_GUIDE.md and find the section
2. Read it twice
3. Try to explain it to someone (anyone, even a stuffed animal)
4. If you still don't get it, file a question for your next session with me

---

## What to do when you're stuck on a judge question

1. Pause. Take a breath.
2. Say: "Great question. Let me think about that for a second."
3. Refer to FAQ.md mentally
4. If still stuck: "I don't have a number for that right now, but I can look it up in the paper / GitHub repo / my notes."

That's an honest, professional answer. Judges respect it.

---

## What to do the week of NEOSEF

- **Mon:** Final equipment check, pack
- **Tue:** Drive to venue, set up booth
- **Wed:** Judging day
- **Thu:** Public viewing day (if NEOSEF has one)
- **Fri:** Awards ceremony
- **Sat-Sun:** Rest, celebrate, plan for ISEF
