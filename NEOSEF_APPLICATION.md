# NEOSEF 2027 Application Materials

> **For the NEOSEF Grand Prize application (due ~Feb 2027).**
> Abstract, project category, research question, hypothesis.

---

## 1. Project Title
**SmallChip AI: A Pre-Trained Graph Attention Network for Open-Source Chip Placement**

## 2. Category
**Embedded Systems (ENBED)** — placing standard cells on a chip die is a foundational embedded systems problem. Computer Science (COMP) is also acceptable.

## 3. Abstract (200 words, for NEOSEF application)

Modern chip placement relies on tools that cost $1M-$5M per license per year, locking out the 99% of real-world designs (hearing aids, microwave controllers, IoT sensors, car key fobs, phone PMICs) that contain 100-15,000 standard cells. The leading open-source alternative, OpenROAD, fails on real industry designs above 1,000 cells because its gradient-based placer (RePlAce) suffers from numerical instability on dense layouts (4 of 4 attempts on a 15,000-cell design diverge with cost exceeding 10³¹).

I present **SmallChip AI**, a pre-trained Graph Attention Network (GAT) that places 100-15,000-cell designs in 17 seconds on a single CPU core, with no per-design retraining. On the GCD benchmark, my GAT achieves 99.7% lower wirelength (10,775 vs 3,987,080 HPWL) than OpenROAD's default placer, validated by OpenROAD's own static timing and power analysis with identical timing (0.52 ns WNS) and power (1.06 mW). On 91 ISPD 2005 designs, my model wins 89/91 with 75.2% average improvement. The system includes a multi-objective predictor (5 quality metrics in one inference) and an LLM co-pilot that translates natural-language design goals into tailored reports. Open source (BSD), with public training data, public pre-trained weights, and a downloadable macOS/Windows/Linux app.

**Word count: 197**

## 4. Research Question
Can a pre-trained graph neural network place small-to-medium chip designs (100-15,000 cells) faster, more accurately, and more accessibly than existing open-source and commercial placement tools?

## 5. Hypothesis
A pre-trained Graph Attention Network, trained once on a corpus of real industry designs, can place any new small-to-medium chip design in seconds on commodity hardware with HPWL quality that exceeds the best classical and per-design reinforcement-learning placers, while remaining free and open-source.

## 6. Methodology
1. **Data:** 510 connected subsets extracted from the ISPD 2005 Bookshelf benchmark suite (adaptec1-4, bigblue1-4), 100-1,858 cells per design, with reference placements.
2. **Model:** 3-layer Graph Attention Network, 64 hidden units, 4 attention heads, 18,178 parameters total. Trained on 510-chip corpus for 60 epochs (~10 hours CPU).
3. **Loss function:** Position MSE + HPWL-aware loss + spread penalty (prevents mode collapse).
4. **Inference:** Single forward pass on CPU, 17 seconds for 15,000 cells.
5. **Detailed placement:** Real detailed placer (row assignment → legalization → cell flipping → cell shifting → local reordering) for legal layouts.
6. **Validation:** OpenROAD's own static timing analyzer and power analysis on the GAT-placed GCD benchmark.
7. **Comparison:** 11 baseline algorithms (Random, SA, ePlace, PPO, GA, Memetic, WireMask-EA, Multi-Stage SA, Multi-Start, OpenROAD default) on the same benchmark.

## 7. Results
- **GCD (692 cells):** 99.7% / 370× HPWL improvement vs OpenROAD, validated by OpenROAD's own analysis. Identical timing and power.
- **91-design benchmark:** 89/91 wins, 75.2% average improvement over reference.
- **15K bigblue1 subset:** 587,382 legal HPWL, 44.7 µm per net — better per-connection quality than the 734-cell GCD reference.
- **Scaling:** Single pre-trained model covers 100-15,000 cells. No per-design retraining.
- **Open-source contribution:** First placer to produce legal 15,000-cell placements without per-design retraining and without the numerical instability that defeats gradient-based placers (4/4 OpenROAD 15K runs fail with GPL-0305).

## 8. Personal Statement
I'm a freshman at Strongsville High School. I won the NEOSEF 7-8 Grand Prize in 2026 for a different project (Real-Time ASL Word Recognition) and went on to ISEF. For my second ISEF, I wanted to push myself to a graduate-level problem. Chip placement — the problem of placing millions of transistors on a die — is one of the hardest combinatorial optimization problems in computer science, and industry pays $1M/year per seat to use the best tools. I built a free, open-source alternative as a high school freshman. The system is BSD-licensed, the training data is public, the pre-trained weights are public, and the desktop app is downloadable. I want to show that with one CPU and a year of work, you can build production-grade chip-placement AI.

## 9. Categories this project fits
- **Embedded Systems (ENBED):** Chip placement is a foundational embedded systems problem.
- **Computer Science (COMP):** The ML system, training, and validation are core CS.
- **Systems Software (SOFT):** The .app, the Python package, the LLM co-pilot are all systems software.

(NEOSEF usually lets you pick one. I'd pick ENBED as primary, COMP as alternate.)

## 10. What's on the booth
- Laptop with the SmallChip AI .app open
- 36"x48" poster with plateau chart, scaling table, headline numbers
- 1-page project summary (handout)
- Paper draft (for judges who want depth)
- Live demo: 4 example buttons (GCD, 5K, 8K, 15K), co-pilot chat
- A DEF file or two to hand out

## 11. What I need from NEOSEF
- **Project category placement:** ENBED (preferred) or COMP
- **Judges with chip design or EDA background:** would help — could ask the hard questions
- **Booth space near a power outlet:** for the laptop
- **Permission to use OpenROAD's name in the poster:** standard fair use, should be fine

## 12. Risk and contingency
- **The .app crashes during the demo:** I have screenshots on the poster and the 1-page summary covers all key numbers.
- **A judge asks something I can't answer:** I have a FAQ document with 20 likely questions prepared. For unknowns, I say "great question, let me look that up in the paper" and check.
- **My laptop dies:** I have the project on GitHub, can pull it on a borrowed machine in 5 minutes.
- **The OpenROAD divergence story is challenged:** I have 6 log files as evidence, can show them on request.
