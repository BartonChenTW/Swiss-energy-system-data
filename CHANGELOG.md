# Changelog

Notable changes to the website and its data. The newest version is shown in the site
footer and on the [Changelog page](https://bartonchentw.github.io/Swiss-energy-system-data/changelog.html).

Versions follow `MAJOR.MINOR.PATCH`: MINOR for new datasets, pages or features, PATCH
for fixes, wording and styling. To release, rename `Unreleased` to the new version
with today's date; `python -m pipeline.build_site` picks up the top released entry.

## [Unreleased]

## [0.6.0] - 2026-09-29
### Added
- Renewables: annual solar PV electricity production.
- Renewables: list of wind farms with number of turbines, years in operation and capacity.
- Heat page with a district heating section: consumption by sector, renewable district heat by source, and the SFOE register of thermal networks (growth and power by energy source).
- Electricity: energy communities section (ZEV, virtual ZEV, LEG) with PV installations and capacity by self-consumption type, and references on LEG.
- Mobility page with an electric vehicles section: plug-in share of new cars and of the stock, new cars by propulsion, electric cars on the road, and public charging stations.
- Library: models STEM (Swiss TIMES Energy systems Model, PSI) and ehubX (Empa).

## [0.5.0] - 2026-09-29
### Added
- Site version, build date and commit in the footer, and this Changelog page.
- Library: open smart meter datasets from CKW (Lucerne), EKZ load profiles and HEAPO (Zurich heat pumps).

## [0.4.0] - 2026-09-28
### Added
- Every chart is tagged as national or regional coverage; regional charts name their canton or city.
### Changed
- National tag in burnt orange so it contrasts with the regional blue.

## [0.3.0] - 2026-09-28
### Added
- Renewables detail: new-renewable electricity, PV, wind and biomass capacity, wind generation.
- Full Buildings section: stock performance, cantonal EPC classes (GEAK), Minergie, subsidised retrofits (Das Gebäudeprogramm), investment in renovation, embodied GHG of materials (KBOB), and the inputs of CESAR-P.

## [0.2.0] - 2026-09-28
### Added
- Catalog (`sources.yml`, `datasets.yml`, `references.yml`) as the single source of truth, validated by `pipeline.check`.
- Library page of reports, standards, dashboards, tools and models.
- Automatic provenance: every chart shows when its data was retrieved.
### Changed
- Sample data replaced with official federal sources (SFOE energy, electricity and renewables statistics, FSO building register).
- Heating-source shares labelled as share of number of buildings.

## [0.1.0] - 2026-09-28
### Added
- First version of the repository, the data pipeline and the GitHub Pages site.
