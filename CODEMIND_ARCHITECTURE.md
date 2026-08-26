# chipmind — Code Architecture

> **For technical judges and code reviewers. Explains the structure of the Python package.**

---

## Overview

`chipmind` is a Python package for AI-powered chip placement. The package is BSD-licensed, ~5,000 lines of code, depends on PyTorch + PyTorch Geometric, and ships with a FastAPI server, a web frontend, and a desktop .app.

```
chipmind/
├── api/              # FastAPI backend
│   ├── server.py     # Main server, ~500 lines
│   └── ...
├── core/             # Core algorithms
│   ├── def_parser.py # DEF file parser
│   ├── lef_parser.py # LEF file parser (new in v0.2.0)
│   ├── def_lef_loader.py # Combined DEF+LEF loader
│   ├── hpwl.py       # HPWL calculator
│   └── ...
├── ml/               # ML models
│   ├── gat_placer.py # GAT model definition
│   ├── detailed_placer.py # Real detailed placer
│   ├── multiobj.py   # 5-metric predictors
│   └── ...
├── algorithms/       # Baseline algorithms
│   ├── sa.py         # Simulated annealing
│   ├── ppo.py        # PPO RL
│   ├── eplace.py     # Analytical ePlace
│   ├── ga.py         # Genetic algorithm
│   ├── memetic.py    # Memetic algorithm
│   ├── wiremask_ea.py # WireMask evolutionary
│   └── ...
└── llm_copilot.py    # LLM integration
```

## Entry points

### 1. Web app (most common)
```bash
python -m uvicorn chipmind.api.server:app --host 0.0.0.0 --port 8000
```
- Loads chipmind package
- Starts FastAPI server
- Serves the web frontend from `../web/`
- Provides REST API for placement, comparison, and LLM co-pilot

### 2. Direct Python use
```python
import torch
from chipmind.core import parse_def, compute_hpwl
from chipmind.ml.gat_placer import GATPlacerV3, predict

# Load pre-trained model
m = GATPlacerV3(in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4)
state = torch.load("chipmind/results/gat_v3_model_best.pt", map_location="cpu")
m.load_state_dict(state)
m.eval()

# Parse a chip
chip = parse_def("path/to/design.def")

# Place it
components = predict(m, chip)

# Report HPWL
placed = {**chip, "components": components}
print(f"HPWL: {compute_hpwl(placed)['total_hpwl']:,}")
```

### 3. Desktop .app
```bash
python desktop_app.py
```
- Wraps the web app in a pywebview window
- Auto-starts the FastAPI backend
- Bundled with PyInstaller for distribution

## Core abstractions

### The `chip` dict
A chip is represented as a Python dict:
```python
chip = {
    "die": {"x1": 0, "y1": 0, "x2": 1000, "y2": 1000},  # die bounds in DBU
    "components": {
        "cell_0": {"x": 100, "y": 200, "width": 5, "height": 7, "is_terminal": False},
        ...
    },
    "nets": [
        {"name": "net_0", "components": ["cell_0", "cell_1", "cell_2"]},
        ...
    ]
}
```

This is the canonical format. Every algorithm reads and writes this format.

### The GAT model
```python
class GATPlacerV3(nn.Module):
    def __init__(self, in_dim=9, hidden=64, out_dim=2, num_layers=3, heads=4):
        # 3 GAT layers, 64 hidden, 4 attention heads
        # Residual + LayerNorm
        # 18,178 parameters total

    def forward(self, x, edge_index):
        # x: (N, 9) — per-cell features
        # edge_index: (2, E) — netlist graph
        # returns: (N, 2) — predicted (x, y) positions in [0, 1]
```

### The detailed placer
```python
def detailed_placement(components, nets, die, cell_w_um, cell_h_um=1.4,
                       n_iterations=3, verbose=False):
    """Real detailed placer: row assignment → legalization → cell flipping
    → cell shifting → local reordering → iterate."""
```

This is what brings the V3 raw placement (e.g., 6,020,661 DBU on 15K) down to legal HPWL (e.g., 436,961 DBU on 15K at cell_w=2.0µm).

### The LLM co-pilot
```python
def parse_request(prompt: str) -> list[float]:
    """Parse a natural-language design goal into a 5-dim preference vector
    [hpwl, power, area, timing, congestion]. Uses LLM if available,
    else falls back to keyword heuristic."""

def generate_report(placement, metrics, preferences) -> str:
    """Generate a human-readable report tailored to the user's preferences.
    The chip is unchanged; only the explanation is tailored."""
```

## Why this design

**Why a dict instead of a class?** Easy to serialize, easy to pass to algorithms, easy to JSON-encode for the web API. No magic.

**Why FastAPI?** Async, type-hinted, automatic OpenAPI docs, fast. Standard Python web framework.

**Why pywebview for the .app?** Native window without Chromium, smallest bundle size, no Electron.

**Why BSD?** Anyone can use it commercially. Including chip companies. We want adoption.

**Why no Docker for the dev environment?** Direct Python is faster for development, simpler for users. Docker is overkill for a single-binary .app.

## Algorithm comparison

`chipmind/algorithms/` contains 11 baseline algorithms. Each takes the same `chip` dict and returns a placed `chip` dict. This makes A/B comparison trivial:

```python
from chipmind.algorithms.sa import simulated_annealing
from chipmind.algorithms.eplace import eplace
from chipmind.ml.gat_placer import predict
from chipmind.core import parse_def, compute_hpwl

chip = parse_def("design.def")
results = {
    "SA": compute_hpwl(simulated_annealing(chip, T=50000, n_iter=10000))["total_hpwl"],
    "ePlace": compute_hpwl(eplace(chip, n_iter=2500))["total_hpwl"],
    "GAT (ours)": compute_hpwl({**chip, "components": predict(m, chip)})["total_hpwl"],
}
print(results)
```

## Training pipeline

```bash
# Generate training data from ISPD 2005 Bookshelf files
python scripts/generate_ispd_training_data.py

# Train V3 GAT (10 hours on CPU for 60 epochs)
python scripts/train_gat_placer_v3.py \
    --data results/training_data/ispd_training_data.json \
    --epochs 60 \
    --save-dir results/

# Evaluate on GCD
python scripts/evaluate_gcd.py
```

## Performance

| Operation | Time | Hardware |
|---|---|---|
| V3 inference (15K cells) | 17 sec | 1 CPU core |
| Detailed placement (15K cells) | 4 min | 1 CPU core |
| Full comparison (12 algorithms on GCD) | 30 sec | 1 CPU core |
| V3 training (60 epochs, 510 chips) | 10 hours | 1 CPU core |
| LLM co-pilot response | 2-5 sec | Ollama local LLM (or OpenAI API) |

## Testing

- `tests/` — unit tests for core algorithms
- `notebooks/` — Jupyter notebooks for interactive exploration
- `scripts/evaluate_*.py` — benchmark scripts that produce JSON results

## Dependencies

```
torch >= 2.0
torch-geometric >= 2.4
fastapi
uvicorn
pywebview (for .app)
pyinstaller (for .app build)
numpy
scipy
matplotlib (for visualizations)
ollama (for LLM, optional)
```

All BSD or MIT licensed. No proprietary dependencies.
