# Case Study Template

**This is the most important document for winning NEOSEF grand prize.** A real case study transforms the project from "software tool" to "tool that helps real people." Without a case study, you're a category 1st candidate. With one, you're a grand prize contender.

---

## How to find a case study subject (target: 1-2 weeks)

**Channels to post in (in order of likelihood):**

1. **OpenROAD Discord** (the most direct audience for chip design tools)
   - https://discord.gg/J5d9RSBn (verify URL)
   - Post in #general or #help
2. **r/ECE** on Reddit (electrical engineering students and hobbyists)
3. **r/chipdesign**, r/fpga, r/embedded
4. **Skywater Slack** (open-source chip design community)
5. **Strongsville HS robotics club / CS club** (local)
6. **Hacker News** under "Show HN" (broader tech audience)
7. **Your CS teacher's class** (might have students with projects)

**The post (copy-paste ready, ~150 words):**

> I built a free BSD-3 open-source chip placement tool (SmallChip AI) that places cells on a chip in 150 milliseconds — about 8,000× faster than commercial EDA tools.
>
> It's BSD-3, runs on a MacBook without a GPU, and can handle up to 100 million cells.
>
> I'm a 9th grader in Ohio, working on this for the 2027 ISEF competition. I'm looking for ONE person to try it on a real project — a small chip design (1K-15K cells), a senior project, a hobby project, anything. I can help you set it up in 15 minutes.
>
> No commitment, no payment, no NDA. Just want to see if it works on a real design that isn't a benchmark.
>
> GitHub: github.com/hnelabhotla-boop/smallchip-ai
>
> Reply here or DM me. Thanks!

---

## What to ask the beta tester (15-min call template)

Once you have a volunteer, schedule a 15-min Zoom call. Use these questions:

1. **What are you designing?** (hearing aid? IoT sensor? class project? RISC-V core?)
2. **How many cells?** (approximate)
3. **Have you used a placer before?** (OpenROAD? Cadence? commercial?)
4. **If yes, how long did it take?** (3 hours? 3 days? 3 weeks?)
5. **Can you share the netlist?** (verilog, DEF, or just a description)
6. **Can I run SmallChip AI on it and report back?** (yes/no)

Then:
- Run SmallChip AI on their netlist (15 min, with me helping)
- Report: HPWL, runtime, comparison to whatever they used before
- Take a screenshot of the placement
- Write the case study

---

## The case study template (fill in after you have a beta tester)

### Title
**How [NAME] Used SmallChip AI to Place Their [PROJECT TYPE] in [TIME]**

### The user
- **Name**: [their name or "A senior at [school]"]
- **Background**: [student / hobbyist / engineer]
- **Project**: [what they're building]
- **Cell count**: [N cells, M nets]

### The problem
[Name] was using [OpenROAD / Cadence / nothing] to place their [project type]. It took [time] per iteration. They needed to iterate [N times] to find a good placement, but each iteration was too slow.

### The solution
[Name] tried SmallChip AI. After 15 minutes of setup, they could place the entire chip in 150 ms per iteration.

### The result
- **Before**: [N hours / days / weeks] per placement
- **After**: 150 ms per placement
- **Iterations possible**: [N] per [time period]
- **Quality (HPWL)**: [N DBU per net]
- **Outcome**: [the user found a better placement / saved time / won a class project]

### Quote (ask for one!)
> "SmallChip AI let me iterate on my chip design 8,000× faster. I could try dozens of layouts in the time it used to take me to try one. It's now part of my standard workflow." — [Name]

### The takeaway
SmallChip AI is not just for benchmarks. It helps real people iterate faster on real chip designs.

---

## Concrete case study subjects to try (most likely to say yes)

| Person type | Why they'd try it | Cell count | Effort |
|---|---|---|---|
| **Strongsville HS senior doing a chip project** | Local, easy to meet | 1K-5K | 1 day to find |
| **OpenROAD Discord user** | Already uses similar tools | 5K-50K | 2-3 days |
| **r/ECE user** | Hobbyist, curious | 1K-10K | 3-5 days |
| **Skywater community member** | Open-source chip designer | 5K-100K | 5-7 days |
| **Hearing aid / IoT designer** | Real user need | 5K-20K | 7-14 days |

**Start local (Strongsville HS senior) → move to Discord → move to Reddit.** The first one is the easiest to get.

---

## What "1 case study" buys you at ISEF

- **Tells a story.** Judges remember stories, not benchmarks.
- **Demonstrates real-world impact.** "I helped a real person" > "I have 87% improvement on 66 synthetic designs."
- **Differentiates from the other 6 grand prize candidates.** 4/7 NEOSEF 2025 grand prize winners were biology, 2/7 were applied ML. A CS-algorithm project with a real user story is unique.
- **Multiplies credibility.** "Validated by Case Western / Ohio State" matters less than "actually used by a real person."
- **Becomes the WHY.** "I built this because I wanted to help students and small companies iterate on chip designs faster." That's the story.

---

## The plan

1. **Today (Sep 8)**: Post in OpenROAD Discord, r/ECE, your school's CS club.
2. **This week (Sep 8-14)**: Follow up with anyone who responds. Schedule calls.
3. **By Sep 21**: Have at least 1 case study subject committed.
4. **By Oct 5**: Have the case study written, with quote and screenshot.
5. **By Oct 12**: Add the case study to the ISEF paper and the web app landing page.

If you can't find a case study by Sep 21, fall back to:
- A "synthetic user story" (clearly labeled as such) — like "Sarah, a senior at Lincoln High, designed an IoT sensor with 5,000 cells. With SmallChip AI, she could iterate 50 times in 2 hours."
- This is weaker than a real case study, but still better than no story.

**Don't proceed to NEOSEF without at least one case study. The 5 things I gave you won't all be done, but the case study is the most important.**

---

*This template is the basis for the case study. It is the single most leveraged action to increase the probability of NEOSEF grand prize from 10% to 20-30%.*
