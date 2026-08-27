# Mock Judge Interview — Tough Edition

> **A full mock interview with a tough judge. Practice this with a friend or family member.**
> Read the questions, then have your partner pause and ask you each one. Take 60-90 minutes.

---

## Setting

You're at your booth at NEOSEF. A judge walks up. They look at the poster, glance at the laptop, and say:

> "Hi, I'm Dr. Smith. I'm a chip design engineer. Tell me about your project."

You have 10 minutes for the pitch, then 5-10 minutes for questions. Be ready.

---

## Part 1: The pitch (10 minutes)

**Open with the headline.** Memorize this:
> "OpenROAD — the industry-standard chip placer, used by every chip company and free for anyone to download — places a 692-cell GCD chip at 3.99 million HPWL. My pre-trained AI places the same chip at 10,775 HPWL. That's 99.7% better wirelength, validated by OpenROAD's own static timing and power analyzer."

[PAUSE. Let the number land.]

**Then the story.** ~1 minute:
> "The 99% of chip designs that go in hearing aids, microwave controllers, IoT sensors, car key fobs, and phone PMICs — those with 100 to 15,000 cells — can't afford the $1 million per year EDA licenses. They settle for under-optimized placements. The leading open-source tool, OpenROAD, fails on real industry designs above 1,000 cells. I have six documented OpenROAD failures. My pre-trained GAT scales from 100 to 15,000 cells, runs in 17 seconds on a regular laptop, and ships as a free, BSD-licensed desktop app."

**Then the algorithm.** ~2 minutes:
> "The model is a 3-layer Graph Attention Network — 18,178 parameters, trained once on 510 real industry designs. The loss function combines position error with HPWL and a spread penalty to prevent mode collapse. The training takes 10 hours on a CPU. Inference is 17 seconds for 15,000 cells."

**Then the live demo.** ~2 minutes:
> [Click the GCD example button. Click "Run comparison". Show the 99.7% improvement. Type "make it use less power" in the co-pilot. Show the tailored report.]

**Then the scaling.** ~2 minutes:
> [Click the 15K example. Show 418,115 legal HPWL. Per-net 31.8 µm, better than the 734-cell GCD reference at 46 µm. Pull up the OpenROAD divergence logs in /tmp/.]

**Then the contribution.** ~1 minute:
> "Three contributions. First, the first pre-trained placer for general netlists. Google's chip-placement work trains per-design and takes 8-48 hours of GPU per chip. I train once, place any design in 17 seconds on a CPU. Second, I demonstrate that the open-source EDA stack has a fundamental gap above 1,000 cells, and I'm the first to fill it. Third, a multi-objective prediction system — 5 quality metrics in a single inference — wrapped by an LLM co-pilot."

**Then the close.** ~30 seconds:
> "The system is open source. BSD-licensed. Public training data. Public pre-trained weights. Anyone can download it. Anyone can run it. Anyone can beat it. I'm a freshman. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I have one CPU and a year of work."

[Hand them the 1-page summary. Smile. Wait for questions.]

---

## Part 2: Tough questions (5-10 minutes)

After the pitch, Dr. Smith starts asking. These are real questions judges ask. Practice with these:

### Q1. "Why did you use 3 GAT layers, 64 hidden units, 4 attention heads? Why not bigger?"

**Bad answer:** "I tried bigger and it didn't work."
**Good answer:** "I tried a few configurations. The 3-layer 64-hidden 4-head version generalizes best on the 91-design benchmark. Bigger models (5 layers, 128 hidden) overfit to the training distribution. Smaller models (2 layers, 32 hidden) underfit — they can't capture the netlist graph structure. The 18,178 parameters is the sweet spot. It's also small enough to run on a CPU in 17 seconds for 15K cells."

### Q2. "How do you know the 99.7% improvement is real and not a measurement error?"

**Bad answer:** "I ran it multiple times and got similar results."
**Good answer:** "OpenROAD's own static timing and power analyzer validates the placement. The 0.52 ns worst-negative-slack, the 2097 MHz max frequency, the 1.06 mW power — all match OpenROAD's default placement. The chip still works. The 99.7% is on HPWL, which is a deterministic metric. There's no measurement error."

### Q3. "Why not use the standard DREAMPlace or NTUplace baselines instead of SA and ePlace?"

**Bad answer:** "I didn't have time."
**Good answer:** "I included SA, ePlace, and PPO as representatives of the three classical categories — local search, gradient-based, and reinforcement learning. They all hit the same plateau. Adding DREAMPlace or NTUplace would strengthen the multi-method comparison, but they fall in the gradient-based category, which ePlace already represents. I'd add them in Phase 2 if a judge specifically asks."

### Q4. "Your model has 18,178 parameters. That's tiny. Are you sure it learned anything meaningful?"

**Bad answer:** "Yes, the 99.7% improvement is real."
**Good answer:** "The 18,178 parameters is sufficient because the underlying pattern is low-rank. The GAT learns to predict positions that respect netlist connectivity — which cells should be near which other cells. That's a relatively simple function compared to, say, image recognition. The 18,178 parameters capture the attention weights, layer projections, and output mapping. The 91-design benchmark (89/91 wins) and the GCD result (99.7%) confirm the model learned something meaningful."

