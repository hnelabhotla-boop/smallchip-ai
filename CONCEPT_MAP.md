# SmallChip AI — Concept Map

> **The 5,000-foot view. One page, all the connections.**

---

## The Big Picture

```
PROBLEM                              SOLUTION
99% of chips can't afford $1M EDA   →  Pre-trained GAT placer, free
Open-source OpenROAD fails on 1K+   →  We work on 100-15K cells
Industry tools closed-source        →  BSD license, public code
Complex multi-objective placement   →  Single inference, 5 metrics
English-only designer interaction   →  LLM co-pilot, plain English
```

## The Architecture (data flow)

```
┌─────────────────┐
│ DEF file upload │  ← User drops a chip design
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DEF parser     │  ← chipmind/core/def_parser.py
│  → chip dict    │     {die, components, nets}
└────────┬────────┘
         │
         ├──────────────────────┐
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│  V3 GAT placer  │    │  LLM co-pilot   │
│  (3 layers,     │    │  (Ollama phi3   │
│  18,178 params) │    │  or OpenAI)     │
└────────┬────────┘    └────────┬────────┘
         │                      │
         │  raw placement       │  5-dim preference
         │  (x, y) in [0,1]²    │  vector
         │                      │
         ▼                      ▼
┌─────────────────────────────────────┐
│  Detailed placer                    │
│  Row assignment → legalization →    │
│  flipping → shifting → reordering →  │
│  iterate                            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Legal DEF      │  ← downloadable
│  + HPWL report  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OpenROAD STA    │  ← validates
│ + power analysis│     the placement
│  (optional)     │
└─────────────────┘
```

## The Math Stack

```
Linear algebra         →  Matrix ops, eigendecomposition (used in some baselines)
Probability            →  Softmax, soft min/max (used in V3 loss)
Calculus               →  Gradients (used in ePlace, RePlAce)
Graph theory           →  GAT operates on graphs
Attention              →  GAT attention mechanism
Combinatorial search   →  SA, GA, Memetic
```

## The Validation Stack

```
Internal:                                  External:
- HPWL (chipmind/core/hpwl.py)            - OpenROAD STA
- Per-net HPWL                             - OpenROAD power analysis
- Spread penalty metric                    - OpenROAD legalizer
- Mode collapse check                      - ISPD 2005 benchmarks
- Cell overlap count                       - FreePDK45 45nm library
```

## The 5 Algorithms Compared (in §4.5)

```
                    HPWL on GCD
                       ↓ lower is better
       ┌──────────────────────────────────────┐
OpenROAD (baseline)            3,987,080  ───┐
WireMask-EA                    3,595,900  ──┤
ePlace                         2,042,684  ──┤
Multi-start from OR            1,972,593  ──┤
PPO (from scratch)             1,970,000  ──┤
Memetic                        2,016,692  ──┤  plateau
Multi-stage SA                 1,314,254  ──┘  1.3-2M
                                            ──── THE PLATEAU
SmallChip AI GAT v3 (raw)         50,175  ──┐
SmallChip AI GAT v3 (legal)      10,775  ──┘  26× lower
                                              370× lower than OpenROAD
```

## The 5-Metric Predictor

```
Input: design features (9-dim)
       n_cells, n_nets, avg/max/min net size,
       die area, cell density, I/O count,
       avg net degree
         │
         ▼
   4 MLPs (4,801 params each)
         │
         ▼
Output: [timing, power, area, congestion]
        predicted from a single inference
```

## The Scaling Curve

```
Cells        Per-net HPWL
100           ~75 µm  (best)
1,000         ~80 µm
5,000        102.6 µm  (5K)
8,000         63.3 µm  (8K)    ← counterintuitive: better
10,000        54.7 µm  (10K)   ← as designs get bigger
15,000        33.2 µm  (15K)   ← per-net quality IMPROVES
```

## The 6 OpenROAD Failures

```
Run    Die         Density   Iter   Cost       Status
v2     1000x1000   0.7       2,700  9.17e+31   ❌ GPL-0305
v3     22Kx12K     0.7       2,680  9.51e+31   ❌ GPL-0305
v4     200x200     0.3       —      —          ❌ STA-0562 (syntax)
v5     200x200     0.5       2,700  9.17e+31   ❌ GPL-0305
v6     22Kx12K     0.7       2,690  6.71e+31   ❌ GPL-0305
5K     various     0.7       2,510  2.73e+29   ❌ GPL-0305
                                        ALL 6 FAILED
```

## The Locked Design Choices

```
1. Chip is always the best possible placer
   → LLM only shapes the report
   → No ParetoGATPlacer (rejected)

2. Use only the 99.7% / 370× post-legalization number
   → not the 98.7% pre-legal number
   → legalizer is OpenROAD's, not ours

3. Target small-medium chips ≤15K cells
   → MAX_CELLS_FOR_GAT = 20,000
   → don't compete on big designs

4. Free, open-source, no $1M license
   → BSD-licensed
   → public data, public weights

5. 5 quality metrics in 1 inference
   → HPWL, timing, power, area, congestion
   → LLM co-pilot wraps it

6. Real detailed placer replaces smart legalizer
   → row → legalize → flip → shift → reorder → iterate
   → 800K → 464K → 418K (15K)

7. Validation: OpenROAD's own legalizer + STA + power
   → GCD: 0.52 ns WNS, 1.06 mW (identical to OpenROAD default)
```

## The Business Model

```
For a 1B-chip product line:
$1M/year saved per design team
9.3 GWh/year energy saved
3.6M BTU/hr heat reduced

For Harshith:
$35K target → BMW Z4 G29 (used, 2020)
$50K padded → Z4 + 4 years of insurance/gas
```

## The 5-Second Pitch

> "OpenROAD: 3.99M HPWL on GCD. SmallChip AI: 10,775. 370× better. Free. Open source. 17 seconds on a laptop. First placer to handle 15K cells. I'm a 9th grader. I built this."

## The 1-Minute Pitch

> "I built SmallChip AI, a free open-source chip placer for the 99% of designs that can't afford $1M EDA licenses. The leading open-source tool, OpenROAD, fails on real industry designs above 1,000 cells — I've documented 6 failures. My pre-trained Graph Attention Network places 100 to 15,000-cell designs in 17 seconds on a regular laptop. On the GCD benchmark, it's 99.7% / 370× better than OpenROAD's default — validated by OpenROAD's own static timing and power analyzer. The system is BSD-licensed, public data, public weights, downloadable as a macOS app. I'm a 9th grader at Strongsville High School. I want to take it to ISEF."

## The 5-Minute Pitch

> See PITCH_10MIN.md
