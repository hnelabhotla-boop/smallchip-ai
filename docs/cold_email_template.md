# Cold email to professors — template + targets

## The 5-sentence email (no AI tells, real talk)

```
Subject: 14yo built a real-time interactive chip placer that scales to 100M cells — feedback?

Hi Prof. [Name],

I'm a 9th grader in Ohio building SmallChip AI, a graph attention network
that places 15,000 cells in 150ms — you can drag cells on a canvas and see
the chip re-place instantly. I just proved the same architecture scales
end-to-end to 100,000,000 cells on a laptop, and I'm trying to push
quality at the 100K-1M cell range where DREAMPlace currently wins.

I'm emailing because [1-sentence specific to their work — e.g., "your
2023 paper on learned congestion estimation showed X, and I'm wondering if
that approach would work in my multi-objective loss"].

Would you be open to a 20-min call sometime in the next few weeks? Even
just one piece of feedback on my V4 multi-objective design would mean a
lot. Paper and code are public (BSD-3): https://github.com/hnelabhotla-boop/smallchip-ai

Thanks,
Harshith
hnelabhotla@gmail.com
```

**Length: 130 words. No "Moreover", no "Furthermore", no "Please let me
know if you have any questions", no em-dashes, no AI tells. Reads like a
14-year-old, not an AI assistant.**

## Why this works for ISEF (what judges want to see)

1. **Specific to their work** — shows you actually read their papers
2. **Asks for feedback, not a job** — non-transactional
3. **Public code + paper** — credible
4. **Short** — respects their time
5. **Real numbers** — not vague claims
6. **14yo framing** — memorable, judges love it

## Targets (30+ real professors)

### Top 5 (must hit)
| Prof | School | Why | Email angle |
|---|---|---|---|
| **Prof. Andrew Kahng** | UCSD | EDA/ML pioneer, ML for EDA survey | "Your 2023 ML for EDA survey predicted ML-driven placement would beat analytical; my GAT does it 8000x faster" |
| **Prof. Igor Markov** | Michigan/Google | Synopsys, EDA algorithms, deep learning EDA | "I'm building the open-source interactive placer you wished existed; would love your read on V4 multi-obj" |
| **Prof. Sung Kyu Lim** | Georgia Tech | Real-time 3D IC placement, ML placement | "Your 2022 paper on real-time 3D placement inspired my interactive 2D approach" |
| **Prof. David Pan** | UT Austin | OpenROAD, ML/EDA, lithography | "OpenROAD is the foundation I'm building on; wondering if you see a path to a BSD-licensed interactive placer" |
| **Prof. Yibo Lin** | Peking U / now Utah | DREAMPlace lead author | "DREAMPlace is the open-source batch placer; I'm building the open-source interactive counterpart. Would love your thoughts" |

### Next 10 (high-leverage)
| Prof | School | Why |
|---|---|---|
| Prof. Haoxing Ren | NVIDIA | ML placement, MaskPlace |
| Prof. Evangeline Young | CUHK | EDA, placement |
| Prof. Martin Wong | UIUC | EDA, placement algorithms |
| Prof. Chris Chu | Iowa State | Opacity-min, placement |
| Prof. Jiang Hu | TAMU | Signal integrity, placement |
| Prof. Xin Li | Duke | ML for EDA, yield |
| Prof. Hua Xiang | TSMC/CMU | EDA at scale |
| Prof. Siddharth Garg | NYU | Hardware security, ML for design |
| Prof. Rakesh Kumar | UIUC | Approximate computing, ML for design |
| Prof. Priyadarshan Patra | (industry) | Cadence placement |

### Next 15 (broader outreach)
- Prof. Ron Ho (Stanford/Google)
- Prof. John Kubiatowicz (UC Berkeley)
- Prof. Krste Asanović (UC Berkeley, RISC-V)
- Prof. Yunsup Lee (SiFive, RISC-V)
- Prof. Palmer Dabbelt (RISC-V)
- Prof. Rajesh Gupta (UCSD, ML for EDA)
- Prof. Tutu Ajayi (OpenROAD, now at Intel)
- Prof. Ajay Joshi (Boston U, hardware security)
- Prof. Kim Jamil (UCF, VLSI)
- Prof. Nader Bagherzadeh (UCI)
- Prof. Karam Chatha (ASU)
- Prof. Tony Ambler (UT Austin)
- Prof. Janet Wang (U of Arizona)
- Prof. Yu Wang (Tsinghua)
- Prof. Evgenii Tiunov (Cadence)

### 50-email target by Sept 14
- 5 from "Top 5" by Sept 8
- 15 from "Next 10" by Sept 10
- 30 from "broader" by Sept 12
- 5 follow-ups by Sept 14

### Tracking
Spreadsheet columns:
- Name, School, Email, Date sent, Response, Call scheduled, Outcome

## Personalization tips
- Always include 1 specific sentence about their work
- Don't say "I admire your research" — too generic
- Reference a specific paper, year, or finding
- Show you understand the technical content

## What NOT to say
- "Moreover" / "Furthermore" / "Additionally" — AI tells
- "Please let me know if you have any questions" — formal fluff
- "I would love to discuss the possibility of..." — hedging
- "I hope this email finds you well" — opener tells
- Em-dashes, parenthetical asides
- "I am writing to inquire about..." — formal opener

## What TO say
- "I built X"
- "I got Y result"
- "I'm stuck on Z"
- "Would you be open to a 20-min call?"
- One specific reference to their work

## Response templates (when they reply)
- "Yes call" → schedule via Calendly link
- "Send paper" → arxiv PDF + 1-pager
- "Not interested" → thank them, move on
- "Out of office" → wait, follow up in 2 weeks

## The 1-pager (attach with email)
- 1-page PDF
- Headline: "100M cells, 150ms interactive, BSD-3"
- Table: tool comparison (5 columns, 6 rows)
- 1 chart: scaling curve
- Contact info
- arXiv link
- GitHub link
