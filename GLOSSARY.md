# SmallChip AI — Glossary

> **Every technical term in the project, defined for a 9th grader.**
> Read this once. Refer back when you hit an unknown word.

---

## A

**Adam optimizer** — A gradient-based optimizer that adapts the learning rate per parameter. Used in V3 training.

**Algorithm comparison** — A table or chart comparing multiple placement algorithms on the same benchmark. Our §4.5 compares 12 algorithms on the GCD.

**Attention mechanism** — A learned weighting that decides which other elements in a sequence or graph are most relevant to the current one. The core idea of the Transformer and GAT architectures.

**Augmented Reality (AR)** — Not used in this project. (Just making sure the glossary is alphabetized.)

---

## B

**Backend** — The server side of an application. For us, FastAPI serving placement endpoints.

**Baseline** — A simple algorithm used as a reference point for comparison. OpenROAD default is our baseline.

**Bay Area** — California. Not relevant to this project. (Strongsville, OH is the right side of the country.)

**Bookshelf format** — The file format used by the ISPD 2005 contest suite. Files include `.aux`, `.nodes`, `.nets`, `.pl`, `.scl`.

**BSD license** — A permissive open-source license. Anyone can use, modify, and redistribute BSD-licensed code, including for commercial use. SmallChip AI is BSD.

**Buffer** — A cell type that drives signals but doesn't perform logic. Used to strengthen signals over long wires.

---

## C

**Cadence Innovus** — A commercial chip placement + routing tool. $1M+/year per license. Industry standard.

**Cell** — A logical unit on a chip (AND gate, OR gate, flip-flop, buffer, etc.). The basic building block.

**Cell library** — A predefined set of cells with known sizes and behaviors. We use the FreePDK45 45nm library.

**Cell width** — The horizontal size of a cell, in micrometers (µm). The detailed placer uses cell width to snap cells to sites. We swept 0.5, 1.0, 1.5, 2.0, 3.0 µm in the polish.

**Cell flipping** — Mirroring a cell vertically. Real detailed placers do this to reduce wirelength.

**Chip** — Short for "integrated circuit" or "microchip". A square of silicon with transistors and wires.

**Chip placement** — The problem of assigning (x, y) positions to cells on a chip die.

**ChipPlacer** — The folder name of the project: `/Users/harshith/Documents/ChipPlacer/`.

**clock tree synthesis (CTS)** — Building the clock distribution network. The clock signal must reach every flip-flop at the same time.

**Co-pilot** — The LLM-based chat interface in our .app. Translates natural language to design preferences.

**Combinatorial optimization** — A class of optimization problems where you search a finite (but huge) set of candidates. Chip placement is combinatorial.

**Connected subset** — A sub-graph of a chip netlist that is still a valid netlist (every cell has at least one net, every net has at least 2 cells).

**Cost function** — A mathematical expression of "how good is this placement". Lower is better.

**CPU** — Central Processing Unit. A regular laptop CPU. Not a GPU. SmallChip AI runs on a single CPU core.

---

## D

**DARPA** — US Defense Advanced Research Projects Agency. Funded the development of OpenROAD.

**DEF (Design Exchange Format)** — A file format for chip layouts. Contains cell names, positions, and net connections.

**Detailed placer** — A placer that produces a legal placement (cells on rows, snapped to sites, no overlap). Our `chipmind/ml/detailed_placer.py`.

**Density penalty** — In gradient-based placement, a term in the cost function that penalizes cell overlap. Becomes "stiff" at high cell density, causing RePlAce to diverge.

**Desktop app** — A standalone application that runs on a regular computer. We have a macOS .app built with PyInstaller + pywebview.

**Diffusion model** — Not used. (Just making sure the glossary is alphabetized.)

**Divergence** — When a numerical algorithm fails because values blow up to infinity or NaN. OpenROAD's RePlAce diverges on 5K+ cell designs.

**Docker** — A containerization tool. We initially tried Docker for OpenROAD but it wasn't available. We use local Python instead.

---

## E

**EDA (Electronic Design Automation)** — Software tools for designing chips. The market is dominated by Cadence and Synopsys.

**Edge** — In a graph, a connection between two nodes. In a chip netlist, an edge between two cells means they share a net.

**Embedding** — A vector representation of something. In our GAT, each cell is represented by a 64-dim vector.

**Endpoint** — A URL on a server. `/api/place` is the endpoint for placing a chip.

**Epoch** — One pass through the entire training dataset. We train V3 for 60-80 epochs.

---

## F

**FastAPI** — A Python web framework. We use it for the placement server.

**Feasible region** — In optimization, the set of valid solutions. For placement, cells must be on rows, no overlap, etc.

**Flip-flop** — A 1-bit memory cell in a chip. Stores a single bit.

**Forward pass** — In a neural network, computing the output from the input. Our V3 GAT does a single forward pass per design.

**FreePDK45** — A 45nm standard cell library from Oklahoma State University. We use it for the GCD benchmark.

---

