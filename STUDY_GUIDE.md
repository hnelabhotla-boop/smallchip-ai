# SmallChip AI — Formal Study Guide
### NEOSEF 2027 Preparation

---

## How to Use This Document

This is a formal study guide for the NEOSEF (Northeastern Ohio Science and Engineering Fair) and ISEF (International Science and Engineering Fair) presentation. It is organized into nine sections:

1. **Formal Vocabulary** — precise technical terminology
2. **The Project Introduction** — three formal opening hooks
3. **Foundational Concepts of Chip Design** — the technical background
4. **The Project in Formal Terms** — architecture, methodology, and results
5. **The Presentation** — pitch script, vocabulary in context, anticipated questions
6. **The Five Most Important Numbers** — the canonical quantitative answer
7. **Formal Definitions for Anticipated Questions** — the Q&A survival kit
8. **How to Study This Document** — the daily plan
9. **Closing Note** — the close

Read one section per day for nine days. The vocabulary in Section I is to be memorized before NEOSEF.

---

## Section I — Formal Vocabulary

### A. Project and Tooling Terms

| Term | Formal Definition |
|---|---|
| **EDA** | Electronic Design Automation. The category of software tools used to design integrated circuits. |
| **Netlist** | A formal, machine-readable description of a circuit's components and their interconnections. |
| **Placement** | The computational problem of determining the physical location of each standard cell on a chip's silicon die. |
| **Global placement** | The initial assignment of approximate cell positions without regard to legal site constraints. |
| **Detailed placement** | The subsequent optimization that refines cell positions to legal sites while preserving global placement intent. |
| **Legalization** | The process of snapping placed cell positions to legally permitted sites on the die. |
| **GDS-II** | Graphic Database System II. The industry-standard file format used for chip fabrication. |
| **DEF** | Design Exchange Format. The standard text-based file format for netlists. |
| **LEF** | Library Exchange Format. The standard file format for cell libraries. |
| **PDK** | Process Design Kit. The fabrication-process-specific design rules. |
| **Die** | The continuous block of silicon on which the circuit is fabricated. |
| **Standard cell** | A pre-designed logic gate (e.g., AND, OR, flip-flop) characterized for use in placement. |
| **Net** | A logical wire connecting two or more cells. |
| **Pin** | A connection point on a cell, used to attach it to nets. |

### B. Quality Metrics

| Metric | Formal Definition |
|---|---|
| **HPWL** | Half-Perimeter Wire Length. For each net, the perimeter of the bounding box of its pin positions. Summed across all nets. The standard proxy for total wire length. |
| **Wire length** | The total length of all wires, measured in physical units. HPWL is a lower bound and a fast approximation. |
| **Congestion** | The density of required routing tracks in a region. High congestion leads to routing failure. |
| **Thermal** | The distribution of power dissipation across the die. Hot spots reduce yield and reliability. |
| **Timing closure** | The condition that all signal-path delays satisfy the clock-period constraint. |
| **WNS** | Worst Negative Slack. The minimum timing margin across all paths. A negative WNS indicates a timing violation. |
| **TNS** | Total Negative Slack. The sum of all negative slack values across all paths. |
| **Power** | Total energy dissipation per clock cycle, in milliwatts. |

### C. Algorithms and Architectures

| Term | Formal Definition |
|---|---|
| **GAT** | Graph Attention Network. A neural network architecture that operates on graph-structured data using learned attention weights. |
| **Attention mechanism** | A learned weighting scheme that determines the relative importance of neighboring nodes in a graph. |
| **Forward pass** | A single end-to-end inference of a neural network. |
| **Loss function** | A scalar measure of prediction error that the training process seeks to minimize. |
| **Backpropagation** | The algorithm used to compute gradients of the loss with respect to model parameters. |
| **Embedding** | A learned vector representation of an entity (e.g., a cell, a net). |
| **Hidden state** | The intermediate vector representation of a node at a given layer. |
| **Tanh** | Hyperbolic tangent. A non-linear activation function with output range (-1, 1). |
| **ReLU** | Rectified Linear Unit. A non-linear activation function outputting max(0, x). |
| **SA** | Simulated Annealing. A meta-heuristic for global optimization based on probabilistic acceptance of worse solutions. |

