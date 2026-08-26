# 100 Self-Test Questions

> **Quiz yourself. If you can answer 90+ without notes, you're ready for NEOSEF.**
> Use this in study sessions with a friend. They ask, you answer, no notes.

---

## Section 1: The Problem (Q1-15)

**Q1. What does HPWL stand for?**
A: Half-Perimeter Wire Length.

**Q2. Write the HPWL formula.**
A: For each net, sum (max x - min x + max y - min y) over all nets.

**Q3. Why use HPWL instead of routed wire length?**
A: HPWL is 1000x faster to compute. Routed wire length requires running a router.

**Q4. Why is HPWL a lower bound on routed wire length?**
A: Wires inside the bounding box must touch the perimeter at least twice. Half the perimeter is a tight bound.

**Q5. What is a chip netlist?**
A: A list of cells and a list of nets (groups of cells that should be connected).

**Q6. What's the input to a placer?**
A: A netlist + die area.

**Q7. What's the output of a placer?**
A: (x, y) position for each cell.

**Q8. Why is placement hard?**
A: 2N-dimensional non-convex optimization. For 10K cells, 20K dimensions.

**Q9. What does "non-convex" mean for placement?**
A: The cost function has many local minima. Gradient methods get stuck.

**Q10. What's the "99% gap"?**
A: 99% of chip designs (100-15K cells) can't afford $1M EDA licenses.

**Q11. Name 3 examples of small-to-medium chip designs.**
A: Hearing-aid DSPs, microwave controllers, IoT sensors, car key fobs, phone PMICs.

**Q12. What does "10 billion transistors" mean for a chip?**
A: Modern smartphone chips have ~10 billion transistors. Our 692-cell GCD has ~5K.

**Q13. What's the difference between a cell and a transistor?**
A: A cell is a logical unit (AND, OR, flip-flop). A transistor is the physical device. Each cell has 4-20 transistors.

**Q14. What's a "die"?**
A: The square of silicon on which the chip is fabricated. We place cells on the die.

**Q15. Why is shorter wire better?**
A: Less capacitance → less dynamic power → less heat → faster signals.

---

## Section 2: GAT (Q16-35)

**Q16. What's a node in the chip graph?**
A: A cell.

**Q17. What's an edge?**
A: A shared net between two cells.

**Q18. What does "GAT" stand for?**
A: Graph Attention Network.

**Q19. How many GAT layers in V3?**
A: 3.

**Q20. How many attention heads?**
A: 4.

**Q21. How many hidden units?**
A: 64.

**Q22. Total parameters?**
A: 18,178.

**Q23. What does an attention weight α_ij mean?**
A: How much node i should consider node j's information.

**Q24. Why do we need attention?**
A: Not all neighbors are equally important. Attention learns which matter.

**Q25. What are the input features (per cell, how many, what)?**
A: 9 features: net count, avg/max/min net size, normalized (x, y), relative density, constant.

**Q26. What's the output of the GAT?**
A: (x, y) position for each cell, in [0, 1]².

**Q27. What's the loss function for V3?**
A: λ₁ * position MSE + λ₂ * HPWL + λ₃ * spread penalty.

**Q28. What are the loss weights?**
A: λ₁ = 1.0, λ₂ = 0.01, λ₃ = 0.1.

**Q29. What is mode collapse?**
A: When all cells predict the same (x, y), making the placement useless.

**Q30. How does the spread penalty prevent mode collapse?**
A: It penalizes if cell positions are too close together (variance too low).

**Q31. What does "Tanh output" mean?**
A: The output layer uses Tanh, giving values in [-1, 1]. We shift/scale to [0, 1].

**Q32. Why use Tanh instead of Sigmoid?**
A: Sigmoid saturates (gradients vanish). Tanh doesn't.

**Q33. What does "residual connections" mean?**
A: Skip connections that add the input of a layer to its output. Helps with deep networks.

**Q34. What does "layer normalization" mean?**
A: Normalize activations within a layer. Stabilizes training.

