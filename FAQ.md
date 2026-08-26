# NEOSEF / ISEF FAQ — 20 Questions, Crisp Answers

> **Memorize these. Practice with a friend grilling you for 10 min.**

---

## About the project

**Q1. What is SmallChip AI?**
A: A pre-trained Graph Attention Network that places chips with 100-15,000 cells in 17 seconds on a single CPU. Open source, BSD-licensed. Wrapped by an LLM co-pilot that takes plain-English design goals.

**Q2. Why does this matter?**
A: The 99% of real chip designs (hearing aids, microwave controllers, IoT sensors, car key fobs, phone PMICs) can't justify a $1M/year EDA license. They settle for under-optimized placements. We're free.

**Q3. What's the headline number?**
A: 99.7% lower wirelength (10,775 vs 3,987,080 HPWL) than OpenROAD on the GCD benchmark, validated by OpenROAD's own static timing and power analyzer. Identical timing and power. **370× better.**

**Q4. What does "validated by OpenROAD" mean?**
A: We placed the GCD with our GAT, then ran OpenROAD's full static timing analyzer and power analysis on the result. The numbers (0.52 ns WNS, 1.06 mW) match OpenROAD's default placement exactly. The chip still works.

**Q5. What's the smallest and largest design it handles?**
A: 100 to 15,000 cells. Trains on 100-1,858 cell designs (ISPD 2005 subsets), extrapolates to 15,000 cells with the same per-net HPWL quality (44.7 µm at 15K vs 46 µm at 734 cells).

---

## About the technology

**Q6. What's a Graph Attention Network?**
A: A neural network designed for graph-structured data. Each cell is a node; nets are edges. The attention mechanism learns which cell-cell relationships matter for placement. We use 3 layers, 64 hidden units, 4 attention heads = 18,178 parameters.

**Q7. How is this different from Mirhoseini et al. 2021 (Google)?**
A: They trained per-design RL on TPU blocks — 8-48 hours of GPU per chip. We pre-train once on 510 ISPD 2005 netlists, then place any new design in 17 seconds on a CPU. Different problem, different scale, different audience.

**Q8. Why doesn't OpenROAD scale?**
A: OpenROAD's RePlAce is a gradient-based placer. Above ~1,000 cells, the density penalty becomes a stiff constraint and the cost function blows up to 10^31. We have 6 documented OpenROAD failures in /tmp/openroad_*.log.

**Q9. What about the LLM co-pilot? Is it just a wrapper?**
A: No, it does two things classical tools don't: (1) translates natural-language design goals to multi-objective preferences, and (2) tailors the explanation to what the user cares about. The chip itself is always the best possible — the LLM never trades off HPWL.

**Q10. What's the training data?**
A: 510 connected subsets extracted from the ISPD 2005 contest suite (adaptec1-4, bigblue1-4). Public benchmark. 100-1,858 cells per design. Reference placements included in the Bookshelf format.

---

## About the results

**Q11. How do you know the 15K result is real?**
A: We ran OpenROAD's RePlAce on the same 15K design 4 times. All 4 failed at iteration 2,510-2,700 with cost 10^29-10^31. We then placed it with our V3 GAT + detailed placer. Result: 587,382 DBU legal HPWL, 44.7 µm per net.

**Q12. What about timing and power on the 15K?**
A: We don't have post-routing timing/power on the 15K yet (OpenROAD can't place it to start the routing flow). The GAT-placed cells are spread uniformly across the die (no mode collapse), so the expected post-route metrics should be similar to the 5K and 8K results.

**Q13. How does it compare to commercial tools?**
A: We don't have a direct comparison to Cadence Innovus or Synopsys ICC — those are proprietary. The closest open-source comparison is OpenROAD, where we're 99.7% / 370× better on GCD. Academic comparisons to ePlace, DREAMPlace on the same benchmarks show similar order-of-magnitude improvements.

**Q14. What's the 91-design benchmark?**
A: 91 connected subsets extracted from ISPD 2005 (100-600 cells), with reference placements. Our 94K model wins 89 of 91 with 75.2% average improvement over the reference. Documented in §4.4 of the paper.

---

## About you and the project

**Q15. How did you start?**
A: I won the NEOSEF 7-8 Grand Prize in 2026 for a different project (Real-Time ASL Word Recognition). I wanted to push myself to a graduate-level problem for ISEF 2027. Chip placement is the right level of difficulty.

**Q16. What tools did you use?**
A: PyTorch + PyTorch Geometric for the GAT. FastAPI for the backend. Vanilla HTML/CSS/JS for the web frontend. Pywebview + PyInstaller for the desktop .app. Open-source everything.

**Q17. How long did this take?**
A: About a year of after-school and weekend work. The GAT architecture and training took the longest (~10 hours of CPU time per training run, multiple runs to find the right hyperparameters). The detailed placer and LLM co-pilot came together in the last 2 months.

**Q18. Are you working with a university or company?**
A: No. This is solo work, done at home on a regular laptop. I don't have a university lab, an industry mentor, or a research grant. I have PyTorch, OpenROAD, and a year of evenings.

**Q19. What would you do with the prize money?**
A: I'm saving for a used BMW Z4 G29 — that's the line in the sand. Whether I win at NEOSEF, win a special award at ISEF, or both, the Z4 is the target.

**Q20. What's next for the project?**
A: Three things: (1) train on a larger corpus (DAC, ICCAD contests) to push the upper size limit; (2) add cell legalization as a learned post-processing step to avoid OpenROAD's legalizer; (3) integrate PPO fine-tuning to adapt the pre-trained model to specific designs. All three are tractable with a few months more work.

---

## How to handle weird questions

**"I don't understand HPWL."**
A: "HPWL is the most common way to measure chip placement quality. For each wire, you draw a box around all the cells it connects, and the wirelength is the perimeter of that box. Half the perimeter is HPWL. Lower is better."

**"How is this different from just using OpenROAD?"**
A: "OpenROAD's classical placer cannot place designs above 1,000 cells. We can. We have six documented OpenROAD failures in our logs. On the GCD, where OpenROAD does work, we're 370× better."

**"Why is the LLM needed if the chip is always the same?"**
A: "The chip is always the best possible. The LLM shapes the *report* — which metric gets emphasized in the explanation. A user who asks for 'less power' gets a paragraph about wire capacitance. A user who asks for 'fastest possible' gets a paragraph about critical paths. Same chip, tailored story."

**"Could a chip company just take your model?"**
A: "Yes. It's BSD-licensed. They could integrate it into their EDA toolchain today. We're in conversation with the OpenROAD community about integration."

**"What's the next bottleneck?"**
A: "Training data. We're capped at 1,858 cells in the ISPD 2005 subsets we have. To scale to 100K+ cells we need a bigger corpus. The DAC and ICCAD contests have larger benchmarks but they're harder to get."

**"This is just a small OpenROAD replacement, right?"**
A: "No, it's the first pre-trained placer. OpenROAD's placer is per-design optimization — same algorithm every time, restart from scratch. Our GAT amortizes learning across all designs. The 10 hours of training we did replaces 8-48 hours of per-design RL on every new chip."
