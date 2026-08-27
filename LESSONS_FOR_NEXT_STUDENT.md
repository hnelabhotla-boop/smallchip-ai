# Lessons for the Next Student

> **What I learned that any high schooler starting a science fair project can use.**
> An essay for the next 9th grader who wants to do a PhD-level project.

---

## Lesson 1: Pick a problem, not a tool

I started SmallChip AI because I was curious about how chips are designed. I learned PyTorch and Graph Attention Networks, then asked "what can these do for chip design?" That worked — but it was backwards.

A better approach: **start with the problem**, then find the tools.

How to do this:
1. Read 2-3 papers in a domain you're curious about.
2. Identify what they CAN'T do, what's missing, what's the obvious next question.
3. Build that.

For me, the obvious next question was: "Mirhoseini 2021 does per-design RL placement. Can we do pre-trained instead?" The tools (GAT, PyTorch) were an implementation detail.

**Rule:** Before you learn a tool, learn a problem.

---

## Lesson 2: Read the citation graph

Every paper has a citation graph. Read the paper, then read the papers it cites, then read the papers those cite. After 3 levels deep, you'll understand the field better than 90% of grad students.

For chip placement, I started with Mirhoseini 2021 (Nature). It cited:
- Veličković 2018 (GAT)
- Lu 2015 (ePlace)
- OpenROAD docs
- ISPD 2005 benchmarks

Each of these led to more papers. After 3 months of reading, I knew the field.

**Rule:** Spend 10% of your project time reading, 90% building. Most students spend 0% reading.

---

## Lesson 3: Build something users can touch

A paper is good. A paper + a working system is great. A paper + a working system + a downloadable .app is unbeatable.

For SmallChip AI:
- The paper is the credibility
- The working system is the validation
- The .app is the wow factor

When a judge visits my booth, they don't just read a paper. They click a button. They upload a chip. They see the placement. They talk to the LLM co-pilot. They download the .app and run it on their laptop. **That's the difference between a good project and a great project.**

**Rule:** Always have something runnable. Even if it's ugly.

---

## Lesson 4: Real benchmarks beat synthetic ones

I could have generated my own random chip designs and tested on them. I didn't. I used the ISPD 2005 Bookshelf benchmark — a real industry contest, used by every academic placer paper.

Why this matters:
- Real benchmarks are reproducible (anyone can verify)
- Real benchmarks are credible (industry uses them)
- Real benchmarks are comparable (other papers use them too)
- Real benchmarks are citable

**Rule:** Always use the standard benchmark for your domain. Don't invent your own unless you have to.

---

## Lesson 5: Document your failures

I have 6 OpenROAD failure logs in `/tmp/openroad_*.log`. They're documented in §4.7 of the paper. They became a finding, not a gap.

Why this matters:
- Failures are normal. Judges know that.
- Documented failures = honest science.
- Sometimes failures become findings (the OpenROAD divergence story).
- A paper with all-positive results is suspicious.

**Rule:** Keep your failure logs. Cite them in the paper. They make you look honest.

---

## Lesson 6: Use the real validation tool

I could have written my own HPWL calculator. I did. But for the headline number, I used **OpenROAD's own static timing and power analysis** to validate the placement. That's the industry standard.

Why this matters:
- The industry uses OpenROAD's analysis to validate
- If I use the same tool, my number is directly comparable
- If I use my own tool, judges question it
- Real validation = real credibility

**Rule:** Use the industry standard validation tool. Don't reinvent.

---

## Lesson 7: Have an LLM co-pilot (or similar) for the wow

The LLM co-pilot in SmallChip AI is what makes the booth memorable. Judges can:
- Upload a chip
- Click "make it use less power"
- See the LLM translate it to a 5-dim preference vector
- See a tailored report

That's interactive, surprising, and shareable. It's the kind of thing judges remember a year later.

**Rule:** Your project needs ONE moment of "wait, what?" Find it, polish it, make it the centerpiece of your booth.

---

## Lesson 8: Open source everything (BSD or MIT)

I made SmallChip AI BSD-licensed. Public training data. Public pre-trained weights. Public benchmarks. Public code.

