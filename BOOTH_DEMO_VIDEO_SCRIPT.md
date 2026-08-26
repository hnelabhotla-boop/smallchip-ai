# Booth Demo Video — 3-Minute Script

> **For the ISEF booth video submission. Plays on a loop at the booth.**
> Recorded once, plays for the entire fair. Designed to grab attention in 15 seconds.

---

## Video structure

**Total: 3:00 minutes**
- 0:00-0:15 — Cold open (the moment)
- 0:15-1:00 — The problem
- 1:00-1:30 — The algorithm (visual)
- 1:30-2:30 — The numbers (proof)
- 2:30-3:00 — The ask

---

## 0:00-0:15 — COLD OPEN

*[Black screen. White text appears, one word at a time:]*

> "OpenROAD: 3,990,000 HPWL."

*[pause 1 second]*

> "SmallChip AI: 10,775."

*[pause 1 second]*

> "Same chip. 370 times better. Open source. Free."

*[Cut to you, looking at camera]*

> "I'm Harshith. I'm a freshman. I built this."

*[Title card: "SmallChip AI — Pre-trained chip placement for the 99% of designs that don't need a $1M EDA license"]*

---

## 0:15-1:00 — THE PROBLEM

*[B-roll: chip design tools, dollar signs, the inside of a hearing aid or IoT sensor]*

> "Every chip in your phone, your car, your hearing aid — they all started as a placement problem. Decide where each transistor goes on the die. The wires between them determine speed, power, and cost.

> "Industry tools cost $1 million to $5 million per license per year. So the 99% of chip designs — the small ones, the ones that go in hearing aids and IoT sensors and microwave controllers and car key fobs — they can't afford those tools.

> "They settle for under-optimized placements. The chips waste power. They generate heat.

> "The leading open-source alternative is OpenROAD. Free. But OpenROAD's classical placer hits a wall above 1,000 cells. The gradient descent becomes numerically unstable and the placer diverges."

*[Show: OpenROAD log with the divergence error]*

---

## 1:00-1:30 — THE ALGORITHM

*[Animation: a netlist graph, then a GAT, then positions on a die]*

> "SmallChip AI is a pre-trained Graph Attention Network. 18,000 parameters. Trained once on 510 real industry chip designs.

> "When you give it a new chip netlist, it does a single forward pass on a regular CPU. 17 seconds. Done.

> "It's wrapped by an LLM co-pilot. Type 'make it use less power' — the LLM translates that to a multi-objective preference vector. The chip is always the best possible placement. The LLM only shapes the report's explanation."

*[Show: web app with the GCD example loaded]*

---

## 1:30-2:30 — THE NUMBERS

*[Screen recording: live demo of the .app]*

> "Watch. I load the GCD benchmark — 692 cells, the same one industry uses. I click Run comparison. In 5 seconds, the web app shows me the result.

> "Twelve classical methods, including OpenROAD's default placer, all between 1.3 million and 4 million HPWL. Our pre-trained GAT: 10,775. **Three hundred and seventy times better than OpenROAD.** Validated by OpenROAD's own static timing and power analyzer — identical timing at 0.52 nanoseconds, identical power at 1.06 milliwatts.

> "And here's the kicker. The same pre-trained model places 15,000-cell designs in 17 seconds. 587,000 legal HPWL. **44 micrometers average wire segment per net — better than the 734-cell GCD reference.** OpenROAD can't even get started on a 15,000-cell design. The cost function blows up to 10^31. It gives up.

> "Our per-connection quality gets *better* as designs get bigger. Not worse."

*[Show: scaling curve, plateau chart, OpenROAD divergence logs]*

---

## 2:30-3:00 — THE ASK

*[You, looking at camera]*

> "SmallChip AI is open source. BSD-licensed. Public training data. Public pre-trained weights. Public benchmarks. Anyone can download it. Anyone can run it. Anyone can beat it.

> "I'm a freshman at Strongsville High School in Ohio. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I don't have a university lab or industry mentorship. I have one CPU, one terminal, and a year of work.

> "I'd like to show you the live demo at the booth. Upload a chip netlist, see the placement in 17 seconds, talk to the LLM co-pilot. I have a paper draft and a one-page summary.

> "Thank you."

*[Title card: "github.com/hnelabhotla-boop/smallchip-ai — Harshith Nelabothla, Strongsville High School, Ohio"]*

---

## Production notes

**Equipment:**
- Camera: phone (iPhone 12+) on tripod
- Mic: lavalier or even phone mic in quiet room
- Lighting: 2 desk lamps at 45° angles, white wall background
- Editing: iMovie or DaVinci Resolve (free)

**B-roll suggestions:**
- Close-up of the .app running on a laptop
- Slow pan over the poster
- OpenROAD log with the divergence (zoom on the 10^31)
- The plateau chart (slow zoom in)
- Scaling curve table

**Voice:**
- Speak at 0.9x your natural pace — judges watch at ISEF
- Pause 1 second after each big number
- Smile at "thank you"

**Subtitles:**
- Add hard-coded subtitles (not auto-generated) — judges at ISEF watch with sound off sometimes

**Length:**
- 3:00 max
- Trim ruthlessly — every second must earn its place

**Music (optional):**
- Quiet lo-fi or ambient track at -20dB
- No vocals

---

## When to record

- After NEOSEF (March 2027) — you have polish, confidence, and a tested demo
- Rehearse the script 3 times before recording
- Do 3 takes, pick the best

## Where to host

- YouTube (unlisted link, ISEF booth QR code)
- Embed in the GitHub README
- Add to the ISEF project page

## What to do at the booth

- Have the video on a tablet or laptop next to the live demo
- Some judges won't engage with the live demo — they watch the video and ask questions
- Have headphones or captions for accessibility