## G

**GAT (Graph Attention Network)** — A graph neural network with attention. We use 3 GAT layers × 64 hidden × 4 attention heads = 18,178 parameters.

**GCD (Greatest Common Divisor)** — A standard test chip design from the OpenROAD project. 692 cells, 463 nets, 45nm.

**GNN (Graph Neural Network)** — A neural network that operates on graphs.

**GPL-0305** — The OpenROAD error code for "RePlAce diverged during gradient descent". Cost function blew up to infinity.

**GPU (Graphics Processing Unit)** — Specialized hardware for parallel computation. Google's chip-placement work uses GPUs for 8-48 hours. SmallChip AI uses a regular CPU.

**Gradient descent** — An optimization algorithm that follows the negative gradient of a cost function. RePlAce uses gradient descent.

**Graph** — A set of nodes connected by edges. A chip netlist is a graph.

---

## H

**Heuristic** — A practical method that's not guaranteed to be optimal but works well enough. Simulated annealing is a heuristic.

**Hidden units** — The width of a neural network layer. We use 64 hidden units per attention head.

**HPWL (Half-Perimeter Wire Length)** — Sum of bounding-box half-perimeters across all nets. The standard metric for placement quality. Lower is better.

**Hyperparameter** — A configuration value that's not learned. Examples: cell width, number of attention heads, loss weights.

---

## I

**Inference** — Running a trained model on new data. Our V3 GAT inference takes 17 seconds for 15K cells.

**ISPD 2005** — A chip design contest suite. 8 industrial designs, used for benchmarking.

**ISEF (Intel International Science and Engineering Fair)** — The world's largest pre-college science competition. Our target.

**Iterative** — Repeating. Our detailed placer iterates flip → shift → reorder until no improvement.

---

## J

**JSON** — JavaScript Object Notation. A data format. We use it for the .app's API and for training data.

---

## K

**Kernighan-Lin** — A graph partitioning algorithm. We use it for hierarchical placement.

---

## L

**Lateral thinking** — Solving problems through indirect, creative approaches. Not a CS term but useful for ISEF.

**Layer normalization** — A normalization technique for neural networks. We use it in V3.

**Layout** — The physical arrangement of cells on a chip die.

**Learning rate** — A hyperparameter for training neural networks. How big a step to take in the gradient direction.

**LEF (Library Exchange Format)** — A file format for cell library definitions. We added LEF parsing in v0.2.0.

**Legal placement** — A placement where every cell is on a row, snapped to a site, no overlap. Required for manufacturing.

**License** — Permission to use. BSD = permissive. MIT = permissive. GPL = copyleft.

**LLM (Large Language Model)** — A neural network trained on text. We use Ollama (local) or OpenAI API for the co-pilot.

**Local minimum** — A point in the optimization landscape where any small step makes things worse, but the global minimum is somewhere else. Classical placers get stuck here.

**Local search** — An optimization algorithm that explores neighboring solutions. SA, GA, Memetic are all local search.

---

## M

**M3** — A neural network architecture. (Also a Mac chip. We use it for AI.)

**MacOS** — Apple's desktop OS. Our .app is built for macOS.

**Mean Squared Error (MSE)** — Sum of squared differences between predicted and target values. Used in V3 loss.

**Memetic algorithm** — A hybrid of genetic algorithm and local search.

**Microarchitecture** — The specific design of a chip's cells and their connections. The input to placement.

**Mode collapse** — A failure mode where a generative model produces the same output regardless of input. For V3, all cells collapse to one point. Spread penalty prevents this.

**Multi-objective** — Optimizing for multiple goals simultaneously. Our 5-metric predictor predicts HPWL, timing, power, area, congestion in one inference.

---

## N

**Net** — A group of cells that should be electrically connected. The "wires" in a chip.

**Netlist** — A list of cells and nets. The input to placement.

**NEOSEF** — North East Ohio Science and Engineering Fair. Our regional fair.

**Neuron** — A single unit in a neural network.

**Node** — In a graph, a single element. In a chip netlist, a cell.

**Novel** — New. ISEF judges value novelty.

**Numerical instability** — When small changes in input cause large changes in output. RePlAce suffers from this on dense designs.

---

## O

**OpenROAD** — The leading open-source EDA toolchain. Free, BSD-licensed, used in academic chip design.

**Open source** — Code that's publicly available and free to use, modify, redistribute. SmallChip AI is open source.

**Optimization** — Finding the best solution from a set of alternatives.

**Outlier** — A data point that's significantly different from the rest. In chip design, an outlier placement has very different properties from typical.

---

## P

**Patent** — Not used. SmallChip AI is BSD-licensed, not patented. Anyone can use it freely.

**Per-design RL** — Training a separate RL agent for each new chip. Google's approach. 8-48 hours of GPU per chip.

**Per-net HPWL** — Total HPWL divided by number of nets. A normalized metric. Our 15K result: 33.2 µm per net.

**PhD-level** — Graduate-level research. ISEF judges will say our project is PhD-level.

