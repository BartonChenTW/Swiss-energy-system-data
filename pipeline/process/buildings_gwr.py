"""Federal Register of Buildings and Dwellings (GWR) -> building stock statistics.

Input : data/raw/bfs_gwr/ch.zip   (python -m pipeline.fetch --source bfs_gwr)
Output: buildings/heating_energy_source
        buildings/buildings_by_construction_period

Variable names (GENH1, GBAUP, GKAT) and their codes follow the GWR feature
catalogue. TODO: verify the codes and the file layout (member name, separator)
against the catalogue version shipped with the download before setting these
datasets to `status: official`.
"""
import zipfile
from datetime import date

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfs_gwr"

# GKAT: building category. 1020-1040 = residential buildings.
RESIDENTIAL_GKAT = {"1020", "1030", "1040"}

# GENH1: energy / heat source of the main heating system.
HEATING_SOURCE = {
    "7501": "Heat pump (ambient heat)",   # air
    "7510": "Heat pump (ambient heat)",   # geothermal
    "7511": "Heat pump (ambient heat)",   # geothermal probe
    "7512": "Heat pump (ambient heat)",   # geothermal collector
    "7513": "Heat pump (ambient heat)",   # water
    "7520": "Natural gas",
    "7530": "Heating oil",
    "7540": "Wood", "7541": "Wood", "7542": "Wood", "7543": "Wood",
    "7560": "Electricity (direct)",
    "7580": "District heating", "7581": "District heating", "7582": "District heating",
}
HEATING_ORDER = [
    "Heating oil", "Heat pump (ambient heat)", "Natural gas", "Wood",
    "Electricity (direct)", "District heating", "Other / unknown",
]

# GBAUP: construction period.
CONSTRUCTION_PERIOD = {
    "8011": "Before 1919",
    "8012": "1919–1945",
    "8013": "1946–1960",
    "8014": "1961–1980", "8015": "1961–1980",
    "8016": "1981–2000", "8017": "1981–2000", "8018": "1981–2000", "8019": "1981–2000",
    "8020": "2001–2010", "8021": "2001–2010",
    "8022": "After 2010", "8023": "After 2010",
}
PERIOD_ORDER = list(dict.fromkeys(CONSTRUCTION_PERIOD.values()))


def read_buildings(zip_path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        member = next(n for n in zf.namelist() if "gebaeude" in n.lower() and n.lower().endswith(".csv"))
        with zf.open(member) as f:
            return pd.read_csv(f, sep="\t", dtype=str, usecols=["GKAT", "GBAUP", "GENH1"])


def run() -> None:
    path = RAW_DIR / SOURCE_ID / "ch.zip"
    if not path.exists():
        print(f"  {path.name} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return

    snapshot_year = date.fromtimestamp(path.stat().st_mtime).year
    buildings = read_buildings(path)
    residential = buildings[buildings["GKAT"].isin(RESIDENTIAL_GKAT)]

    heating = residential["GENH1"].map(HEATING_SOURCE).fillna("Other / unknown")
    shares = (heating.value_counts(normalize=True) * 100).reindex(HEATING_ORDER, fill_value=0)
    write_tidy(pd.DataFrame({
        "year": snapshot_year, "category": shares.index, "value": shares.round(1).values, "unit": "%",
    }), "buildings/heating_energy_source")

    periods = residential["GBAUP"].map(CONSTRUCTION_PERIOD).dropna()
    counts = periods.value_counts().reindex(PERIOD_ORDER, fill_value=0) / 1000
    write_tidy(pd.DataFrame({
        "year": snapshot_year, "category": counts.index, "value": counts.round(1).values,
        "unit": "thousand buildings",
    }), "buildings/buildings_by_construction_period")
