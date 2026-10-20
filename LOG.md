# Log

Working log of this repository, newest first: what was done, the decisions behind it, and
what was learned about data availability. It serves the repository's three goals: **a.** collect
Swiss energy system modelling data, **b.** identify the gaps in the existing data, and **c.** review
whether the data is enough to train a foundation model for the building domain.

Open work is in [TODO.md](TODO.md). Site releases are in [CHANGELOG.md](CHANGELOG.md).

## 2026-10-20

### Done
- Sources page: theme and status filters; `build_site` now records every input source of a dataset.
- Renewables: SFOE solar potential of municipalities as a new source (`bfe_solar_potential`, two charts),
  a table of potential studies, 17 references and three gaps.
- Scenarios page (energy system studies): CROSS v2022-09 results as a new source (`sweet_cross_results`,
  three charts), a table of 16 studies, 17 references and two gaps. EP2050+ link fixed.

### Decisions
- "EPFL's solar and wind study" is read as Dujardin, Kahl & Lehning 2021 (EPFL CRYOS / SLF), the study
  EPFL and WSL announced as "untapped solar and wind potential in Swiss mountains".
- Energy system studies get their own page (Scenarios), since they span all sectors.
- CROSS charts show one scenario (abroad-together), the only one all nine models ran; the tidy format
  has no axis for a second dimension, so models are bars.

### Findings on data availability
- Open scenario results are rare: only CROSS v2022-09 (CSV) and PSI's STEM study (XLSX) are CC BY 4.0.
  EP2050+ results are downloadable but under admin.ch terms (written consent for reproduction).
- Models disagree widely even in the same CROSS scenario: 2050 solar 9–42 TWh, wind 0–11 TWh.
- SFOE solar potential: 65 TWh/a on roofs, 86 TWh/a with facades; 27 % of the roof potential in Oct–Mar.
- EPFL's siting study data are only "available upon reasonable request"; EPFL's EnviDat datasets
  (hourly PV potential, power-system inputs) are the open alternative.

## 2026-10-19

### Done
- **0.10.0:** finished the work begun on the workstation on 2026-09-28 (branch `euler-handoff`): fetched and
  processed on Euler; all processors run. Nine new datasets on the National, Electricity and
  Renewables pages, which now follow the Buildings layout (sections, notes, data gaps).
- Planned sources (`status: planned`) in `catalog/sources.yml`: the download wish list, listed in TODO.md.
- New gap: history of the production plant register (Renewables).
- Library: Swiss SolarWind Explorer and EDGE Recommender.
- Bumped the GitHub Actions in both workflows to their Node 24 releases.

### Decisions
- Related Swiss platforms (tools, dashboards) go into `references.yml` and the Library, not a
  separate page; pages link to them where relevant.
- Gross energy chart: coal and waste are one series, as in final energy, to stay within the
  eight-colour palette.

### Findings on data availability
- Sanity checks: import dependency 67–76 % since 2018 (about 80 % 1980–2010); domestic production
  plus net imports equals gross consumption. Winter consumption exceeded domestic production in
  every complete winter except 2020, 2024 and 2025; the largest gap was 6.5 TWh (winter 2022).
- Winter 2026 nuclear output was low (8.5 TWh): Gösgen was offline from May 2025 to March 2026.
- PV per existing building: 2.78 kW for Switzerland, 1.35 (UR) to 4.72 (LU).
- The workstation's endpoint security (Cortex XDR) blocks commands launched from VS Code there,
  so pipeline runs happen on Euler.

## 2026-09-30

### Done
- **0.9.0:** Data gaps page (goal b) from a new `catalog/gaps.yml`: 15 gaps in four sectors,
  validated by `pipeline.check`; the Buildings gap list now reads from it.

### Decisions
- Gaps are catalog entries like sources and references, so each is recorded once and cites its
  evidence by id; pages show all gaps or one theme.
- Gap status vocabulary: not published, restricted, paid, incomplete, not machine-readable.

## 2026-09-29

### Done
- Added goal c (foundation model readiness for buildings) to the README, TODO.md and LOG.md, with review steps in TODO.md.
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
