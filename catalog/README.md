# Catalog

Everything this project knows about lives in three YAML files here. They are the
single source of truth: the pipeline reads them, `python -m pipeline.check`
validates them, and the website's Sources and Library pages are generated from them.

| File | Holds | One entry per |
|---|---|---|
| [sources.yml](sources.yml) | Machine-readable **data sources** the pipeline can fetch | publisher dataset (a CSV, zip, API) |
| [datasets.yml](datasets.yml) | **Datasets published on the site**, derived from sources | chart-ready tidy CSV in `data/processed/` |
| [references.yml](references.yml) | **Reports, websites, dashboards, tools and models** we cite or use but don't process | document / site / tool |

Rule of thumb: if the pipeline downloads it, it goes in `sources.yml`. If a person
reads or uses it, it goes in `references.yml`.

## Controlled vocabulary

Used across all three files. `pipeline.check` rejects anything else.

- **theme**: `national`, `buildings`, `electricity`, `renewables`, `heat`, `mobility`, `emissions`, `prices`, `scenarios`, `general`
- **reference type**: `report`, `standard` (norms such as SIA, often paid), `website`, `dashboard`, `tool`, `model`, `portal`
- **dataset chart**: `line`, `stacked-area`, `stacked-bar`, `hbar`
- **dataset coverage**: `national` (all of Switzerland, including national data broken down by canton) or `regional` (one canton, city or region, named in `region`)
- **dataset palette** (optional): `sequential` for ordered classes such as A–G labels; default is categorical
- **dataset status**: `official` (processed from the source), `sample` (placeholder values)

## `sources.yml`

| field | required | notes |
|---|---|---|
| `id` | yes | snake_case, unique. Also the folder `data/raw/<id>/` **and** the processor `pipeline/process/<id>.py` |
| `name` | yes | publisher's title (original language is fine) |
| `publisher` | yes | organisation, with acronyms |
| `theme` | yes | from the vocabulary |
| `url` | yes | landing page (opendata.swiss page if there is one) |
| `terms` | yes | licence / terms of use as published |
| `frequency` | no | update frequency stated by the publisher |
| `downloads` | no | list of `{url, filename}` fetched by `python -m pipeline.fetch` |
| `notes` | no | caveats: coverage, breaks in series, definitions |

## `datasets.yml`

| field | required | notes |
|---|---|---|
| `id` | yes | `<theme>/<name>`, the path of `data/processed/<id>.csv` |
| `title`, `description` | yes | shown on the chart card. Put definitions and caveats in the description |
| `source` | yes | a `sources.yml` id |
| `chart` | yes | from the vocabulary |
| `status` | yes | `official` or `sample` |
| `coverage` | yes | `national` or `regional`; shown as a tag on the chart card |
| `region` | if regional | e.g. `Canton of Geneva` |
| `palette` | no | `sequential` for ordered categories |

## `references.yml`

| field | required | notes |
|---|---|---|
| `id` | yes | snake_case, unique |
| `type` | yes | from the vocabulary |
| `title` | yes | |
| `publisher` | yes | organisation or authors |
| `url` | yes | stable link (DOI if available) |
| `themes` | yes | list from the vocabulary |
| `year` | no | publication year (reports, models) |
| `language` | no | e.g. `de`, `fr`, `en`, `de/fr` |
| `description` | no | one or two sentences: what it is, why it's useful here |
| `related_sources` | no | `sources.yml` ids it describes or builds on |
| `checked` | yes | date (YYYY-MM-DD) the link and content were last checked |
| `ev_profile` | no | puts the entry in the EV profile data study on the Mobility page; see below |

### `ev_profile` (optional, on references)

Open EV charging and driving data, shown as tables by region on the Mobility page. All fields are required
when the block is present:

| field | values |
|---|---|
| `region` | `Switzerland`, `Europe` (outside Switzerland), `World` (outside Europe) |
| `data` | list of `sessions` (charging sessions), `load` (load profiles or time series), `driving` (trips, travel diaries, GPS), `status` (charger occupancy), `synthetic` (model outputs and generators) |
| `coverage` | place, size and period, e.g. `"Norway, 267 users at 12 sites, Nov 2018–May 2021"` |
| `resolution` | e.g. `session`, `5 min`, `hourly`, `live` |
| `access` | `open` (direct download), `registration` (free account or key), `restricted` (contract, fee or on request) |
| `licence` | as published, or `not stated` |

## Provenance (automatic)

You don't edit provenance by hand:

1. `pipeline.fetch` records URL, retrieval time, `Last-Modified` and SHA-256 of each
   download in `data/raw/<source>/_manifest.json`.
2. Each processor passes its input files to `write_tidy()`, which writes
   `data/processed/<id>.meta.json` next to the CSV (committed) with the processor
   name, generation time and those input records.
3. `build_site` copies that into the site JSON, so every chart shows when its data
   was retrieved.