Why this matters:
- Anyone can verify your results
- Anyone can build on your work
- Industry can adopt your tool
- Judges trust open source (no hidden tricks)

**Rule:** If you can open-source it, do. The risk of "someone steals my idea" is much smaller than the benefit of "anyone can verify and adopt my work."

---

## Lesson 9: Make a 1-page summary

I have a 1-page summary (`PROJECT_SUMMARY_1PAGE.md`). It explains the project in 60 seconds. I hand it to every judge.

Why this matters:
- Judges see 100+ projects. They can't read every paper.
- A 1-page summary respects their time.
- The summary is what they take home — not the paper.
- The summary is the elevator pitch in print form.

**Rule:** Always have a 1-page summary. Print 50 copies. Hand them out.

---

## Lesson 10: Practice the pitch

I have a 10-min pitch (`PITCH_10MIN.md`) and a 3-min booth demo (`BOOTH_DEMO_SCRIPT.md`). I practice them 10+ times before the fair.

Why this matters:
- A polished pitch wins over a better project with a bad pitch.
- Practice makes you calm under pressure.
- Memorize the 3 anchor sentences. The rest flows.
- Practice with a parent or friend. Get feedback.

**Rule:** Practice your pitch at least 10 times. Out loud. With someone watching.

---

## Lesson 11: Have a fallback story

My project has a primary story (pre-trained GAT for small chips) and a fallback story (OpenROAD divergence on 1K+ cells, we fill the gap). If the primary story doesn't land, the fallback does.

Why this matters:
- Some judges care about novel ML. Some care about open-source EDA. Some care about industry impact.
- A multi-faceted story covers more judge types.
- If one angle is dismissed, you have others.
- The fallback is also a "wait, what?" moment.

**Rule:** Always have 2-3 ways to tell your story. Different judges care about different things.

---

## Lesson 12: Track time, take breaks, sleep

I worked 6 hours straight tonight. I shouldn't have. I should have:
- Worked 2 hours, taken a 30-min break
- Worked 2 more hours, taken another 30-min break
- Worked 2 more hours, then stopped

Burnout is real. The project is a year of work, not a sprint. Marathon, not 100-meter dash.

**Rule:** Take breaks. Sleep. Eat. The project needs a healthy human to survive.

---

## Lesson 13: Be honest about limitations

I have `OPEN_ISSUES.md` listing 7 un-defended claims. The real-routed GCD power isn't done. The DAC benchmarks aren't tested. The detailed placer is a heuristic.

Why this matters:
- Judges can tell when you're overclaiming.
- Honest limitations show scientific maturity.
- A clear "future work" section makes the project look bigger, not smaller.
- "Here's what I haven't done, here's why, here's my plan" is the answer.

**Rule:** Make a list of what you HAVEN'T done. Cite it. It makes the project stronger, not weaker.

---

## Lesson 14: Build for a specific audience, but write for everyone

I built SmallChip AI for chip designers. But the paper is for:
- ISEF judges (non-experts)
- Industry professionals (experts)
- College admissions officers (different lens)
- Future students (will read the code)

The paper has to work for all four. The headline number is the same. The story is the same. The depth varies by section.

**Rule:** Write for multiple audiences. Lead with the universal. Layer the technical.

---

## Lesson 15: Don't compare yourself to grad students

I'm a 9th grader. I'm not a Stanford PhD. My work is good, but it's not at the level of a $1M NSF-funded project.

That's OK. The point of ISEF isn't to compete with grad students. It's to show what a 9th grader can do with curiosity, discipline, and a year of work.

The story isn't "I'm as good as a grad student." The story is "look what a 9th grader can do." That's a more powerful story anyway.

**Rule:** Be honest about your level. The underdog story is your superpower.

---

## The 1-sentence summary

> Pick a real problem, use real benchmarks, build a real system, validate with real tools, document your failures, open-source everything, have a 1-page summary, practice the pitch, be honest about limitations, and remember you're a 9th grader — that's your superpower, not your weakness.

That's the lesson. Pass it on.
