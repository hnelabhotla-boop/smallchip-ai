# ISEF Research Paper Outline (Full Submission)

> **The ISEF research paper is the official submission for ISEF 2027.**
> The existing `paper/ISEF_paper_draft.md` is the NEOSEF version. This is the
> ISEF version — longer, more detailed, more math, more figures.
> Target length: 25-35 pages, including figures.

---

## Structure

### Front matter (2 pages)
- Title, author, affiliation
- Abstract (250 words, slightly longer than NEOSEF)
- Acknowledgments (parents, science teacher, OpenROAD team, ISPD 2005 authors)
- Table of contents

### §1 Introduction (3 pages)
- **1.1 The chip placement problem.** What is it? Why is it hard? Why does it matter?
- **1.2 The 99% gap.** Why small-to-medium chip designs (100-15K cells) are underserved by industry ($1M/yr licenses) and open-source (RePlAce divergence).
- **1.3 This work's contributions.** Three contributions clearly stated. Pre-trained GAT. Open-source scalability fix. Multi-objective + LLM co-pilot.
- **1.4 Paper organization.** What's in each section.

### §2 Background (4 pages)
- **2.1 HPWL and wirelength metrics.** Formal definition, why HPWL is the standard.
- **2.2 GCD benchmark.** 692 cells, 463 nets, 45nm.
- **2.3 ISPD 2005 Bookshelf benchmarks.** adaptec1-4, bigblue1-4. Connected subset extraction.
- **2.4 OpenROAD.** What it is, how it works, why it's the standard.
- **2.5 The small-to-medium chip market.** Why 100-15K cells is the right target.
- **2.6 Related work.** Mirhoseini et al. 2021 (Google), WireMask-BBO, ePlace, DREAMPlace, NTUplace, ABCDPlace. How SmallChip AI differs.

### §3 Methods (8 pages)
- **3.1 The placement problem.** Formal statement.
- **3.2 Simulated Annealing.** (baseline)
- **3.3 PPO Reinforcement Learning.** (baseline)
- **3.4 ePlace.** (baseline, analytical)
- **3.5 GAT — our approach.** Architecture, hyperparameters, training procedure.
- **3.6 Multi-objective predictors.** 5 MLPs for timing, power, area, congestion.
- **3.7 LLM co-pilot.** Prompt → preference vector → report tailoring.
- **3.8 Hierarchical placement.** Initial scaling attempt.
- **3.9 Real detailed placer.** Row assignment, legalization, flipping, shifting, reordering.
- **3.10 Mathematical foundations.** HPWL formal, GAT attention equations, V3 loss with all 3 terms, complexity table, novelty argument.

### §4 Results (8 pages)
- **4.1 Primary result: GAT vs OpenROAD on GCD.** Full table with timing, power, frequency.
- **4.2 Two-model architecture.** 94K (multi-design winner) vs V3 (scaling winner).
- **4.3 V3 scaling curve.** 100 cells to 15,000 cells, with the new 464K result.
- **4.4 91-design benchmark.** Win rate, average improvement, distribution.
- **4.5 Algorithm comparison on GCD.** All 12 algorithms.
- **4.6 Industry impact.** $1M/yr, 9.3 GWh/yr, 3.6M BTU/hr.
- **4.7 The Scalability Wall.** OpenROAD RePlAce divergence, 4/4 + 1/1 failures.
- **4.8 Multi-objective predictor accuracy.** For each of the 5 metrics, the predictor's MAE on a held-out set.

### §5 Discussion (5 pages)
- **5.1 Why pre-trained placement works.** Amortization argument.
- **5.2 Generalization beyond training distribution.** ISPD 2005 → GCD → 15K bigblue1.
- **5.3 The multi-objective advantage.** Why 5 metrics in 1 inference matters.
- **5.4 The algorithmic plateau.** Why 12 classical methods get stuck at 1.3M.
- **5.5 Lessons for ISEF judges.** Methodology, engineering, honest reporting, validation, real-world impact, reproducibility.
- **5.6 The LLM co-pilot as a design tool.** Why natural language matters.
- **5.7 Limitations and honest reporting.** Training data caps at 1,858 cells. No post-routing timing on 15K. Detailed placer is local search, not learned.

### §6 Conclusion (2 pages)
- Summary of contributions
- Projected industry impact
- Future directions (DAC/ICCAD corpus, learned legalization, PPO fine-tuning)

### References (2 pages)
- ~30-40 references
- All cited properly

### Appendices (3-4 pages)
- **A. Code & data** (links to GitHub, training data, pre-trained weights)
- **B. Reproducing results** (step-by-step instructions)
- **C. Detailed placer pseudocode** (so reviewers can verify)
- **D. LLM co-pilot prompt examples** (so reviewers can verify)

### Figures (8-10 figures)
1. Plateau chart (already done)
2. Headline 370× chart (already done)
3. Scaling curve (5K → 15K)
4. Algorithm comparison bar chart
5. Multi-objective predictor accuracy scatter
6. Side-by-side routing congestion heatmap (TODO)
7. LLM co-pilot screenshot
8. Desktop .app screenshot
9. GitHub repo screenshot
10. Per-net HPWL vs cell count

### Tables (5-6 tables)
1. GAT vs OpenROAD on GCD (full metrics)
2. Two-model architecture comparison
3. Scaling curve table
4. 91-design benchmark statistics
5. Algorithm comparison on GCD
6. Industry impact numbers

---

## What's missing from the current draft

| Item | Status | Action |
|---|---|---|
| §3.6 Multi-objective predictors | exists, brief | expand with the predictor architecture + accuracy results |
| §4.8 Multi-objective predictor accuracy | missing | run the 5 MLPs on a held-out set, report MAE per metric |
| §5.7 Limitations | missing | write 1 page of honest limitations |
| §B. Reproducing results | exists, brief | expand with exact commands |
| §C. Detailed placer pseudocode | missing | write 1 page of pseudocode |
| §D. LLM co-pilot prompt examples | missing | capture 10 real prompts + responses |
| Figures 6, 7, 8, 9, 10 | mostly missing | build out (10 is most important) |
| References | partial | expand to 30-40 |

## Target length
- 30-40 pages
- 8-10 figures (all print-ready, 300+ DPI)
- 5-6 tables
- 30-40 references

## Submission deadline
ISEF abstract typically due ~3 weeks before the fair. The full paper is uploaded with the project materials at the fair. Plan to have v1.0 done by mid-March 2027.

## What to do next
1. Wait for the polish loop to finish (cell_w=2.0µm, 3.0µm, then restarts)
2. Update the paper with the final 15K number
3. Build the multi-objective predictor accuracy results (§4.8) — this is the missing piece
4. Write the limitations section honestly
5. Expand the appendices
6. Build the remaining figures
