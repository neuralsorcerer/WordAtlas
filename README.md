# WordAtlas

WordAtlas builds interactive semantic maps from [**WordNet**](https://wordnet.princeton.edu/).

- CLI: list relations or export a Graphviz image (PNG/SVG/PDF)
- Web: FastAPI + Cytoscape.js interactive graph, with relation toggles, label and font controls, and layout presets

## Install

- From PyPI (recommended):

```bash
pip install wordatlas
```

- From source (this repo):

```bash
pip install -e .
```

Optional dev extras:

```bash
pip install -e .[dev]
```

> Note: For PNG/SVG/PDF rendering you need the system Graphviz tool (`dot`). See Quickstart below.

## Quickstart

```bash
# 1) Install system graphviz (for PNG/SVG/PDF rendering)
# - Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y graphviz
# - macOS (brew): brew install graphviz
# - Windows (choco): choco install graphviz -y

# 2) Create venv and install
python -m venv .venv
# Activate:
# - Linux/macOS: source .venv/bin/activate
# - Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .

# 3) First run downloads WordNet corpora automatically

# CLI — quick checks
wordatlas list happiness --depth 1 --json-out g.json   # write graph JSON
wordatlas show happiness --depth 1                     # compact summary

# CLI — query and export image
wordatlas graph happiness --depth 2 --out graph.png

# Web — start API/UI
wordatlas web --host 0.0.0.0 --port 8000
# open http://localhost:8000/
```

## CLI commands and flags

### Commands:

- `wordatlas list WORD` — build the graph and print a relation summary table (or `--json-out`)
- `wordatlas show WORD` — print a compact JSON-like summary (center, counts, samples)
- `wordatlas graph WORD` — render a Graphviz image and optional CSV/JSON exports

### Common flags:

- `--depth INT` — overall expansion depth (default from env; see Configuration)
- `--max-nodes INT` — cap total nodes in the graph
- `--relation ...` or `-r ...` (repeatable) — keep only selected edge types
- `--rel-depth relation:INT` (repeatable) — per-relation hop caps
  - Only relations you specify are constrained; others follow the overall `--depth`.
- `--pos-cap POS:INT` (repeatable) — cap nodes per POS (e.g., `n:80 a:30`)
- `--exclude WORD` (repeatable) — exclude words; `--stopwords file.txt` for a newline list
- `--min-degree INT` — drop nodes with degree less than N (center is kept)
- Rendering and exports:
  - `--out PATH` — output file (suffix .png/.svg/.pdf)
  - `--format {png,svg,pdf}` — override format regardless of `--out` suffix
  - `--csv-out edges.csv` — write `source,target,relation`
  - `--json-out graph.json` — dump graph JSON
  - `--open` — open the rendered image

### Examples:

```bash
# Synonyms only, prune low-degree nodes, export CSV
wordatlas graph happy -r synonym --min-degree 1 --csv-out edges.csv --out g.svg

# Cap adjective nodes and limit hypernym depth
wordatlas graph bright --pos-cap a:5 --pos-cap n:50 --rel-depth hypernym:1 --out g.png

# Remove custom stopwords
wordatlas graph happy --stopwords stop.txt --exclude joyful

# Override format regardless of --out suffix
wordatlas graph run --out output.png --format pdf  # writes output.pdf
```

## Web UI

- Sliders: label width and font size
- Layout presets: CoSE, Breadthfirst, Concentric, Grid

Tips:

- Click a node to recenter and rebuild the graph
- Use relation toggles to declutter specific edge types

## REST API

The web UI uses these endpoints; you can call them directly.

- GET `/api/health`

  - Returns status, version, uptime, NLTK corpora status, and cache metrics.
  - Example:

    ```bash
    curl http://localhost:8000/api/health
    ```

- GET `/api/graph`

  - Params: `word` (required), `depth` (int), `max_nodes` (int), `relation` (repeatable)
  - Server-side relation filtering applies if one or more `relation` params are supplied.
  - Example:

    ```bash
    curl "http://localhost:8000/api/graph?word=happiness&depth=1&relation=synonym&relation=hypernym"
    ```

- POST `/api/cache/clear`

  - Clears internal LRU caches to free memory.
  - Example:

    ```bash
    curl -X POST http://localhost:8000/api/cache/clear
    ```

## Relations supported

- synonyms, hypernyms, hyponyms, antonyms, similar_to

## Configuration

Environment variables:

- `WORDATLAS_DEFAULT_DEPTH` (int, default 1)
- `WORDATLAS_MAX_NODES` (int, default 300)
- `LOG_LEVEL` (str, default "INFO")

## Caching and performance

- NLTK corpora (`wordnet`, `omw-1.4`) are downloaded automatically on first use.
- WordNet synset lookups are cached with an internal LRU cache.
  - Inspect via `GET /api/health` (cache metrics) and clear via `POST /api/cache/clear`.
- Use `--relation` filters, `--rel-depth`, `--pos-cap`, and `--min-degree` to keep graphs manageable.

## Tests

```bash
pip install -e .[dev]
pytest -q
```

## Development

```bash
# install dev deps
pip install -e .[dev]

# run the web app (live reload)
wordatlas web --reload

# or use Make targets
make install-dev
make test
make lint
make format
make typecheck
```

## License

See [LICENSE](LICENSE) for full license text.

## Acknowledgements

- [WordNet by Princeton University](https://wordnet.princeton.edu/)
- NLTK WordNet interface
- FastAPI, Uvicorn
- Cytoscape.js
- Graphviz
