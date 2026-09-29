# Log

Working log of this repository, newest first: what was done, the decisions behind it, and
what was learned about data availability. It serves the repository's two goals: **a.** collect
Swiss energy system modelling data, and **b.** identify the gaps in the existing data.

Open work is in [TODO.md](TODO.md). Site releases are in [CHANGELOG.md](CHANGELOG.md).

## 2026-09-29

### Done
- **0.8.1:** section links on the Buildings page styled as buttons; a Back to top button on every page.
- Added TODO.md and LOG.md and wrote down the repository's two goals in the README.
- **0.8.0:** study of open EV profile data on the Mobility page: 43 datasets and generators for
  Switzerland, Europe and the rest of the world, stored as `references.yml` entries with a new
  `ev_profile` block (validated by `pipeline.check`).
- **0.7.0:** light/dark switch; stacked/lines switch on stacked charts; greenhouse gas emissions
  by sector and gas on the National page (FOEN inventory).
- **0.6.0:** annual PV production; wind farm list; models STEM and ehubX; Heat page with district
  heating; energy communities on the Electricity page; Mobility page with electric vehicles.
- **0.5.0:** site version and Changelog page; smart meter datasets in the Library (PR #1, merged;
  branch deleted).

### Decisions
- **"TIMS"** was read as the Swiss TIMES model (STEM, PSI); nothing named TIMS was found.
- **Wind farms:** the plant register has no farm names, so turbines within 3 km are grouped and
  named after their main municipality. Years are those of the turbines now running.
- **EV charging:** the chart uses stations, not charging points; the point count falls in 2025
  while stations keep rising.
- **EV study:** restricted sources are listed too, marked "Restricted", to document gaps (goal b).
- **Releases:** one minor version per batch of new data or pages, released when pushed.

### Findings on data availability
- FSO passenger car tables on opendata.swiss (PXWeb) predate the revision of 4 Feb 2026; the
  revised series are only on the stats.swiss SDMX API.
- The FOEN greenhouse gas data is only on LINDAS (SPARQL); a GET request returns CSV.
- ZEV and LEG have no register. The only national numbers are the SFOE survey (PV in ZEV) and
  Swissolar's estimate of about 1,860 LEG by June 2026.
- The thermal networks register has one implausible energy value (`tn1680`, 23 TWh); the charts
  do not use the energy field.
- ElaadNL (Netherlands) no longer publishes its open charging sessions.
- ACN-Data (Caltech) is limited to education and research use, although often called open.

### Environment
- The session on the ETH Euler login node ended unexpectedly twice. `/tmp` is local to each
  login node, so the Python environment now lives in `.venv/` (gitignored), and work is committed
  after each section.
- Python 3.12 comes from the software stack
  (`/cluster/software/stacks/2024-06/.../python-3.12.8-*/bin/python3`); `module load` did not take
  effect in the tool shell.

## 2026-09-28

### Done
- **0.1.0–0.4.0:** repository, pipeline and GitHub Pages site; official federal sources replacing
  sample data; the catalog (`sources.yml`, `datasets.yml`, `references.yml`) with provenance;
  renewables detail and the Buildings section (retrofit, EPC, LCA, CESAR-P); national/regional
  coverage tags on every chart.
