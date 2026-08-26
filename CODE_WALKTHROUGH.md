# Code Walkthrough Tutorial

> **Read this alongside the actual code. You'll learn every important file.**

---

## The 5-minute tour: what to read first

If you have 5 minutes, read these in order:
1. `chipmind/ml/gat_placer.py` — the GAT model
2. `chipmind/core/def_parser.py` — parses a chip design
3. `chipmind/core/hpwl.py` — computes HPWL
4. `chipmind/ml/detailed_placer.py` — makes placement legal
5. `chipmind/api/server.py` — exposes it as a web API

If you have 30 minutes, also read:
6. `chipmind/algorithms/sa.py` — the SA baseline
7. `chipmind/algorithms/eplace.py` — the ePlace baseline
8. `chipmind/llm_copilot.py` — the LLM co-pilot
9. `web/app.js` — the web frontend
10. `desktop_app.py` — the .app wrapper

If you have 2 hours, read everything.

---

## Walkthrough 1: parsing a chip (def_parser.py)

When a user uploads a `.def` file, we need to convert it to a Python dict. The `parse_def` function does this.

```python
# chipmind/core/def_parser.py (simplified)
def parse_def(path: str) -> dict:
    """Parse a DEF file and return a chip dict."""
    chip = {"die": None, "components": {}, "nets": []}
    in_nets = False
    in_components = False

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("DIEAREA"):
                # Parse die area: e.g., ( 0 0 ) ( 1000 1000 )
                # Set chip["die"] = {"x1": 0, "y1": 0, "x2": 1000, "y2": 1000}
                ...
            elif line.startswith("COMPONENT"):
                in_components = True
            elif line.startswith("END COMPONENT"):
                in_components = False
            elif in_components and line.startswith("-"):
                # Parse component: - cellname refname + PLACED ( x y ) ...
                # Add to chip["components"]
                ...
            elif line.startswith("NET"):
                in_nets = True
                # Parse net name, then list of (cellname, pinname) pairs
                # Add to chip["nets"]
                ...

    return chip
```

**What to learn from this:**
- DEF is a text-based format. Each line is parsed sequentially.
- Three main sections: DIEAREA (the die bounds), COMPONENTS (the cells), NETS (the connections).
- The output is a Python dict with three keys: `die`, `components`, `nets`.

**Try it:**
```python
from chipmind.core import parse_def
chip = parse_def("web/examples/gcd_734cells.def")
print(f"Die: {chip['die']}")
print(f"Cells: {len(chip['components'])}")
print(f"Nets: {len(chip['nets'])}")
```

---

## Walkthrough 2: computing HPWL (hpwl.py)

The HPWL is the total half-perimeter wire length. For each net, find the bounding box of its cells, sum the dimensions.

```python
# chipmind/core/hpwl.py (simplified)
def compute_hpwl(chip: dict) -> dict:
    """Compute HPWL of a chip. Returns dict with 'total_hpwl' and per-net."""
    components = chip["components"]
    nets = chip["nets"]
    die = chip["die"]

    total = 0
    per_net = []

    for net in nets:
        cell_names = net["components"]  # list of cell names
        if len(cell_names) < 2:
            continue

        # Get positions
        xs = [components[c]["x"] for c in cell_names if c in components]
        ys = [components[c]["y"] for c in cell_names if c in components]

        if not xs or not ys:
            continue

        # Bounding box
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)

        # HPWL = width + height (half of the perimeter)
        net_hpwl = width + height
        total += net_hpwl
        per_net.append(net_hpwl)

    return {
        "total_hpwl": total,
        "per_net_hpwl": per_net,
        "average_per_net": total / len(per_net) if per_net else 0,
    }
```

**What to learn:**
- O(M) where M is the number of nets. Each net is processed once.
- For 15K nets, this takes ~10ms in Python.
- The "average per net" metric is what we use to compare designs of different sizes (e.g., 33.2 µm at 15K vs 46 µm at GCD).

**Try it:**
```python
from chipmind.core import parse_def, compute_hpwl
chip = parse_def("web/examples/gcd_734cells.def")
# Place cells at random
import random
for c in chip["components"]:
    chip["components"][c]["x"] = random.uniform(0, 1000)
    chip["components"][c]["y"] = random.uniform(0, 1000)
result = compute_hpwl(chip)
print(f"Random HPWL: {result['total_hpwl']:,.0f}")
# Should be ~22 million (matches paper's "Random" baseline)
```

---

## Walkthrough 3: the GAT model (gat_placer.py)

This is the brain of SmallChip AI. 3 GAT layers, 64 hidden units, 4 attention heads, 18,178 parameters.