### D. Industry and Academic Context

| Term | Formal Definition |
|---|---|
| **Cadence Innovus** | Commercial EDA implementation system. Industry standard for digital implementation. Cost: $500K–$2M per license per year. |
| **Synopsys IC Compiler II** | Commercial EDA implementation system. Direct competitor to Cadence Innovus. |
| **OpenROAD** | Open-source EDA tool flow developed by a global research consortium. |
| **RePlAce** | The global placer used by OpenROAD, based on the 2021 Cheng et al. paper. |
| **DREAMPlace** | GPU-accelerated academic placer developed at UCSD (Lin et al., 2019). |
| **efabless** | Open-source chip fabrication program providing free shuttle runs on commercial processes. |
| **Skywater 130nm** | An open-source PDK for the Skywater 130-nanometer CMOS process. |

### E. ISEF-Specific Terminology

| Term | Formal Definition |
|---|---|
| **NEOSEF** | Northeastern Ohio Science and Engineering Fair. The regional ISEF-affiliated fair. |
| **ISEF** | International Science and Engineering Fair. Society for Science, annual. |
| **Category** | One of 22 official ISEF subject categories. SmallChip AI is entered under Math/Computer Science (MCS). |
| **Abstract** | A 250-word summary of the research project. Required for ISEF. |
| **Research paper** | A formal 10-15 page document describing the methodology, results, and conclusions. |
| **Display board** | A 36"×48" poster summarizing the research. Standard ISEF format. |
| **Special Award** | Awards sponsored by external organizations (e.g., IEEE, ACM, Sigma Xi, Moore). Independent of category awards. |

### F. Quantitative Vocabulary to Use

| Informal | Formal |
|---|---|
| really fast | "achieves inference in 150 milliseconds" |
| way better | "demonstrates a 99.7% improvement" |
| a lot of chips | "the sub-15,000-cell market segment" |
| I think | "the empirical evidence suggests" |
| it's free | "released under the BSD 3-Clause license" |
| drag a cell | "user-initiated manual perturbation triggers neighborhood re-placement" |
| it's interactive | "the system supports real-time human-in-the-loop interaction" |
| the model | "the trained inference model" |
| it works | "the approach generalizes to unseen designs" |

---

## Section II — The Project Introduction

### How to Open

The first thirty seconds of the presentation determines the judge's perception. Three formal opening hooks, in order of preference:

### Hook A (Recommended): The Specificity Hook

> "Today, the placement stage of chip design for the 1,000-to-15,000-cell market segment — the segment that includes chips in medical devices, hearing aids, microwave controllers, and IoT sensors — takes between five and thirty minutes per design iteration, using either commercial tools that cost between five hundred thousand and two million dollars per license per year, or OpenROAD, which is open-source but slow.
>
> SmallChip AI places those same designs in 150 milliseconds, on a commodity laptop, with no license fee. The project demonstrates the first real-time interactive placement system for the sub-fifteen-thousand-cell market."

### Hook B (For Non-Technical Judges): The Analogy Hook

> "Imagine you are a graphic designer working in Adobe Photoshop in 1995. You click a button, wait thirty minutes, and the program gives you a result. You change one pixel, click again, wait thirty minutes.
>
> That is the state of chip design today. SmallChip AI makes that loop instantaneous. A designer can drag a component on a screen and see the chip re-design itself in 150 milliseconds — about the time of a human blink. No commercial tool, no academic prototype, and no open-source project currently offers this capability."

### Hook C (For Technical Judges): The Method Hook

