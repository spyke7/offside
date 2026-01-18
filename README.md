# OffSide

A Python-based football match simulation platform.

## Overview
OffSide simulates football matches using configurable engines and renders them with a visual UI. It includes modules for synthetic match generation, ML simulation, and rendering.

## Project Structure
- `src/` – Core source code (engines, renderer, data loaders).
- `data/` – Input datasets and generated match data.
- `assets/` – Visual assets used by the renderer.
- `archive/` – Archived simulation results.
- `tests/` – Test suite.

## .gitignore
The repository now ignores common Python artifacts, virtual environments, build outputs, and project‑specific directories:
```
__pycache__/
*.pyc
*.pyo
*.pyd
env/
venv/
ENV/
*.egg-info/
build/
dist/

data/
archive/
assets/
*.zip
```

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Run the simulation: `python main.py`

## License
MIT License.