**Q35. How long does V3 training take?**
A: ~10 hours on CPU for 60 epochs.

---

## Section 3: Benchmark (Q36-50)

**Q36. What's GCD?**
A: Greatest Common Divisor, a standard test chip from OpenROAD.

**Q37. How many cells in GCD?**
A: 692.

**Q38. How many nets in GCD?**
A: 463.

**Q39. What technology node?**
A: 45nm (FreePDK45).

**Q40. What's OpenROAD's HPWL on GCD?**
A: 3,987,080.

**Q41. What's our raw HPWL on GCD (V3)?**
A: 50,175.

**Q42. What's our post-legalization HPWL on GCD?**
A: 10,775.

**Q43. What's the improvement vs OpenROAD?**
A: 99.7% / 370× better.

**Q44. What's our timing result on GCD?**
A: 0.52 ns WNS, 2097 MHz (identical to OpenROAD default).

**Q45. What's our power result on GCD?**
A: 1.06 mW (identical to OpenROAD default).

**Q46. What does "WNS" mean?**
A: Worst Negative Slack — the worst timing violation across all paths.

**Q47. What's the ISPD 2005 contest?**
A: A 2005 chip placement contest. 8 industrial designs in Bookshelf format.

**Q48. What does the 91-design benchmark test?**
A: 91 ISPD 2005 connected subsets, separate from training. Tests generalization.

**Q49. What's our win rate on the 91-design benchmark?**
A: 89/91 = 98%.

**Q50. What's the average improvement on the 91-design benchmark?**
A: 75.2%.

---

## Section 4: OpenROAD and the Wall (Q51-65)

**Q51. What's OpenROAD?**
A: The leading open-source EDA toolchain. BSD-licensed, free.

**Q52. What does RePlAce do?**
A: Global placement using gradient descent on a smooth HPWL surrogate + density penalty.

**Q53. What is GPL-0305?**
A: OpenROAD's error code for "RePlAce diverged during gradient descent".

**Q54. Why does RePlAce diverge?**
A: Stiff PDE in the cost landscape. Gradient grows without bound at high density.

**Q55. At what cell count does OpenROAD start failing?**
A: Above ~1,000 cells.

**Q56. How many of our 6 OpenROAD attempts on 5K+ cells failed?**
A: All 6 (4/4 on 15K + 1/1 on 5K + 1 syntax error on 15K).

**Q57. At what iteration does RePlAce diverge?**
A: ~2,500-2,700.

**Q58. What does the cost function blow up to?**
A: 10²⁹ - 10³¹ (essentially infinity).

**Q59. Is this a bug in OpenROAD?**
A: No, it's a fundamental limitation of gradient-based placement on dense designs.

**Q60. What's the alternative to RePlAce?**
A: SA, ePlace, our V3 GAT.

**Q61. Why is ePlace also limited?**
A: Same gradient-based approach. Same stiff-PDE issue.

**Q62. What does "industry tools" refer to?**
A: Cadence Innovus, Synopsys ICC. $1M+/year per license.

**Q63. How does SmallChip AI fill the gap?**
A: Pre-trained GAT works where RePlAce diverges. BSD-licensed, free, CPU.

**Q64. What's the per-net HPWL on our 15K result?**
A: 33.2 µm (cell_w=2.0µm) or 31.8 µm (cell_w=3.0µm).

**Q65. How does that compare to GCD's 46 µm?**
A: Better (smaller = better). 15K has better per-connection quality than 692 cells.

---

## Section 5: The Detailed Placer (Q66-75)

**Q66. What's a legal placement?**
A: Cells on rows, snapped to sites, no overlap.

**Q67. What's the difference between raw and legal placement?**
A: Raw is what the GAT outputs. Legal is what can be manufactured.

**Q68. What does the detailed placer do?**
A: Row assignment → legalization → cell flipping → cell shifting → local reordering → iterate.

**Q69. What is cell flipping?**
A: Mirroring a cell vertically to reduce wirelength.

**Q70. What is cell shifting?**
A: Moving a cell 1 site left/right in its row.