```python
# chipmind/ml/gat_placer.py (simplified)
import torch
import torch.nn as nn
from torch_geometric.nn import GATConv

class GATPlacerV3(nn.Module):
    def __init__(self, in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4):
        super().__init__()
        self.input_proj = nn.Linear(in_dim, hidden)
        self.gat_layers = nn.ModuleList()
        for i in range(num_layers):
            self.gat_layers.append(
                GATConv(hidden, hidden // heads, heads=heads)
            )
        self.norm = nn.LayerNorm(hidden)
        self.output = nn.Linear(hidden, out_dim)
        self.activation = nn.Tanh()  # output in [-1, 1]

    def forward(self, x, edge_index):
        # x: (N, 9) — per-cell features
        # edge_index: (2, E) — graph edges
        h = self.input_proj(x)
        for gat in self.gat_layers:
            h_new = gat(h, edge_index)
            h = self.norm(h + h_new)  # residual + layernorm
        out = self.output(h)  # (N, 2) — (x, y) in [-1, 1]
        return self.activation(out)
```

**What to learn:**
- `GATConv` is from PyTorch Geometric. It implements the attention mechanism.
- The input is per-cell features (9-dim). The output is per-cell (x, y) in [-1, 1].
- Residual connections (`h + h_new`) help with deep networks.
- Layer normalization stabilizes training.
- Tanh output (not Sigmoid) avoids saturation.

**The predict function:**
```python
def predict(model, chip):
    """Run the GAT on a chip. Returns {cell_name: (x, y)}."""
    # Convert chip dict to graph (x, edge_index)
    ...
    # Run model
    raw_output = model(x, edge_index)  # (N, 2) in [-1, 1]
    # Shift/scale to die dimensions
    x_norm = (raw_output[:, 0] + 1) / 2  # [0, 1]
    y_norm = (raw_output[:, 1] + 1) / 2
    x = x_norm * (die["x2"] - die["x1"]) + die["x1"]
    y = y_norm * (die["y2"] - die["y1"]) + die["y1"]
    return {name: {"x": x[i], "y": y[i]} for i, name in enumerate(cell_names)}
```

---

## Walkthrough 4: the detailed placer (detailed_placer.py)

The detailed placer makes a raw placement legal. It does 5 things in a loop:

```python
# chipmind/ml/detailed_placer.py (simplified)
def detailed_placement(components, nets, die, cell_w_um, cell_h_um=1.4,
                       n_iterations=3, verbose=False):
    """Make a placement legal. Returns updated components dict."""

    # Step 1: Row assignment
    # Group cells by y-coordinate into horizontal rows
    rows = assign_to_rows(components, die, cell_h_um)

    # Step 2: Initial legalization
    # Snap each cell to the nearest available site in its row
    components = initial_legal(components, rows, cell_w_um)

    # Step 3-5: Iterate: flip, shift, reorder
    for iteration in range(n_iterations):
        improved = False
        for net in nets:
            if try_flip(components, net, cell_w_um, cell_h_um):
                improved = True
            if try_shift(components, net, cell_w_um, cell_h_um):
                improved = True
            if try_swap(components, net, cell_w_um, cell_h_um):
                improved = True
        if not improved:
            break

    return components
```

**What to learn:**
- `assign_to_rows`: divide the die into horizontal rows of cell_h_um height.
- `initial_legal`: snap each cell to the nearest available site.
- `try_flip`: mirror a cell vertically. Sometimes flipping reduces wire length.
- `try_shift`: move a cell 1 site left/right. Sometimes shifting reduces wire length.
- `try_swap`: swap two adjacent cells in the same row. Sometimes reordering reduces wire length.
- The loop runs until no improvement.

---

## Walkthrough 5: the web server (server.py)

The FastAPI server exposes SmallChip AI as a REST API.

```python
# chipmind/api/server.py (simplified)
from fastapi import FastAPI, UploadFile
from chipmind.core import parse_def, compute_hpwl
from chipmind.ml.gat_placer import GATPlacerV3, predict

app = FastAPI()

# Load pre-trained model once at startup
model = GATPlacerV3()
state = torch.load("chipmind/results/gat_v3_model_best.pt", map_location="cpu")
model.load_state_dict(state)
model.eval()

@app.post("/api/place")
async def place(file: UploadFile):
    """Place a chip uploaded as a DEF file."""
    # Save uploaded file
    with open("/tmp/upload.def", "wb") as f:
        f.write(await file.read())

    # Parse + place
    chip = parse_def("/tmp/upload.def")
    components = predict(model, chip)
    placed = {**chip, "components": components}

    # Compute HPWL
    result = compute_hpwl(placed)

    return {
        "hpwl": result["total_hpwl"],
        "per_net": result["average_per_net"],
        "components": components,  # raw (x, y) positions
    }

@app.post("/api/compare")
async def compare(file: UploadFile):
    """Compare 12 algorithms on the uploaded chip."""
    # Run SA, ePlace, GAT, etc.
    # Return table of HPWLs
    ...
```

