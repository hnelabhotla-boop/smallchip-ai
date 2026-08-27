# 5-Minute Pitch (Conversational Version)

> **For casual conversations with teachers, parents, relatives, admissions officers, or anyone who asks "what's your project about?".**
> This is the everyday version. Conversational, not stage-pitch.

---

## The 5-min version

> "I built a free, open-source AI chip placer — kind of like Google Maps for placing transistors on a chip. Most chip design tools cost $1 million to $5 million a year, which locks out the 99% of designs that are too small. The leading free option, OpenROAD, fails on real industry designs above 1,000 cells because the math breaks down.

> "My pre-trained Graph Attention Network places 100 to 15,000-cell designs in 17 seconds on a regular laptop. On the standard GCD benchmark, it's 99.7% better than OpenROAD — 370 times — validated by OpenROAD's own static timing and power analysis. Same timing, same power, just shorter wires. The system is BSD-licensed, public training data, public pre-trained weights, downloadable as a macOS app.

> "The interesting finding is the scaling. The per-connection wire quality actually *improves* as designs get bigger. At 15,000 cells, my model gets 31.8 micrometers per net — better than the 734-cell reference at 46 micrometers per net. As designs get denser, my model gets *more* efficient, not less.

> "I'm taking it to ISEF 2027 through NEOSEF. The contribution is the pre-trained-amortized approach — Google's chip-placement work trains per-design and takes 8-48 hours of GPU per chip. I train once and place anything in 17 seconds. That's the novelty.

> "I have an LLM co-pilot that wraps it. You upload a chip design, type 'make it use less power' or 'I need this to run as fast as possible', and the co-pilot returns a tailored report. The chip is always the best possible — the LLM only shapes the explanation.

> "I'm a freshman at Strongsville High School. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I don't have a university lab. I have one CPU and a year of work."

---

## Variations by audience

### To a teacher
> "It's a research-level chip design project. I trained a Graph Attention Network on 510 real industry chip designs, and it generalizes to designs 30x larger than the training set. The validation is real — OpenROAD's own static timing and power analyzer confirms the placement works. I'm taking it to ISEF."

### To a parent or relative
> "I built an AI that designs computer chips better than the industry free tool. The 99% of chip designs that can't afford million-dollar tools can now use mine. It's all open source — anyone can download it. I'm taking it to a national science fair."

### To a college admissions officer
> "It's a graduate-level research project in applied machine learning for chip design. I designed the architecture, the training procedure, the loss function, and the validation pipeline. The system is published as open-source code on GitHub. I'm taking it to ISEF."

### To a friend
> "I made an AI that places computer chips. It's 370 times better than the best free tool. The math is PhD-level and I had to teach it to myself. Want to see a demo?"

### To a reporter
> "I built a free alternative to $1M chip design tools, as a high school freshman, in my bedroom, on a regular laptop. The system is open-source and validates 99.7% better than the industry free tool on the standard benchmark. I'm taking it to ISEF 2027."

---

## When to use which

- **3 minutes or less:** The 30-second elevator pitch (PITCH_10MIN.md §9)
- **5 minutes:** This file
- **10 minutes:** The full pitch (PITCH_10MIN.md)
- **Casual conversation:** The variations above
- **Formal presentation:** The full pitch + Q&A
- **On camera (for the booth video):** BOOTH_DEMO_VIDEO_SCRIPT.md

---

## The 3 sentences to ALWAYS lead with

1. **"Open-source AI chip placer, 99.7% / 370× better than OpenROAD on the GCD benchmark."**
2. **"Pre-trained — place any new design in 17 seconds on a regular laptop."**
3. **"BSD-licensed, public data, public weights — anyone can download and run it."**

These three work in any context. They cover: the headline number, the novelty, and the accessibility. Adjust the details based on the audience.

---

## What NOT to say (casual version)

- "It's just a side project" — it's a year of work
- "I think it might be useful" — let the numbers speak
- "I just need to..." — rephrase
- "It's kind of like..." — don't dumb it down too much

---

## Practice

Say it out loud 5 times. Time yourself. Should be 4:30-5:00 minutes, no longer.