**Q71. What is local reordering?**
A: Swapping adjacent cells in the same row.

**Q72. What's the cell width hyperparameter?**
A: Site width in micrometers. 0.5 to 3.0 µm in our sweep.

**Q73. What's the best cell width for 15K?**
A: 3.0 µm (gives 418,115 DBU).

**Q74. How long does the detailed placer take?**
A: ~4 minutes for 15K cells at one cell width.

**Q75. Why is 3.0µm better than 0.5µm?**
A: Smaller cells create more rows/columns, more iteration overhead, more overlap. Sweet spot is design-dependent.

---

## Section 6: LLM Co-Pilot (Q76-85)

**Q76. What does the LLM co-pilot do?**
A: Translates natural language to a 5-dim preference vector, runs V3, generates a tailored report.

**Q77. What are the 5 dimensions?**
A: HPWL, power, area, timing, congestion.

**Q78. Does the LLM change the chip?**
A: NO. The chip is always the best possible V3 placement.

**Q79. What does the LLM change?**
A: The explanation paragraph in the report.

**Q80. Why is the chip "always the best possible"?**
A: A chip optimized for "less power" by spreading cells would be a worse chip in absolute terms (longer wires, more capacitance, slower signals).

**Q81. What's the LLM parser based on?**
A: OpenAI-compatible LLM if API key set, else keyword-based heuristic.

**Q82. Example: what does "less power" map to?**
A: `[0.18, 0.47, 0.12, 0.12, 0.12]` (preference vector).

**Q83. What's Ollama?**
A: A local LLM runtime. We use phi3:mini for offline co-pilot.

**Q84. Where does the co-pilot run?**
A: In the .app and the web app. Backend endpoint: `/api/copilot`.

**Q85. What does the co-pilot remember?**
A: Conversation history within a session. Not across sessions.

---

## Section 7: Validation (Q86-92)

**Q86. How do we validate the GAT placement?**
A: Run OpenROAD's own STA + power analysis on the result.

**Q87. What's the WNS?**
A: 0.52 ns (identical to OpenROAD default).

**Q88. What's the max frequency?**
A: 2097 MHz (identical).

**Q89. What's the total power?**
A: 1.06 mW (identical).

**Q90. What's the 91-design benchmark?**
A: 91 ISPD 2005 connected subsets, separate from training.

**Q91. What's our win rate?**
A: 89/91 = 98%.

**Q92. What's a "held-out test set"?**
A: Designs not used in training. Tests generalization.

---

## Section 8: Business Case (Q93-100)

**Q93. How much do industry EDA tools cost?**
A: $1M-$5M per license per year.

**Q94. What does BSD-licensed mean?**
A: Anyone can use, modify, redistribute, including commercially. No restrictions.

**Q95. What's the projected energy saving at 1B chips?**
A: 9.3 GWh/year.

**Q96. What's the projected cost saving per design team?**
A: $1M/year.

**Q97. What's the projected heat reduction at 1B chips?**
A: 3.6M BTU/hour.

**Q98. Why is the GAT 18K parameters?**
A: 3 layers × 64 hidden × 4 heads + biases. Small enough to run on a CPU.

**Q99. What's the inference time on 15K cells?**
A: 17 seconds on a single CPU core.

**Q100. Why is pre-training better than per-design RL?**
A: Amortization. 10 hours of training, 17 seconds per inference forever. Google: 8-48 hours per chip.

---

## Score yourself

- **100/100**: ISEF Grand Prize ready
- **90-99**: NEOSEF Grand Prize ready, IEEE-CS likely
- **80-89**: NEOSEF competitive, IEEE-CS possible
- **70-79**: Need more study, focus on weak sections
- **<70**: Re-read STUDY_GUIDE.md and GLOSSARY.md

## How to use this quiz

1. Have a friend ask you 10 questions per day, randomly
2. Don't look at the answers until you've answered
3. Mark the ones you got wrong
4. Re-quiz on the wrong ones the next day
5. After 7 days, you should hit 90+ without notes
