# Handoff: continue on Euler

Work paused on the workstation on 2026-09-28 because the endpoint security tool (Cortex XDR,
rule `powershell_cradles.b`) flags commands launched from VS Code there. The edits below were
made without running anything, so none of them have been executed or tested yet.
Delete this file once the work is merged.

## Done (untested)

- `pipeline/common.py`, `pipeline/fetch.py`: sources can have `status: planned` (+ `planned_for`);
  fetch skips them and no dataset may use them.
- `catalog/sources.yml`: 8 planned sources = the download wish list (monthly electricity balance,
  reservoirs, WASTA hydropower, ElCom prices, FSO GHG by sector, population, FOEN inventory, vehicles).
- `catalog/README.md`: documents `status` / `planned_for`.
- `pipeline/process/bfe_energy_statistics.py`: new outputs
  `national/gross_energy_by_source`, `national/supply_domestic_vs_imports`, `national/import_dependency`.
- `pipeline/process/bfe_electricity_statistics.py`: new outputs
  `electricity/cross_border_trade`, `electricity/consumption`.
- `pipeline/process/bfe_swissgrid_production.py` (new): `electricity/winter_balance`,
  `electricity/summer_balance`, `electricity/winter_production_by_source` from the daily Swissgrid files.
  Local check done earlier: daily production sums match the official annual statistics (±5 GWh);
  dashboard consumption differs by 1–3 %.
- `pipeline/process/bfe_production_plants.py`: new output `renewables/pv_per_building_by_canton`
  (reads the GWR for building counts).
- `catalog/datasets.yml`: entries added for the 3 national datasets only.

## To do

1. `python -m pipeline.fetch` (raw data is not in git), then `python -m pipeline.process`; fix any errors.
2. Add `catalog/datasets.yml` entries for the 6 remaining new datasets
   (2× cross-border/consumption, 3× winter/summer, 1× PV per building). Each needs `coverage: national`.
3. Sanity-check the new CSVs (e.g. import dependency ~70 %, winter consumption > winter production).
4. Pages: rework `docs/national.html`, `docs/electricity.html`, `docs/renewables.html` like
   `docs/buildings.html` (sub-sections, `section-note` text, a "What is not openly available" card).
5. `python -m pipeline.check` and `python -m pipeline.build_site`; preview with
   `python -m http.server -d docs 8000`.
6. Planned sources (see `catalog/sources.yml`): set `status: active` one at a time, inspect the file,
   write the processor.
7. Merge to `main` to deploy.
