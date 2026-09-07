# Cold email 2: Prof. Igor Markov (Michigan / Google)

**Why him**: Synopsys veteran, EDA algorithms, deep learning for EDA, recent papers on VLSI placement quality. He's seen every placer in the industry.

**His work hook**: His 2015 Nature Communications paper on "VLSI Placement Quality" established the metrics everyone uses. My GCD 99.7% is reported using his framework.

---

**To:** imarkov@umich.edu
**Subject:** 14yo asking about quality vs speed tradeoff in learned placement

Hi Prof. Markov,

I'm a 9th grader building SmallChip AI — a graph attention network placer with sub-150ms inference and an LLM co-pilot. BSD-3 open source.

I read your work on VLSI placement quality metrics. I have a question: DREAMPlace gets ~30K HPWL on adaptec1 (211K cells) but takes 30 minutes on a V100. SmallChip AI gets 1,281 DBU/net on 15K real designs in 150ms (CPU). The tradeoff is real-time but lower quality per pass.

My current approach: V3 GAT single-pass + smart legalizer + detailed placer (flipping/shifting/swapping). For 1-15K cells this gets 87.7% improvement over random, validated on 66 held-out designs.

The question: in your view, is the right path to push for better single-pass quality (V4 multi-objective), or to keep real-time + accept that interactive iteration beats batch quality for small chips?

20-min call sometime in the next few weeks?

Code: https://github.com/hnelabhotla-boop/smallchip-ai
Paper: https://github.com/hnelabhotla-boop/smallchip-ai/blob/main/paper/arxiv_preprint.pdf

Thanks,
Harshith
hnelabhotla@gmail.com
