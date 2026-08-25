# SmallChip AI — Desktop App

A native desktop app for SmallChip AI (chip placement co-pilot for small-to-medium chips).

## Run from source

```bash
pip install -r requirements-desktop.txt
python desktop_app.py
```

This will:
1. Check if the FastAPI backend is already running on port 8000
2. If not, start it automatically
3. Open a native window pointing at `http://localhost:8000`

## Build a standalone .app (macOS)

```bash
pip install py2app
python setup.py py2app
# Output: dist/SmallChip AI.app
# Drag to /Applications to install
```

## First-run experience

The window opens to the SmallChip AI landing page. You can:
- Upload a `.def` chip file
- See the placement result with raw vs legal HPWL
- Talk to the AI co-pilot in plain English
- Run the Full Analysis to see congestion/thermal heatmaps

## Requirements

- macOS 11+ (Big Sur or later)
- Python 3.10+ (for source build)
- The full SmallChip AI pip install (chipmind, torch, torch-geometric, fastapi, uvicorn)

## Architecture

```
[SmallChip AI window]  ←  pywebview (native webview)
        ↓
[http://localhost:8000]  ←  FastAPI backend
        ↓
[V3 GAT placer]  ←  [Smart legalizer]  ←  [Quality estimators]
```

The desktop app is a thin shell around the existing web app — no code duplication, no separate UI to maintain.
