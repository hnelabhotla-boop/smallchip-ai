# Cold email 3: Prof. Yibo Lin (Utah, ex-DREAMPlace)

**Why him**: Lead author of DREAMPlace, the academic SOTA for GPU-accelerated placement. He's the most likely person to (a) respect the interactive angle and (b) critique fairly.

**His work hook**: DREAMPlace is the open-source batch placer; I built the open-source interactive counterpart. We're complementary, not competitive.

---

**To:** yibolin@cs.utah.edu
**Subject:** Built the interactive counterpart to DREAMPlace — would love your read

Hi Prof. Lin,

I'm a 9th grader who used DREAMPlace as a benchmark for my ISEF project. I built SmallChip AI, a graph attention network placer that's interactive (drag-to-re-place in 14ms) and has an LLM co-pilot. BSD-3, on GitHub.

DREAMPlace is the SOTA batch placer — I cite it in my paper. SmallChip AI is the open-source interactive counterpart. They're complementary: DREAMPlace wins on raw quality per pass, SmallChip AI wins on iteration speed and human-in-the-loop design.

I proved the architecture scales to 30M cells (random per-block in 50s) and have 100M scaling as next milestone.

Would you be open to a 20-min call? Two specific things I'd love your read on:
1. My V4 multi-objective loss (HPWL + congestion + thermal) — am I missing something obvious?
2. GPU-accelerated DREAMPlace vs CPU SmallChip AI at 1-15K cells — is this even a fair comparison?

Paper: https://github.com/hnelabhotla-boop/smallchip-ai/blob/main/paper/arxiv_preprint.pdf
Code: https://github.com/hnelabhotla-boop/smallchip-ai

Thanks,
Harshith
hnelabhotla@gmail.com
