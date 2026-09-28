# Data

## `raw/`

Files exactly as downloaded from the publisher, in `raw/<source-id>/`. Not committed —
recreate with `python -m pipeline.fetch`. Sources without automatic download links
are placed here by hand; note the download date in the processor's docstring.

## `processed/`

One tidy CSV per dataset, at `processed/<theme>/<dataset>.csv`. The path without
`.csv` is the dataset id used in `catalog/datasets.yml` and on the site
(e.g. `national/final_energy_by_carrier`).

| column | type | rule |
|---|---|---|
| `year` | int | calendar year; snapshot year for cross-sectional data |
| `category` | str | series label, in the order it should appear in legends |
| `value` | float | no thousands separators; empty = missing |
| `unit` | str | a single unit per file |

Conventions:

- **Energy** in PJ (national balance) or TWh/GWh (electricity); **power** in MW.
- **Shares** in `%`, summing to 100 within a year.
- English category labels; keep the original German/French term in the processor if a mapping is ambiguous.
- Themes: `national`, `buildings`, `electricity`, `renewables`, `mobility`, `emissions`.

Files marked `status: sample` in `catalog/datasets.yml` hold illustrative placeholder
values for building the site. Do not cite them.