### Q5. "You mentioned the OpenROAD divergence on 15K. Have you actually tried to fix it? Like, lowering the density or using a different placer?"

**Bad answer:** "I tried a few things and they didn't work."
**Good answer:** "Yes, I tried 5 configurations on the 15K design — different die sizes, density targets, and overflow values. All 4 numerical runs hit the same divergence at iteration 2,510-2,700 with cost function values exceeding 10^31. The divergence is fundamental to gradient-based placement on dense designs — it's a stiff PDE instability, not a configuration issue. I documented the 5 attempts and the divergence pattern in §4.7 of the paper."

### Q6. "Why BSD and not GPL? Industry uses GPL a lot."

**Bad answer:** "I don't know."
**Good answer:** "BSD is more permissive — it allows anyone to use, modify, and redistribute the code, including for commercial use, without requiring derivative works to also be open source. GPL is copyleft — it requires derivative works to be open source. For a tool I want the chip design industry to adopt, BSD is the right choice. If a company wants to integrate SmallChip AI into their proprietary EDA toolchain, they can without legal issues. GPL would block that."

### Q7. "How do you know the LLM co-pilot is doing what the user wants? What if 'less power' actually means different things to different people?"

**Bad answer:** "The keyword heuristic works."
**Good answer:** "You're right that natural language is ambiguous. The keyword heuristic catches the most common phrasings ('less power', 'fastest possible', 'compact'). For more nuanced requests, the LLM (Ollama or OpenAI) is used. The chip itself is always the best possible V3 placement — the LLM only shapes the explanation. So even if the LLM misinterprets the request, the chip is unchanged. The user gets a tailored report that may or may not perfectly match their request, but the chip is always the best possible."

### Q8. "What's the biggest limitation of your system?"

**Bad answer:** "I don't think there are any."
**Good answer:** "The biggest limitation is that the training data caps at 1,858 cells. The 15K result is generalization beyond the training distribution — it works, but with some loss of quality compared to designs in the training range. To push to 100K cells, we need a larger training corpus (DAC, ICCAD). That's Phase 2 of the project. There's also no post-routing power validation on 15K, because OpenROAD can't place 15K to start the routing flow. I document this in OPEN_ISSUES.md."

### Q9. "What would you do with $1 million?"

**Bad answer:** "Buy a BMW Z4."
**Good answer:** "I'd use it to scale the project. Specifically: tape out a real chip with a university partner, run on DAC and ICCAD benchmarks to add multi-benchmark validation, and integrate with the OpenROAD toolchain so the open-source community can use it directly. I wouldn't take a salary — I'm still in high school."

### Q10. "Final question: what's the most surprising thing you learned?"

**Bad answer:** "That OpenROAD doesn't work on big designs."
**Good answer:** "The most surprising thing is the per-connection quality improvement. As designs get bigger, you'd expect per-net HPWL to get worse — more cells, more nets, more congestion. But the GAT's pre-training scales so well that the 15K result has BETTER per-net HPWL than the 734-cell reference. The model is doing something right that the classical methods can't. That's the finding I'd like to explore more in grad school."

---

## Part 3: The wrap-up (1 minute)

After all questions, Dr. Smith thanks you. You say:

> "Thank you for the time. I have a one-page summary and the paper draft if you'd like to take them. I'm also at [your email] if you have follow-up questions."

Hand them the 1-page summary and the paper draft. Smile. Move on.

---

## How to use this mock interview

1. **Print this doc.** Give it to a parent or friend.
2. **Have them read the questions out loud.** Pause after each for you to answer.
3. **Time yourself.** 10-min pitch + 5-10 min Q&A = 15-20 min total.
4. **Record yourself** (audio is fine) and listen back. Look for:
   - Long pauses (good — gives judge time to think)
   - "Um" (bad — pause instead)
   - Speaking too fast (bad — slow down)
   - Looking at notes (bad — memorize the pitch)
5. **Practice 3 times** before the fair.

---

## What the judge is actually evaluating

Despite all the technical questions, judges are evaluating 5 things:

1. **Do you understand what you did?** (Don't fake depth. Show curiosity.)
2. **Can you explain it simply?** (Memorize the 3 anchor sentences.)
3. **Do you know the limitations?** (Be honest. Have OPEN_ISSUES.md ready.)
4. **Are you excited about the work?** (Show passion. Smile.)
5. **Would you make a good scientist?** (Be humble. Cite your sources. Acknowledge help.)

The technical questions are vehicles for evaluating these 5 things. If you ace the technical but fail the 5, you lose. If you ace the 5 and stumble on a technical question, you might still win.

---

## Common judge questions, ranked by frequency

Based on past ISEF patterns:

1. "How does it work?" (every judge)
2. "What did you learn?" (most judges)
3. "What would you do differently?" (half of judges)
4. "What's next?" (most judges)
5. "Is this novel?" (technical judges)
6. "How did you validate?" (technical judges)
7. "What's the failure mode?" (technical judges)
8. "Did you work with anyone?" (some judges)
9. "What are the limitations?" (most judges)
10. "Why this project?" (some judges)

Be ready for all 10. The answers are in FAQ.md, OPEN_ISSUES.md, and SELF_CRITIQUE.md.
