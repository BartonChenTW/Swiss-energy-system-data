# Log

Working log of this repository, newest first: what was done, the decisions behind it, and
what was learned about data availability. It serves the repository's three goals: **a.** collect
Swiss energy system modelling data, **b.** identify the gaps in the existing data, and **c.** review
whether the data is enough to train a foundation model for the building domain.

Open work is in [TODO.md](TODO.md). Site releases are in [CHANGELOG.md](CHANGELOG.md).

## 2026-10-23

### Done
- **0.13.0:** new source `hp_catch` (ETH Zurich, CC BY 4.0, ESSD preprint essd-2026-448): monthly and seasonal
  natural inflow into 107 storage reservoirs, 1991–2022. The processor reads the Zarr arrays inside the 214 MB
  zip without extracting it; `zarr` (<3) added to requirements.txt.

### Decisions
- Only "direct contributors" reservoir inflows are summed: they exclude water from reservoirs upstream, so the
  total has no double counting. Run-of-river inflows are not summed, since plants on one river share its water.

### Findings on data availability
- HP-CatCH is the first open dataset linking Swiss reservoirs and run-of-river plants to their catchments; it gives
  natural inflows, not production or reservoir levels per plant.
- Natural inflow into storage reservoirs averages 13.2 billion m³ a year (1991–2022), 74 % from April to September;
  lowest 10.3 (2005), highest 16.9 (1999). The monthly mean peaks in June (about 2.3 billion m³).

## 2026-10-22

### Done
- Renewables: Hydropower, snow and glaciers section with three new sources: `glamos` (glacier mass balance
  and length change), `meteoswiss_snow` (snow days at four stations) and `meteodat_waegital_swe` (snow water
  equivalent of a storage lake catchment). Four charts, five references, two gaps.
- Study table on hydropower, snow and glaciers on the Renewables page, with nine studies in `references.yml`.
- Optional `span_gaps` field for line charts whose series are not observed every year.
- Sub-annual data: tidy files may use `period` (date, month or ISO week) instead of `year`; `build_site`,
  `pipeline.check` and the charts handle both. Activated `bfe_reservoirs` and `bfe_electricity_monthly`: four
  charts on stored energy in storage lakes and monthly hydropower.
- Footer and README credit: initiated by Barton Chen (UESL, Empa).

### Decisions
- Snow and glaciers go under the `renewables` theme, next to hydropower, instead of a new theme.
- Glacier mass balance shows only the two glaciers measured every year since 1915 (Great Aletsch,
  Silvretta); Claridenfirn lacks 1994–1995.
- Snow and glacier charts are tagged regional, since they show selected stations and glaciers.

### Findings on data availability
- Hydropower data already on the site: annual run-of-river and storage production (1990–2025), hydropower
  in the renewables and gross energy balances (1980/1990–2025), and winter production from Swissgrid
  (2016–2026). Reservoir fill levels and WASTA plant statistics are still planned sources.
- GLAMOS data are free only for scientific and non-commercial use; MeteoSwiss open data are CC BY 4.0.
- No open national snow water equivalent series: SLF's SPASS (1962–2023) is under the WSL data policy, OSHD
  grids cover only 2016–2022 with unstated terms. The Wägital series (1943–2026, CC BY) is the exception.
- Wägital snow on 1 April averages 15.2 million m³ (1943–2026). Snow days fell by 15–30 a year between
  1961–1990 and 1997–2026 at all four stations. Since 1915 Great Aletsch has lost 66 m w.e. and Silvretta 43 m w.e.
- Storage lakes: capacity 8.9 TWh (8.5 TWh in 2000, as dams were raised), about 14 % of annual consumption.
  Spring lows fall in April–May, autumn highs in September–November. Lowest spring level 0.70 TWh (2000);
  in early 2023 the lakes were 75 % full against a 60 % mean, after the crisis-year savings. Monthly sums of
  run-of-river and storage production match the annual statistics (2025: 16.3 and 21.2 TWh). Storage plants
  also peak in June–July, not in winter.
- Studies: net glacier loss supplied 3–4 % of Swiss hydropower since 1980 (Schaefli 2019). Of the studies, only
  Haddad et al. 2025 (run-of-river output per plant 1991–2022, Nexus-e) publish their data openly (CC BY 4.0).

## 2026-10-20

### Done
- **0.11.0:** Sources page: theme and status filters; `build_site` now records every input source of a dataset.
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
