# Press & Interview Talking Points

> **If a local newspaper, school newsletter, or science blog interviews you after NEOSEF / ISEF.**
> Print this. Have it in front of you. Stay on message.

---

## The 30-second elevator pitch (memorize)

> "I'm Harshith Nelabothla, a freshman at Strongsville High School. I built SmallChip AI — a free, open-source AI chip placer that beats OpenROAD by 370 times on the GCD benchmark and runs on a regular laptop. The 99% of chip designs that can't afford a $1M/year EDA license can now use my pre-trained AI to get the same placement quality as the industry tools. I'm taking it to NEOSEF and ISEF to show that a high school freshman with one CPU can build production-grade chip-placement AI."

---

## Top 5 messages (always lead with these)

### 1. The number
> "OpenROAD — the industry standard — gets 3.99 million HPWL on the GCD benchmark. SmallChip AI gets 10,775. That's 370 times better. Validated by OpenROAD's own analyzer."

### 2. The accessibility story
> "The 99% of chip designs that go in hearing aids, microwave controllers, IoT sensors, car key fobs, and phone PMICs can't afford a $1M/year EDA license. SmallChip AI is free, open-source, and runs on a regular laptop. 17 seconds per design."

### 3. The novel contribution
> "This is the first pre-trained placer for general netlists. Google's chip-placement work trains per-design and takes 8-48 hours of GPU per chip. SmallChip AI is amortized: 10 hours of training once, 17 seconds per inference forever."

### 4. The OpenROAD failure story
> "OpenROAD's classical placer hits a wall above 1,000 cells. The gradient descent becomes numerically unstable. I have six documented OpenROAD failures in my logs — the cost function blew up to 10 to the 31st. No open-source solution existed for chips above 1,000 cells until I built one."

### 5. The youth angle
> "I'm a freshman. I built this with off-the-shelf PyTorch and a copy of OpenROAD. I don't have a university lab. I have one CPU, one terminal, and a year of work. I want to show other high schoolers that this level of work is possible."

---

## What to say when asked "How did you get into this?"

> "I won the NEOSEF 7-8 Grand Prize in 2026 for a different project — real-time ASL word recognition. That was a taste of what I could do with computer vision and machine learning. For my second ISEF, I wanted to push myself to a graduate-level problem. Chip placement is the right level — it's the problem of placing millions of transistors on a die, and industry pays $1M a year per seat for the best tools. I built a free, open-source alternative."

---

## What to say when asked "What's next?"

> "Three things. First, train on a larger corpus — DAC and ICCAD contests have bigger benchmarks. Second, add cell legalization as a learned post-processing step so we don't have to use OpenROAD's legalizer. Third, integrate PPO fine-tuning so the pre-trained model can adapt to specific designs. All three are tractable with a few more months of work."

---

## What to say when asked "How much did this cost?"

> "Zero dollars in software. I used free, open-source tools — PyTorch, PyTorch Geometric, FastAPI, OpenROAD, all BSD or MIT licensed. My laptop is the only hardware cost, and I already had that for school. The data I trained on is the public ISPD 2005 contest suite. Everything I built is reproducible by anyone with a laptop and a weekend."

---

## What to say when asked "Are you trying to start a company?"

> "I'm 14. I'm not trying to start a company right now. I'm trying to win ISEF. The system is BSD-licensed, so anyone can use it commercially — including chip companies, if they want to. I'm in conversation with the OpenROAD community about integrating SmallChip AI into the open-source EDA stack. That's a more interesting path for me than a startup."

---

## What to say when asked "What would you do with the prize money?"

> "I'm saving for a used BMW Z4 G29. That's the line in the sand. Whether I win at NEOSEF, win a special award at ISEF, or both, the Z4 is the target. Anything left over goes to college."

---

## What to NEVER say (even if asked)

- "I think this is the best" — let the numbers speak
- "I might want to" — be direct about what you've done
- "It's just a side project" — it's a year of work, treat it that way
- "I don't know the math behind it" — you do, you wrote §3.8
- "I want to be the next [famous person]" — be yourself, not a comparison
- "AI is going to replace chip designers" — this is a tool, not a replacement
- "OpenROAD is bad" — OpenROAD is great, the classical placer has limits

## Tough questions and how to handle them

### "Is this really better than OpenROAD, or just on benchmarks you chose?"

> "I chose the GCD because it's the standard chip-design benchmark — OpenROAD itself uses GCD as its reference. And the 15K result is a real industry design from the ISPD 2005 contest. The 91-design benchmark is across 91 connected subsets of real industry designs. OpenROAD is the industry tool I'm comparing against. I'm not gaming the benchmark."

### "But 1.06 mW power is the same as OpenROAD — doesn't that mean your chip is no better?"

> "The power is the same because at 692 cells, the cell library's intrinsic power dominates. The dynamic power scales with wire capacitance, which scales with wire length. We have 99.7% shorter wires. If we routed the design, the dynamic power would drop proportionally. The 1.06 mW number is the floor set by the cell library, not the wire contribution."

### "What if OpenROAD improves their placer and beats you?"

> "That's the point of being open source. I want them to. The system is BSD-licensed. If OpenROAD integrates my GAT into their toolchain, the open-source community wins. I'm not trying to beat OpenROAD — I'm trying to make the open-source EDA stack better for the 99% of designs that the proprietary tools ignore."

### "What if someone accuses you of using AI to write the code?"

> "I use AI assistance for parts of the workflow — I have access to Mavis, a coding assistant. The architecture, the math, the training procedure, the validation — those are mine. The AI is a tool, like PyTorch is a tool. The contribution is the design and the validation, not the keystrokes."

### "What if you don't win ISEF?"

> "Then I'll come back next year and try again. The project is good. The validation is real. The numbers are reproducible. If I don't win, it's because the competition was stiffer or my presentation wasn't sharp enough. The science doesn't change."

### "Are you going to study CS in college?"

> "I haven't decided. I like the intersection of ML and chip design — there's a lot of unsolved problems there. I might study EE, or CS, or both. I'll figure it out after ISEF."

---

## Body language for press interviews

- ✅ Sit up straight, hands visible on the table
- ✅ Make eye contact with the interviewer, not the camera
- ✅ Speak at 0.9x normal pace, pause for big numbers
- ✅ Smile when you talk about the project — show you love it
- ❌ Don't fidget
- ❌ Don't say "um" — pause instead
- ❌ Don't look at notes during a filmed interview
