# Swiss Energy System Data

A curated, reproducible summary of open data on the Swiss energy system — national
energy balance, buildings, electricity, renewables and more — visualised as a
static website on GitHub Pages.

> **Status:** scaffold. The CSVs in `data/processed/` are **sample values** (flagged
> `status: sample` in `catalog/datasets.yml` and badged on the site) until each
> processor is implemented and run against the official source.

## How it fits together

```
 official sources ──fetch──► data/raw/ ──process──► data/processed/ ──build──► docs/data/*.json ──► GitHub Pages
 (catalog/sources.yml)       (gitignored)            (tidy CSV, committed)     (generated)           (docs/)
```

| Step | Command | What it does |
|---|---|---|
| fetch | `python -m pipeline.fetch [--source ID]` | Downloads files listed under `downloads:` in `catalog/sources.yml` into `data/raw/<source>/` |
| process | `python -m pipeline.process [module]` | Runs each module in `pipeline/process/`, turning raw files into tidy CSVs |
| build | `python -m pipeline.build_site` | Converts every dataset in `catalog/datasets.yml` into JSON for the site |
| preview | `python -m http.server -d docs 8000` | Serves the site at <http://localhost:8000> |

## Repository layout

```
catalog/
  sources.yml          # Who publishes what: publisher, URL, terms, download links
  datasets.yml         # Each dataset shown on the site: title, unit, source, chart type, status
data/
  raw/                 # Downloaded source files (gitignored, reproducible via fetch)
  processed/           # Tidy CSVs, one per dataset, grouped by theme
    national/  buildings/  electricity/  renewables/  mobility/  emissions/
pipeline/
  common.py            # Paths, catalog loading, tidy-schema validation
  fetch.py             # Downloader
  process/             # One module per source → one or more processed datasets
    _template.py       # Copy this to add a processor
    buildings_gwr.py   # Example: building register (GWR) → heating & age statistics
  build_site.py        # processed CSV → docs/data/<id>.json + catalog.json
docs/                  # GitHub Pages site (plain HTML + Chart.js, no build step)
  index.html  national.html  buildings.html  electricity.html  renewables.html  sources.html
  assets/app.js        # Renders every <div class="chart" data-dataset="..."> automatically
  assets/style.css
.github/workflows/
  pages.yml            # Build JSON + deploy site on push to main
  update-data.yml      # Monthly fetch + process, opens a PR with changed data
```

## Data conventions

Every processed dataset is a **tidy CSV** with exactly these columns:

| column | meaning |
|---|---|
| `year` | integer year (snapshot year for cross-sectional data) |
| `category` | series name, e.g. `Natural gas`, `Households`, `Solar PV` |
| `value` | number |
| `unit` | one unit per dataset, e.g. `PJ`, `TWh`, `MW`, `%` |

See [data/README.md](data/README.md) for details.

## Adding a dataset

1. Register the source in `catalog/sources.yml` (add `downloads:` if it can be fetched automatically).
2. Write a processor: copy `pipeline/process/_template.py`, output via `write_tidy()`.
3. Register the dataset in `catalog/datasets.yml` (`status: official` once it's real data).
4. Show it on a page: `<div class="chart" data-dataset="theme/dataset_id"></div>`.

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate elsewhere
pip install -r requirements.txt
python -m pipeline.build_site
python -m http.server -d docs 8000
```

**GitHub Pages:** in the repo settings, set *Pages → Source* to **GitHub Actions**.
The `pages.yml` workflow deploys on every push to `main`.

## Themes and main sources (planned)

| Theme | Sources |
|---|---|
| National energy balance | SFOE Overall Energy Statistics (Gesamtenergiestatistik) |
| Buildings | FSO Federal Register of Buildings and Dwellings (GWR/RegBL), GEAK/CECB certificates |
| Electricity | SFOE Electricity Statistics, Swissgrid, ElCom tariffs |
| Renewables | SFOE renewable energy statistics, electricity production plants register, sonnendach.ch |
| Mobility | FSO vehicle stock, SFOE transport energy |
| Emissions | FOEN Greenhouse Gas Inventory |

Source URLs in `catalog/sources.yml` should be checked against the publisher before
a processor is written. Each source keeps its own terms of use; cite the publisher
when reusing the data.
