# Swiss Energy System Data

A curated, reproducible summary of open data on the Swiss energy system — national
energy balance, buildings, electricity, renewables and more — visualised on
**[GitHub Pages](https://bartonchentw.github.io/Swiss-energy-system-data/)**.

Every chart is built from an official source by a script in this repo, and records
where its data came from and when it was retrieved.

## How information is organised

Everything the project knows about lives in **three catalogue files** under `catalog/`:

| File | What goes in it | Shown on |
|---|---|---|
| `catalog/sources.yml` | Machine-readable **data sources** the pipeline downloads (CSV, zip, API) | Sources page |
| `catalog/datasets.yml` | **Datasets on the site**: title, unit, source, chart type, status | Every chart card |
| `catalog/references.yml` | **Reports, websites, dashboards, tools, models** we cite but don't process | Library page |

The rule: if the pipeline downloads it, it goes in `sources.yml`. If a person reads or
uses it, it goes in `references.yml`. Field definitions and the controlled vocabulary
(themes, types) are in [catalog/README.md](catalog/README.md), and
`python -m pipeline.check` enforces them.

**Naming convention:** a source id such as `bfs_gwr` is also its raw-data folder
`data/raw/bfs_gwr/` and its processor `pipeline/process/bfs_gwr.py`.

**Provenance** is recorded automatically at each step:

```
fetch   → data/raw/<source>/_manifest.json      url, retrieved, Last-Modified, sha256
process → data/processed/<id>.csv + .meta.json  processor, generated, inputs (from manifest)
build   → docs/data/<id>.json                   shown on the chart card as "Retrieved …"
```

## Pipeline

```
catalog/sources.yml ─fetch─► data/raw/ ─process─► data/processed/ ─check─► build ─► docs/data/*.json ─► GitHub Pages
                             (gitignored)          (tidy CSV + provenance, committed)   (generated)
```

| Step | Command | What it does |
|---|---|---|
| fetch | `python -m pipeline.fetch [--source ID] [--force]` | Downloads files listed under `downloads:` and records them in the manifest |
| process | `python -m pipeline.process [module]` | Runs `pipeline/process/<source>.py`, writing tidy CSVs and provenance |
| check | `python -m pipeline.check [--links]` | Validates catalogue schema, cross-references and processed files. `--links` also tests every URL |
| build | `python -m pipeline.build_site` | Converts datasets and catalogue into JSON for the site |
| preview | `python -m http.server -d docs 8000` | Serves the site at <http://localhost:8000> |

## Repository layout

```
catalog/            sources.yml · datasets.yml · references.yml · README.md (schema)
data/
  raw/              downloads, one folder per source (gitignored; reproducible via fetch)
  processed/        <theme>/<dataset>.csv + <dataset>.meta.json (committed)
pipeline/
  common.py         paths, catalogue validation, tidy contract, provenance
  fetch.py  check.py  build_site.py
  process/          one module per source; _template.py to start a new one
docs/               the website (plain HTML + Chart.js, no build step)
.github/workflows/  pages.yml (check + deploy on push) · update-data.yml (monthly refresh PR)
```

## Current datasets

| Dataset | Source | Coverage |
|---|---|---|
| Final energy consumption by carrier / sector | SFOE Overall Energy Statistics (OGD 115) | 1980–2025, PJ |
| Electricity production by technology | SFOE Electricity Statistics (OGD 32) | 1990–2025, TWh |
| Installed solar PV capacity | SFOE register of production plants | 2005–2025, MW |
| Main heating energy source of residential buildings | FSO building register (GWR) | current snapshot, % |
| Residential buildings by construction period | FSO building register (GWR) | current snapshot |

## Adding something

- **A dataset:** register the source in `sources.yml` (with `downloads:`), copy
  `pipeline/process/_template.py` to `pipeline/process/<source_id>.py`, register the
  output in `datasets.yml`, and add `<div class="chart" data-dataset="theme/name"></div>` to a page.
- **A report, website or tool:** add an entry to `references.yml` with today's date
  in `checked`. It appears on the Library page on the next deploy.

Run `python -m pipeline.check` before committing.

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows; use bin/activate elsewhere
pip install -r requirements.txt
python -m pipeline.fetch        # the building register is a ~950 MB download
python -m pipeline.process
python -m pipeline.check
python -m pipeline.build_site
python -m http.server -d docs 8000
```

## Data licence

The data belongs to its publishers and is reused under their terms, listed per source
in `catalog/sources.yml` and on the Sources page. The federal sources used so far
allow free use with attribution (for example "Source: Swiss Federal Office of Energy
SFOE" or "Bundesamt für Statistik; Eidg. Gebäude- und Wohnungsregister").
