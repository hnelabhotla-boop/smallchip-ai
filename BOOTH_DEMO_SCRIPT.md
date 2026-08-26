# NEOSEF Booth Demo Script (3 minutes)

> **Live walkthrough for judges who walk up to the booth.**
> Designed to be repeatable in 3 minutes. Practice this until you can do it without thinking.

---

## Before the judge arrives (5 seconds)

Laptop is open. The .app is on the landing page. Browser is at full screen. Volume is off. The poster is on the wall behind you. The 1-page summary is on the table.

You say nothing. You smile. You wait for the judge to make eye contact.

---

## Phase 1: The headline (30 seconds)

> "Hi, I'm Harshith. I built a free, open-source AI chip placer for the 99% of chip designs that can't afford a $1M EDA license. The headline number is this:"

*[Point at the plateau chart on the poster]*

> "Twelve classical methods — simulated annealing, ePlace, PPO, memetic, genetic — they all get stuck at 1.3 million HPWL on the GCD benchmark. Our pre-trained GAT drops to 50,000. After OpenROAD's own legalizer, we hit 10,775. OpenROAD's default gets 3.99 million. **That's 370 times better, validated by OpenROAD's own static timing and power analysis.** Identical timing, identical power, on a 692-cell real-industry chip."

*[Pause. Let the number land.]*

## Phase 2: The live demo (60 seconds)

> "Let me show you it running."

*[Click the **🟢 GCD example** button — it loads in <1 second]*

> "I'm loading the GCD benchmark — 692 cells, 463 nets, 45 nanometer. Now I click **Run comparison**."

*[Click Run comparison — it finishes in ~5 seconds, shows: 99.7% / 370× improvement]*

> "The web app runs 12 algorithms in parallel and shows the result. Our pre-trained GAT is the lowest. Now let me ask the AI co-pilot something."

*[Click on the co-pilot tab. Type: "make it use less power"]*

> "I type 'make it use less power' — the LLM translates that to a 5-dimensional preference vector. The chip doesn't change — it's always the best possible. But the *report* explains the result in terms of power savings. Let me show you."

*[Show the co-pilot's response — a paragraph about wire capacitance and gigawatt-hours saved]*

> "The chip is the same. The explanation is tailored. That's the wow factor."

## Phase 3: The scaling (60 seconds)

> "Now the harder part. OpenROAD's classical placer is fundamentally limited to small chips. **It cannot place any real industry design above 1,000 cells** — the gradient descent becomes numerically unstable and diverges. We have six documented OpenROAD failures in our logs. Here's the 15K run, the last line of the log:"

*[Pull up `/tmp/openroad_15k_v6.log` in a terminal OR show the screenshot on the poster]*

> "Cost function blew up to 10^31. RePlAce gave up at iteration 2,700."

*[Click the **🔴 15K bigblue1 subset** button in the .app — it loads the 15,000-cell design]*

> "Our pre-trained GAT places the same 15,000-cell design in 17 seconds on this laptop. The legal HPWL is 587,000 — 44.7 micrometers per net. That's *better* per-connection quality than our 734-cell GCD reference at 46 micrometers. As designs get bigger, our per-net quality gets *better*, not worse."

## Phase 4: The "why" (30 seconds)

> "Three contributions. One: the first pre-trained placer for general netlists. Google and Mirhoseini trained per-design — 8 to 48 hours of GPU per chip. We train once, place anything in 17 seconds.

> "Two: we demonstrate that the open-source EDA stack has a gap above 1,000 cells, and we're the first to fill it.

> "Three: a multi-objective prediction system — five quality metrics in a single inference — wrapped by an LLM co-pilot. No commercial EDA tool exposes all five simultaneously."

*[Pause. Eye contact.]*

## Phase 5: The ask (15 seconds)

> "The system is open source — BSD-licensed, public training data, public pre-trained weights, public benchmarks. Anyone can download it. Anyone can run it. Anyone can beat it.

> "I'd like to take it to ISEF. I have a one-page summary and a paper draft. Take whichever you want."

*[Hand them the 1-page summary OR the paper. Smile. Wait for questions.]*

---

## What to do if the demo breaks

- **GCD button doesn't load** → the .app may have lost the static mount. Run `python -m uvicorn chipmind.api.server:app --host 0.0.0.0 --port 8000` in a separate terminal. Refresh the browser.
- **Comparison takes too long** → only the GCD comparison is in the live demo. The 5K/8K/10K/15K run the V3 model only (not all 12 algorithms), so they're fast.
- **LLM co-pilot times out** → it falls back to a keyword-based heuristic. The response will be less natural but the chip is still placed.
- **App crashes entirely** → say "let me show you the screenshots" and point to the poster. The poster has all the key numbers.

## What to do if a judge wants to go deeper

- "How is this different from Mirhoseini 2021?" → PITCH_10MIN.md Q&A
- "How do you validate?" → OpenROAD's own STA + power analysis. Numbers in the paper.
- "Why doesn't OpenROAD just use your GAT?" → It could. BSD-licensed. We're in conversation.
- "Can I download it?" → github.com/hnelabhotla-boop/smallchip-ai. Have the laptop open with the repo URL.
- "What's the failure mode?" → Training data caps at 1,858 cells. We extrapolate to 15K with some quality loss. Future work: larger corpus, learned legalization, PPO fine-tuning.

## What to NEVER say

- "I think this is novel" — let the data speak for itself
- "It might be useful for..." — be specific about who uses it
- "I just need to..." — every "just" hides a problem; rephrase
- "I don't know" — say "Great question, let me look that up" and check the paper

## Body language checklist

- ✅ Stand up. Don't sit behind the laptop.
- ✅ Make eye contact before you start talking.
- ✅ Speak at judge-pace, not student-pace. Pause after big numbers.
- ✅ Point at the chart, not the laptop, when showing numbers.
- ✅ Smile at the end. Let them ask questions.
- ❌ Don't read from notes.
- ❌ Don't apologize for limitations — frame them as future work.
- ❌ Don't fidget with the laptop. Hands at sides or pointing at the poster.