**What to learn:**
- FastAPI uses `@app.post()` decorators to define endpoints.
- The model is loaded once at startup (don't reload per request).
- `/api/place` does the basic placement. `/api/compare` runs all 12 algorithms.
- The frontend (`web/app.js`) calls these endpoints via `fetch()`.

---

## Walkthrough 6: the web frontend (app.js)

The web app is vanilla JavaScript. It calls the FastAPI endpoints and displays results.

```javascript
// web/app.js (simplified)
async function loadExample(filename) {
    const response = await fetch(`/static/examples/${filename}`);
    const blob = await response.blob();
    const file = new File([blob], filename, { type: 'text/plain' });
    setFile(file);
}

async function runComparison() {
    const formData = new FormData();
    formData.append('file', currentFile);

    const response = await fetch('/api/compare', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();

    // Display results in a table
    displayResults(data);
}
```

**What to learn:**
- `fetch()` is the modern way to make HTTP requests from JavaScript.
- `FormData` is used to upload files via POST.
- The example buttons (`/static/examples/gcd_734cells.def`) are served by the static file mount.
- The `loadExample` function turns a static URL into a `File` object that can be uploaded.

---

## Walkthrough 7: the LLM co-pilot (llm_copilot.py)

The LLM co-pilot takes a natural-language request and returns a tailored report.

```python
# chipmind/llm_copilot.py (simplified)
def parse_request(prompt: str) -> list:
    """Parse a natural-language design goal into a 5-dim preference vector."""
    prompt_lower = prompt.lower()

    # Keyword-based heuristic
    if "power" in prompt_lower or "energy" in prompt_lower:
        return [0.18, 0.47, 0.12, 0.12, 0.12]  # emphasize power
    if "fast" in prompt_lower or "speed" in prompt_lower:
        return [0.10, 0.10, 0.10, 0.50, 0.20]  # emphasize timing
    if "compact" in prompt_lower or "small" in prompt_lower:
        return [0.10, 0.10, 0.50, 0.20, 0.10]  # emphasize area
    # Default: balanced
    return [0.20, 0.20, 0.20, 0.20, 0.20]

def generate_report(chip, placement, metrics, preferences) -> str:
    """Generate a human-readable report tailored to the user's preferences."""
    # The chip is unchanged. The report is tailored.
    focus_metric = preferences.index(max(preferences))
    metric_names = ["HPWL", "power", "area", "timing", "congestion"]

    return f"""Placed {len(chip['components'])} cells with HPWL {metrics['total_hpwl']:,}.
The placement emphasizes {metric_names[focus_metric]} based on your request.
[... tailored explanation paragraph based on focus_metric ...]"""
```

**What to learn:**
- The LLM doesn't change the placement. It only changes the report.
- The keyword heuristic catches the most common phrasings. For more nuanced requests, an LLM (Ollama or OpenAI) is used.
- The 5-dim preference vector is the *emphasis* of the report, not weights for the placer.

---

## What to study in order

If you're learning the code from scratch:

**Day 1**: def_parser.py + hpwl.py
- 200 lines total
- Pure Python, no ML
- You'll understand: how chips are represented, how quality is measured

**Day 2**: gat_placer.py
- 100 lines
- The GAT model
- You'll understand: how the AI works

**Day 3**: detailed_placer.py
- 300 lines
- The detailed placer
- You'll understand: how raw placement becomes legal

**Day 4**: server.py + app.js
- 500 lines (server) + 1000 lines (app.js)
- The web interface
- You'll understand: how the parts connect

**Day 5**: llm_copilot.py
- 100 lines
- The LLM co-pilot
- You'll understand: how the user-facing magic works

**Day 6-7**: the algorithms/ directory (SA, ePlace, PPO, etc.)
- 100-300 lines each
- 11 baseline algorithms
- You'll understand: how the plateau forms, why GAT is different

**Day 8-9**: the training scripts (train_gat_placer_v3.py)
- 300 lines
- The training loop
- You'll understand: how the GAT learns

**Day 10**: README, INSTALL.md, the .app
- 100 lines total
- The packaging
- You'll understand: how to ship it

After 10 days, you'll know the code cold. You'll be able to walk through any file with a judge.