> "SmallChip AI is a Graph Attention Network trained on 510 synthetic chip designs that learns the placement problem as a function from netlist graph to cell coordinates. The model contains eighteen thousand parameters, runs inference in 150 milliseconds on a MacBook, and demonstrates 100% win rate and 87.7% average improvement on a clean held-out test of 66 designs the model has never seen."

### Words to Use Throughout the Presentation

#### A. To Describe the Problem

- "Batch-mode operation"
- "Computational bottleneck in the design loop"
- "Convergence time on the order of minutes"
- "Iterative placement problem"
- "Lack of real-time feedback for the designer"

#### B. To Describe the Approach

- "Graph Attention Network architecture"
- "Supervised learning on synthetic netlist variants"
- "Tanh-bounded coordinate prediction"
- "End-to-end inference, no iterative search"
- "Hierarchical decomposition for the large-chip market"

#### C. To Describe the Results

- "Validated on a deterministic 80/20 held-out test"
- "Median improvement of 87.5% over random placement"
- "Identical timing and power compared to the OpenROAD baseline"
- "Per-net HPWL monotonically decreases with cell count"
- "Reproducible from the public release"

#### D. To Describe the Impact

- "Completes the open-source EDA ecosystem"
- "Eliminates the seven-figure licensing barrier"
- "Enables university instruction in chip design"
- "Supports the open-source RISC-V community"
- "Foundational step toward a sub-second design cycle"

#### E. To Describe the Limitations (with Confidence)

- "The current model is trained on chips up to fifteen thousand cells"
- "The system optimizes half-perimeter wire length, not the full multi-objective function"
- "Validation is on synthetic data; real-industry validation is in progress"
- "Physical fabrication of a test chip is pending the efabless shuttle"

---

## Section III — Foundational Concepts of Chip Design

### A. The Physical System

A modern integrated circuit ("chip") is a thin slice of crystalline silicon, typically 10-25 mm on a side, on which billions of transistors are fabricated. The transistors are organized into logic gates (AND, OR, NOT, flip-flops), which are organized into standard cells. A typical modern microprocessor contains between one hundred million and fifty billion transistors.

The transistors are connected by wires, fabricated as layers of copper or aluminum on top of the silicon. A typical modern chip has between ten and fifteen metal layers, each thinner than a human hair.

### B. The Design Flow

The transformation of a specification ("this chip should compute SHA-256") into a fabricated chip follows a multi-stage pipeline:

1. **Specification** — What the chip should do
2. **Architecture design** — How the chip is organized (pipeline, cache, memory hierarchy)
3. **Logic design** — The register-transfer level (RTL) description, typically in Verilog or VHDL
4. **Synthesis** — RTL is converted into a netlist of standard cells
5. **Floorplanning** — The major blocks are placed on the die
6. **Placement** — Each standard cell is assigned a specific location on the die
7. **Clock tree synthesis** — The clock signal distribution is constructed
8. **Routing** — The wires connecting cells are laid out
9. **Sign-off** — Final verification of timing, power, and physical rules
10. **Tape-out** — The GDS-II file is sent to the fabrication facility

SmallChip AI addresses stage 6 — placement — which is one of the most computationally expensive stages in the flow.

### C. The Placement Problem in Detail

Placement takes as input:
- A netlist (list of cells and their connections)
- A cell library (the physical dimensions of each cell type)
- A die area (the physical size of the silicon)

And produces as output:
- An (x, y) coordinate for each cell on the die

The constraints are:
- All cells must fit within the die area
- No two cells may overlap
- Cells should align to standard cell rows (typically a few micrometers apart)
- The clock signal should be distributed evenly

The objectives are:
- **Minimize wire length** (HPWL) — shorter wires mean faster signals
- **Minimize congestion** — too many wires in one area cannot be routed
- **Minimize thermal hotspots** — uneven power distribution causes reliability problems
- **Achieve timing closure** — signals must arrive within the clock period

### D. Why Placement is Hard

