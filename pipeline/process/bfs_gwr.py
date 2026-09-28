"""Federal Register of Buildings and Dwellings (GWR) -> residential building stock.

Input : data/raw/bfs_gwr/ch.zip
        gebaeude_batiment_edificio.csv (tab-separated, one row per building)
        kodes_codes_codici.csv (code labels, used to check the mappings below)
Output: buildings/heating_energy_source            (% of residential buildings with a recorded source)
        buildings/buildings_by_construction_period  (thousand residential buildings)

Filters: GSTAT 1004 (existing), GKAT 1020/1030/1040 (residential).
The snapshot year is the export date in GEXPDAT.
"""
import zipfile

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfs_gwr"
FILE = "ch.zip"

EXISTING = "1004"
RESIDENTIAL = {"1020", "1030", "1040"}

# GENH1: energy source of heating system 1. Codes 7500 (none) and 7598 (undetermined)
# and blanks are excluded from the shares.
HEATING_SOURCE = {
    "7501": "Heat pump (air, ground, water)",
    "7510": "Heat pump (air, ground, water)",
    "7511": "Heat pump (air, ground, water)",
    "7512": "Heat pump (air, ground, water)",
    "7513": "Heat pump (air, ground, water)",
    "7530": "Heating oil",
    "7520": "Gas",
    "7540": "Wood", "7541": "Wood", "7542": "Wood", "7543": "Wood",
    "7560": "Electricity (direct)",
    "7580": "District heating", "7581": "District heating", "7582": "District heating",
    "7550": "Other", "7570": "Other", "7599": "Other",
}
NOT_RECORDED = {"7500", "7598"}

# GBAUP: construction period
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


def check_codes(codes: pd.DataFrame, variable: str, mapped: set) -> None:
    """Fail if the register defines codes for `variable` that this module doesn't handle."""
    defined = set(codes.loc[codes["CMERKM"] == variable, "CECODID"])
    unknown = defined - mapped
    if unknown:
        raise ValueError(f"{variable}: codes {sorted(unknown)} are not mapped in {__name__}")


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        codes = pd.read_csv(zf.open("kodes_codes_codici.csv"), sep="\t", dtype=str)
        buildings = pd.read_csv(zf.open("gebaeude_batiment_edificio.csv"), sep="\t", dtype=str,
                                usecols=["GSTAT", "GKAT", "GBAUP", "GENH1", "GEXPDAT"])

    check_codes(codes, "GENH1", set(HEATING_SOURCE) | NOT_RECORDED)
    check_codes(codes, "GBAUP", set(CONSTRUCTION_PERIOD))

    snapshot_year = int(buildings["GEXPDAT"].dropna().max()[:4])
    res = buildings[(buildings["GSTAT"] == EXISTING) & buildings["GKAT"].isin(RESIDENTIAL)]

    heating = res["GENH1"].map(HEATING_SOURCE).dropna()
    shares = heating.value_counts(normalize=True) * 100  # largest first
    shares = pd.concat([shares.drop("Other", errors="ignore"), shares.filter(["Other"])])  # "Other" last
    write_tidy(pd.DataFrame({"year": snapshot_year, "category": shares.index,
                             "value": shares.round(1).values, "unit": "%"}),
               "buildings/heating_energy_source", [path], __name__,
               notes=f"{len(heating):,} of {len(res):,} existing residential buildings have a recorded heating source.")

    periods = res["GBAUP"].map(CONSTRUCTION_PERIOD).dropna()
    counts = periods.value_counts().reindex(PERIOD_ORDER, fill_value=0) / 1000
    write_tidy(pd.DataFrame({"year": snapshot_year, "category": counts.index,
                             "value": counts.round(1).values, "unit": "thousand buildings"}),
               "buildings/buildings_by_construction_period", [path], __name__,
               notes=f"{len(periods):,} of {len(res):,} existing residential buildings have a recorded construction period.")
