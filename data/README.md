# Data

## `raw/`

Files exactly as downloaded from the publisher, in `raw/<source-id>/`, plus a
`_manifest.json` written by `python -m pipeline.fetch` (URL, retrieval time,
`Last-Modified`, SHA-256, size). Not committed. Recreate with `python -m pipeline.fetch`.

A file placed here by hand still works, but its provenance is marked "not in fetch
manifest". Prefer adding a `downloads:` entry to `catalog/sources.yml`.

## `processed/`

One tidy CSV per dataset at `processed/<theme>/<dataset>.csv`, with a provenance
record `<dataset>.meta.json` beside it. Both are committed, so a diff shows exactly
what changed and why. The path without `.csv` is the dataset id used in
`catalog/datasets.yml` and on the site (e.g. `national/final_energy_by_carrier`).

| column | type | rule |
|---|---|---|
| `year` | int | calendar year; snapshot year for cross-sectional data |
| `category` | str | series label, in the order it should appear in legends |
| `value` | float | no thousands separators; empty = missing |
| `unit` | str | a single unit per file |

Conventions:

- **Energy** in PJ (national balance) or TWh/GWh (electricity); **power** in MW.
- **Shares** in `%`, summing to 100 within a year.
- English category labels. Keep the original German/French term in the processor's mapping.
- Theme folders match the vocabulary in `catalog/README.md`.
- Never edit these files by hand. Change the processor and re-run it.