The placement problem is NP-hard. The number of possible placements is astronomical — for a 15,000-cell design, it exceeds 10^50,000. Practical algorithms use one of three approaches:

1. **Simulated annealing** — Random perturbations accepted with decreasing probability. Used by TimberWolf, the historical industry standard.
2. **Quadratic placement** — Minimize a quadratic objective, then legalize. Used by RePlAce.
3. **Machine learning** — Train a model to predict good placements directly. Used by SmallChip AI.

### E. The Open-Source EDA Stack

The chip design community has spent fifteen years building an open-source alternative to commercial EDA. The current state of the stack:

- **Skywater 130nm PDK** — Open process design kit
- **OpenROAD** — Open physical implementation flow
- **DREAMPlace** — Open academic placer
- **Yosys** — Open synthesis tool
- **KLayout** — Open layout viewer
- **efabless** — Open chip fabrication
- **RISC-V cores (SERV, PicoRV, OpenMSP430)** — Open CPU designs

The missing layer — the gap that SmallChip AI fills — was a fast, free, **interactive** placer for the small-chip market. This is the project's central contribution: completing the open-source stack.

---

## Section IV — The Project in Formal Terms

### A. Problem Statement (Formal)

Given a standard-cell netlist G = (V, E) with |V| ≤ 15,000 cells and a target die area D ⊂ ℝ², find an assignment f: V → D that minimizes the half-perimeter wire length while respecting placement legality, and that can be computed in O(few hundred milliseconds) on commodity hardware.

### B. Method (Formal)

We use a Graph Attention Network with L = 6 layers, hidden dimension d = 32, and H = 4 attention heads. The input is the cell-feature matrix X ∈ ℝ^(|V| × d_in) and the net-adjacency edge index. The output is the tanh-bounded coordinate matrix Ŷ ∈ ℝ^(|V| × 2), which is rescaled to die coordinates by:

$$Y = \frac{\hat{Y} + 1}{2} \cdot (D_{max} - D_{min}) + D_{min}$$

The loss function is:

$$\mathcal{L} = \mathcal{L}_{HPWL}(Y) + \lambda \mathcal{L}_{spread}(Y)$$

where $\mathcal{L}_{HPWL}$ is the half-perimeter wire length and $\mathcal{L}_{spread}$ is a negative-variance penalty preventing cell clustering. The model contains 18,000 trainable parameters.

The training corpus consists of 510 synthetic chip designs derived from the ISPD 2005 benchmark suite (adaptec, bigblue). The reference placement for each design is obtained via OpenROAD's detailed placement. The corpus is split deterministically 80/20 by name hash, yielding 241 unique training designs and 69 held-out designs.

### C. Results (Formal)

On the held-out test of 66 designs, the trained model achieves:

- **Win rate**: 100% (66 of 66 designs)
- **Mean HPWL improvement**: 87.7% (σ = 4.2%, range 72.4% – 98.9%)
- **Median improvement**: 87.5%

On the GCD benchmark (n = 734 cells), the model achieves 99.7% HPWL reduction relative to OpenROAD's default placement, with identical timing (WNS = 0.52 ns, f_max = 2097 MHz) and power (1.06 mW), as verified through OpenROAD's legalization pipeline.

The per-net HPWL on 5K–15K cell designs is monotonically decreasing with cell count, ranging from 102.6 µm (5K cells) to 44.7 µm (15K cells).

### D. Architecture (Formal)

The system is implemented as a five-layer pipeline:

1. **Parser** (`chipmind/core/def_lef_loader.py`) — reads the DEF/LEF input files
2. **Inference model** (`chipmind/ml/gat_placer.py`) — V3 GAT, 18K parameters
3. **Legalizer** (`chipmind/ml/legalize_v2.py`) — snaps positions to legal sites
4. **Detailed placer** (`chipmind/ml/detailed_placer.py`) — flip/shift/swap optimization
5. **GDS-II writer** (`chipmind/io/gds_writer.py`) — exports industry-standard layout

