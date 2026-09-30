# TODO

Open work for this repository, grouped by its three goals:

- **a. Collect Swiss energy system modelling data**: open, machine-readable data that
  energy system models need, processed reproducibly and shown on the site.
- **b. Identify the gaps in the existing data**: what modellers need but cannot get openly,
  with evidence (who holds it, under which terms).
- **c. Review whether the data is enough to train a foundation model for the building domain**:
  what such a model needs, how much of it is openly available for Switzerland, and what is missing.

Tick an item when it is done and add a line to [LOG.md](LOG.md). User-facing changes also go
under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).

## a. Collect data

### Electricity
- [ ] Process the registered Swissgrid sources (`bfe_swissgrid_production`, `bfe_swissgrid_consumption`). Needs sub-annual data support, see *Site*.
- [ ] Consumption by sector, imports and exports (the Electricity page says they are planned).
- [ ] Tariffs by municipality from ElCom (`elcom_tariffs` is a placeholder; terms still TBD).
- [ ] Smart meter rollout, 2019–2024 (smart and conventional meters are already in the `bfe_self_consumption_survey` workbook).

### Heat
- [ ] Heat delivered by waste incineration plants (SFOE open data on KVA, 2010–2024).
- [ ] District heat input mix (SFOE overall energy statistics, table T26 in the yearly XLSX).
- [ ] Heat pumps: stock or sales by type (find an open source).

### Mobility
- [ ] Electricity use of road transport (SFOE end-use analysis, sheet Tabelle38; the download id changes with each edition).
- [ ] Energy use by transport mode, public transport.
- [ ] Process one open Swiss EV profile dataset as a chart, e.g. ETH's municipal charging demand for 2050 (needs sub-annual support).

### Renewables
- [ ] Hydropower plants by type and capacity (SFOE WASTA statistics).

### Emissions
- [ ] International aviation and the land-use balance as separate series (already in the FOEN download).

### Scenarios
- [ ] Energieperspektiven 2050+ scenario results; replace the publication-search link of `bfe_energy_perspectives_2050` with a stable page.

### Site
- [ ] Support monthly, hourly and 15-minute datasets in the tidy contract and the charts (Swissgrid, Winterthur LEG load profile, EV profiles).

## b. Identify gaps

- [x] A site-wide *Data gaps* page that collects the gaps below per sector, with evidence and the organisation that could publish the data (`catalog/gaps.yml`, `docs/gaps.html`).
- [ ] Add each new gap to `catalog/gaps.yml` as it is found, and review the list when sources are updated.

Known gaps so far (ticked: on the gaps page):

- [x] **Buildings:** no national open energy performance certificates (GEAK); no renovation-rate series; measured energy use per building only in Geneva; no embodied emissions of the stock; SIA norms are paid; the open Minergie dataset is incomplete.
- [x] **Electricity:** no register of ZEV, virtual ZEV or LEG and their members; self-consumption known only from the SFOE survey of grid operators (2019–2024).
- [x] **Heat:** the thermal networks register is voluntary and incomplete (power missing for about a sixth, commissioning year for about a quarter, energy for about half); the district heat input mix exists only as a spreadsheet table.
- [x] **Mobility:** SFOE keeps no history of charger status; no open charging-session or home-charging data; MZMV travel diaries need an FSO contract; utility smart-charging pilots (EKZ, BKW, CKW) publish no data.
- [x] **Licences to clarify** (on the page; still to ask the publishers): ChargePlace Scotland, Dundee, My Electric Avenue (not stated); UrbanEV and CHARGED (scraped from apps).

## c. Foundation model readiness (buildings)

- [ ] **Define the requirements** of a building-domain foundation model: which data types
  (per-building electricity and heat time series, building attributes and geometry, heating
  system, energy labels, retrofits, occupancy, weather), what scale (buildings × years ×
  resolution) and which licence terms (training allowed, redistribution of derived models).
- [ ] **Inventory the Swiss open data** against these requirements, starting with what the repo
  already lists: the building register (GWR), FOEN's modelled CO2 per building, Geneva's measured
  heat index, Lucerne GEAK, the smart meter datasets (EKZ load profiles, HEAPO heat pumps, CKW
  Lucerne) and open weather data (MeteoSwiss). Record size, resolution, period and licence.
- [ ] **Compare with the corpora used for building foundation models** elsewhere, e.g. NREL's
  End-Use Load Profiles (ResStock/ComStock) and BuildingsBench, and the Building Data Genome 2
  (verify each: size, licence, whether real or simulated).
- [ ] **Check licences for ML use:** whether training and publishing model weights is allowed
  (CC BY, opendata.swiss "open use", "commercial use on request", research-only terms).
- [ ] **Conclude**: enough for pre-training, enough only for fine-tuning or evaluation, or not
  enough, and which gaps matter most (these feed goal b).
- [ ] **Publish the review** on the site, as a section of the Buildings page or the Data gaps page.

## Maintenance

- [ ] **Every April:** the FOEN greenhouse gas inventory is published as a new LINDAS cube version. Update the version number in the `foen_ghg_inventory` query in `catalog/sources.yml`.
- [ ] **New SFOE editions:** pubdb download ids change (e.g. `bfe_self_consumption_survey`, id 12429). Update the URL when a new edition appears.
- [ ] **Before 19 Oct 2026:** GitHub's `ubuntu-latest` moves to Ubuntu 26 and actions on Node 20 are deprecated. Bump `actions/checkout`, `setup-python`, `configure-pages` and `upload-pages-artifact` in both workflows and check they still run.
- [ ] Run `python -m pipeline.check --links` now and then. Some sites (MDPI, National Grid, Mendeley) block scripts and answer 403 although the link works in a browser.