**Placement** — The (x, y) positions of cells on a chip die. The output of a placer.

**Plateau** — A flat region in an optimization landscape. 12 classical methods all get stuck at 1.3M HPWL on GCD — the plateau.

**Placer** — An algorithm that takes a netlist and outputs a placement.

**Polish** — Improvement. We "polish" a placement by running the detailed placer.

**Post-routing** — After the router has run. We don't have post-routing power on 15K (OpenROAD can't place 15K to start).

**Power analysis** — Estimating how much power a chip consumes. OpenROAD's static power analyzer says 1.06 mW for both V3-placed and default-placed GCD.

**Pre-training** — Training a model once on a large corpus, then using it for many tasks. Our GAT is pre-trained on 510 chips.

**Pareto** — When you can't improve one metric without worsening another. We avoid Pareto by always using the best possible placement.

**PyTorch** — A Python deep learning library. We use it for the GAT.

**PyTorch Geometric** — A PyTorch library for graph neural networks. We use it for the GAT.

**PyInstaller** — A tool for packaging Python apps as standalone executables. We use it for the .app.

**pywebview** — A Python library for creating native desktop windows. We use it for the .app.

---

## Q

**Quality metrics** — HPWL, timing, power, area, congestion. We predict all 5 in one inference.

---

## R

**ReLU** — A neural network activation function. We use LeakyReLU in the GAT attention.

**RePlAce** — OpenROAD's gradient-based global placer. Diverges on 5K+ cells.

**ResNet-style** — Using residual connections. We use them in V3.

**Routability** — How easily a design can be routed (wires connected). Lower HPWL usually means better routability.

**Routing** — The process of connecting cells with physical wires. Comes after placement.

---

## S

**Saturation** — When a neural network's output stops responding to input. Tanh output (used in V3) avoids saturation.

**Scaling** — How a method performs as the design size increases. Our V3 scales from 100 to 15,000 cells.

**Sensitivity** — How much output changes with input. The V3 GAT is robust to variations in input features.

**Simulated Annealing (SA)** — A local search algorithm inspired by metallurgy. We use it as a baseline.

**Sparsity** — Most entries in a matrix are zero. Graph data is sparse.

**Spread penalty** — A term in V3's loss function that penalizes mode collapse. Cells must spread across [0, 1]².

**Standard cell** — A pre-designed cell from a cell library. All cells in our GCD are standard cells.

**Static Timing Analysis (STA)** — Computing the timing of a chip without simulating. OpenROAD has an STA tool.

**Strongsville** — A city in Ohio. Where Harshith goes to high school.

**Synopsys ICC** — A commercial chip placement + routing tool. $1M+/year per license. Industry standard.

---

## T

**Tanh** — A neural network activation function with output in [-1, 1]. We use it in V3 (output is in [0, 1] after scaling).

**Test set** — A held-out set of designs not used in training. We test on 91 ISPD 2005 connected subsets separate from training.

**Throughput** — How many operations per second. Our V3 does 15K cells in 17 seconds.

**Topology** — The shape of a network. Our chip netlist is a graph topology.

**Training** — Adjusting model weights to minimize loss on training data. V3 trains for 60-80 epochs.

**Transform** — In math, a function that maps one set to another. The GAT is a transform from netlist to placement.

**TSMC** — Taiwan Semiconductor Manufacturing Company. The world's largest chip foundry. Not directly related to SmallChip AI.

---

## U

**Unit test** — A small test that checks one specific function. We have tests in `tests/`.

**Uvicorn** — A Python ASGI server. We use it to run the FastAPI backend.

---

## V

**V3 GAT** — Our pre-trained 3-layer Graph Attention Network. 18,178 parameters. 99.7% / 370× better than OpenROAD on GCD.

**Validation** — Checking that the model works on new data. We validate with OpenROAD's own STA + power analysis.

**Vanilla** — Plain, without additions. Vanilla SA is plain simulated annealing.

**Vapnik-Chervonenkis** — Not used. (Just making sure the glossary is alphabetized.)

**Vertex** — Singular of "vertices". In a graph, a vertex is a node.

**V3** — The third version of our GAT. The first to use HPWL-aware loss + spread penalty. 99.7% / 370× better on GCD.

---

## W

**Web app** — An application that runs in a web browser. We have a web app at `localhost:8000`.

**Weight** — In a neural network, a parameter that's learned during training. V3 has 18,178 weights.

**Wirelength** — The total length of all wires on a chip. HPWL is a proxy for wirelength.

**Wizard** — Not used. (Just making sure the glossary is alphabetized.)

---

## X

**XOR** — A logic gate. The GCD chip has XOR gates.

---

## Y

**Yield** — The percentage of manufactured chips that work. Not directly related to placement.

**Y-axis** — The vertical direction. We use (x, y) coordinates.

---

## Z

**Z4 G29** — The BMW Z4 G29, a 2-door roadster. Harshith's prize-money target. ~$35K used.