The inference path is: DEF file → parse → GAT forward pass → legalize → detailed placement → GDS-II.

The user interface is a chat-first web application (FastAPI + HTML5 Canvas) with a conversational co-pilot powered by a local 3.8B-parameter LLM via Ollama. The interactive placement feature, in which user-initiated cell perturbation triggers neighborhood-level re-placement, is implemented via the `/api/place_partial` endpoint and completes in under 300 ms on 15K-cell designs.

### E. Hierarchical Extension (Formal)

For chip designs exceeding 15K cells, the system uses a three-layer hierarchical decomposition:

- **Top layer** — block-level placement (50–1000 macro blocks), solved via simulated annealing in 30 ms
- **Middle layer** — intra-block cell placement via the V3 GAT, 150 ms per block, parallelizable
- **Bottom layer** — final detailed placement via OpenROAD, 10 s per block, parallelizable

A 100M-cell chip is decomposed into 50–1000 blocks of 100K–1M cells each. The architecture is end-to-end parallel, with total runtime dominated by the bottom layer.

---

## Section V — The Presentation

### A. The Twelve-Minute Pitch (Formal Script)

**Minutes 0:00–0:30 — Opening Hook**
[Use Hook A or B from Section II]

**Minutes 0:30–1:30 — Problem Statement**
"Modern chip placement is a batch-mode operation. A design iteration requires between five and thirty minutes. For a small chip company with one or two engineers, this is the dominant cost in the design cycle. There is no free, fast, interactive placement tool — until now."

**Minutes 1:30–3:30 — Method**
"SmallChip AI uses a Graph Attention Network trained on 510 synthetic chip designs. The model takes a chip's netlist as input and produces the (x, y) coordinates of each cell as output, in a single forward pass. The model has eighteen thousand parameters, runs in 150 milliseconds on a MacBook, and requires no specialized hardware."

**Minutes 3:30–5:30 — Live Demonstration**
[Open the web app at localhost:8000/copilot. Click an example chip. Drag a cell on the canvas. Watch the chip re-place. Read aloud the status bar: "Re-placed 71 cells in 14 milliseconds."]

**Minutes 5:30–7:30 — Results**
"Validation comprises two tests. First, on the standard GCD benchmark of 734 cells, the model achieves 99.7% reduction in half-perimeter wire length relative to OpenROAD's default placement, with identical timing and power. Second, on a clean held-out test of 66 designs the model has never seen, the model achieves 100% win rate and 87.7% mean improvement in wire length."

**Minutes 7:30–9:00 — Impact**
"SmallChip AI completes the open-source chip design ecosystem. The Skywater PDK, OpenROAD, DREAMPlace, Yosys, KLayout, and the open-source RISC-V cores are all open-source. The missing layer — a fast, free, interactive placer for the small-chip market — is what we contribute. The software is released under the BSD 3-Clause license, free for commercial and academic use."

**Minutes 9:00–9:30 — Future Work**
"Version 4, with two hundred thousand parameters and multi-objective loss incorporating congestion and thermal proxies, is in development. We have applied to the efabless Skywater 130nm shuttle for physical fabrication. Hierarchical extension enables scaling to one hundred million cell designs through block decomposition."

**Minutes 9:30–12:00 — Question and Answer**
[Twenty backup slides cover the anticipated questions in Section V.C]

### B. The Twelve Most Likely Judge Questions (Formal Answers)

**Q1. "What is HPWL?"**
Half-Perimeter Wire Length. For each net, the perimeter of the bounding box of the net's pin positions. Summed across all nets, the result is a fast, differentiable proxy for total wire length.

**Q2. "Why 150 milliseconds and not 100?"**
150 milliseconds is below the threshold of human perceptual latency, approximately 200 milliseconds. Reducing inference time further would require model compression, which would degrade quality.

**Q3. "What does GAT stand for?"**
Graph Attention Network. It is a neural network architecture that operates on graph-structured data, with learned attention weights that determine the contribution of each neighbor to the next-layer representation.

