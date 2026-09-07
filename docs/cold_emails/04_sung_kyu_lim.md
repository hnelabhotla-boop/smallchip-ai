# Cold email 4: Prof. Sung Kyu Lim (Georgia Tech)

**Why him**: Real-time 3D IC placement work, ML for physical design, deep ties to industry (Samsung, etc.). His 3D placement work directly inspired my interactive approach.

**His work hook**: His 2022 paper on real-time 3D IC placement showed that human-in-the-loop design beats batch for certain design styles. My interactive 2D approach is a natural extension.

---

**To:** limsk@gatech.edu
**Subject:** Inspired by your real-time 3D placement work — built the 2D version, BSD-3

Hi Prof. Lim,

I'm a 9th grader who read your 2022 work on real-time 3D IC placement. The thesis — that human-in-the-loop design beats batch for certain design styles — is exactly what I'm trying to prove in 2D.

I built SmallChip AI: a graph attention network placer with drag-to-re-place (14ms response), LLM co-pilot, and BSD-3 release. I proved the architecture scales to 30M cells with hierarchical partitioning.

Your 3D work inspired my 2D approach. The interactive framing is what's new — no other placer (Cadence, Synopsys, OpenROAD, DREAMPlace) is interactive at the cell level.

Would you be open to a 20-min call? I'm specifically interested in:
- How your 3D hierarchical partitioner works
- Whether 2D interactive + LLM co-pilot makes sense for analog/mixed-signal design
- ISEF tips for the engineering track

Paper: https://github.com/hnelabhotla-boop/smallchip-ai/blob/main/paper/arxiv_preprint.pdf
Code: https://github.com/hnelabhotla-boop/smallchip-ai

Thanks,
Harshith
hnelabhotla@gmail.com