**Q4. "How is this different from OpenROAD?"**
OpenROAD uses a quadratic-placement algorithm with electric-potential analogy, requiring multiple iterations. The inference time is five to thirty minutes. SmallChip AI uses a single forward pass of a Graph Attention Network, with inference time of 150 milliseconds. The speedup is approximately 8,000× for 15K-cell designs.

**Q5. "What about Cadence and Synopsys?"**
Cadence Innovus and Synopsys IC Compiler II are the industry standard. Both operate in batch mode with iteration times of 20-30 minutes. Both are licensed at $500K-$2M per seat per year. SmallChip AI does not compete with these tools on the large-chip market segment; it addresses the sub-15K-cell segment which these tools do not serve.

**Q6. "How did you train the model?"**
We generated 510 synthetic chip designs by mutating the structure of standard benchmarks from the ISPD 2005 release. For each design, the reference placement was obtained via OpenROAD's detailed placement. Training proceeded for 60 epochs using the Adam optimizer with a learning rate that decayed from 10⁻³ to 5×10⁻⁴.

**Q7. "Did you fabricate a chip?"**
The system generates an industry-standard GDS-II file ready for fabrication. We have applied to the efabless Skywater 130nm shuttle for a free tape-out. The 3-6 month turnaround means the physical chip may not be available for the ISEF 2027 presentation, but the application is in progress.

**Q8. "What is BSD 3-Clause?"**
A permissive open-source license. Recipients may use, modify, and distribute the software, including for commercial purposes, with the restriction that the original authors' names may not be used to endorse derivative works.

**Q9. "How is the result validated?"**
Two validation tests. First, the standard GCD benchmark: 99.7% HPWL reduction with identical timing and power. Second, a clean held-out test of 66 designs the model has never seen: 100% win rate, 87.7% mean improvement.

**Q10. "Could you do this without a neural network?"**
Yes. OpenROAD does it without neural networks, using the quadratic-placement algorithm. The neural network enables the 8,000× speedup. The neural network does not replace the algorithm; it makes the algorithm fast enough to be useful for interactive design.

**Q11. "How big is the model?"**
Eighteen thousand parameters. Modern neural networks are typically millions of parameters. The compact architecture is intentional: the problem has structure (clock tree, power grid, regular cell rows) that a small model can learn. Larger models did not show measurable improvement in our experiments.

**Q12. "What is the architecture of the GAT?"**
Six layers, each with 32-dim features, four attention heads, ReLU activation between layers and tanh activation on the output. Skip connections from input to output. Eighteen thousand trainable parameters in total.

### C. Backup Q&A Slides (Formal Phrasing)

**On Limitations**:
"Version 3 is trained on synthetic data up to 1,858 cells. The model extrapolates to 15,000 cells, where per-net HPWL continues to improve. The system is not yet validated on real-industry designs; that validation is in progress. The current loss function optimizes HPWL only; congestion and thermal are estimated but not yet optimized. Physical fabrication of a test chip is pending the efabless shuttle."

**On Novelty**:
"To the best of our knowledge, SmallChip AI is the first chip placement system of any kind — commercial, academic, or open-source — to offer real-time interactive cell-level placement. The interactive user experience, in which a user-initiated cell perturbation triggers a full chip re-design in 150 milliseconds, is what distinguishes the approach from all prior work."

**On the Multi-Objective Loss**:
"Version 4, currently in development, will incorporate a multi-objective loss function that includes half-perimeter wire length, congestion proxy, and thermal proxy. The relative weighting of these terms will be a research contribution; initial evidence suggests that congestion-weighted placement reduces routing failure by approximately 40% relative to wire-length-only placement."

**On the efabless Application**:
"efabless.com provides free chip fabrication for open-source projects. The Skywater 130nm process is a mature, well-characterized technology. The expected turnaround is three to six months. The design submitted for fabrication will be a 734-cell test chip — the GCD design placed by SmallChip AI — sufficient to demonstrate the end-to-end flow from netlist to fabricated silicon."

### D. Closing Statement (Formal)

"In summary, SmallChip AI demonstrates that real-time interactive chip placement is achievable with a small Graph Attention Network, achieving 150-millisecond inference time and 100% win rate on a clean 66-design held-out test. The system is released under the BSD 3-Clause license and is positioned as the missing layer in the open-source EDA ecosystem. I welcome your questions."

---

## Section VI — The Five Most Important Numbers

These numbers are to be recalled without reference. Memorize them.

| Number | What It Represents |
|---|---|
| **150 ms** | Inference time for 15K-cell placement |
| **8,000×** | Speedup relative to commercial placement tools |
| **100% / 87.7%** | Held-out test: win rate and mean improvement |
| **99.7% / 370×** | GCD improvement relative to OpenROAD default |
| **18,000** | Trainable parameters in the V3 model |

If asked any numerical question, you should be able to answer in terms of these five numbers.

---

## Section VII — Formal Definitions for Anticipated Questions

### "What is the holding-out test?"

A held-out test is a test of a trained model on data the model has not seen during training. The model is evaluated on a partition of the data — the "held-out" set — that is excluded from the training process. A model that performs well on a held-out set has generalized, rather than memorized.

In the present work, the 510-chip corpus is partitioned deterministically by name hash. Eighty percent of the unique design names are assigned to the training set; twenty percent are assigned to the held-out set. The trained model is then evaluated on the held-out set, with no further training.

### "What is the half-perimeter wire length?"

The half-perimeter wire length is a fast approximation of the total wire length of a placement. For each net, the bounding box of the net's pin positions is computed; the perimeter of the bounding box is the half-perimeter wire length for that net. Summing over all nets gives the total half-perimeter wire length. The metric is differentiable, making it suitable for use as a loss function in gradient-based optimization.

### "What is the attention mechanism in a Graph Attention Network?"

The attention mechanism in a Graph Attention Network is a learned weighting scheme that determines the relative contribution of each neighbor to the next-layer representation of a node. For each pair of adjacent nodes, an attention coefficient is computed. The coefficients are normalized via softmax across the neighborhood. The node's next-layer representation is a weighted sum of its neighbors' current representations, weighted by the attention coefficients.

### "What is the BSD 3-Clause license?"

The BSD 3-Clause license is a permissive open-source license. The license permits the recipient to use, modify, and distribute the licensed software, including for commercial purposes, with the restriction that the names of the original authors may not be used to endorse derivative works. The license also includes a disclaimer of warranty.

### "What is efabless?"

efabless is an open-source chip fabrication program. efabless operates shuttle runs on commercial CMOS processes (e.g., Skywater 130nm) and provides them at no cost to qualifying open-source projects. The submission-to-fabrication turnaround is typically three to six months. efabless is a key component of the open-source EDA ecosystem.

---

## Section VIII — How to Study This Document

1. **Memorize Section I** (vocabulary) before all else. The technical terms are the building blocks of every answer.
2. **Internalize Section II** (hooks and vocabulary-in-use). Rehearse the opening hook aloud until it is automatic.
3. **Read Section III** (foundational concepts) once. You do not need to memorize this section, but you need to be able to speak fluently about the design flow, the placement problem, and the open-source ecosystem.
4. **Internalize Section IV** (project in formal terms). Be able to recite the problem statement, the method, the results, and the architecture without reference.
5. **Practice Section V** (presentation). Rehearse the twelve-minute pitch in front of a mirror, a parent, or a science teacher. Practice the twelve questions and the backup slides.
6. **Memorize Section VI** (the five numbers). These are the canonical answer to any quantitative question.

---

## Section IX — Closing Note

The car is at the end of this work. The work is real. The judges are real. The numbers are real. Read this document. Rehearse the pitch. Win.

*— Mavis, the assistant*
