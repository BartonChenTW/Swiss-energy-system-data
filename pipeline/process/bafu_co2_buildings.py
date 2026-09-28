"""FOEN estimated CO2 emissions of buildings (SIA 380/1) -> distribution by CO2 class.

Input : data/raw/bafu_co2_buildings/klima-co2_ausstoss_gebaeude_2056.csv.zip
        MAPGEO_GEB_CO2.txt (tab-separated, one row per residential building):
        CO2_CLASS (0 = no value, 1..7), CO2_RANGE (kg CO2 per m² heated area and year),
        GUE20 (1 = heating information last updated more than 20 years ago)
Output: buildings/co2_class_distribution  (% of residential buildings with an estimate)

Values are modelled for standard conditions (heating and hot water) from GWR data, not measured.
"""
import zipfile

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bafu_co2_buildings"
FILE = "klima-co2_ausstoss_gebaeude_2056.csv.zip"
MEMBER = "MAPGEO_GEB_CO2.txt"
LABEL = {"0": "0 (no direct emissions)", "0 - 5": "0–5", "5 - 10": "5–10", "10 - 15": "10–15",
         "15 - 20": "15–20", "20 - 25": "20–25", "> 25": "more than 25"}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        b = pd.read_csv(zf.open(MEMBER), sep="\t", dtype=str, usecols=["CO2_CLASS", "CO2_RANGE", "GUE20", "GEXPDAT"])

    rated = b[b["CO2_CLASS"] != "0"]
    ranges = rated.groupby("CO2_CLASS")["CO2_RANGE"].first().sort_index(key=lambda s: s.astype(int))
    unknown = set(ranges) - set(LABEL)
    if unknown:
        raise ValueError(f"Unexpected CO2_RANGE values: {unknown}")
    shares = rated["CO2_CLASS"].value_counts(normalize=True).reindex(ranges.index) * 100
    year = int(b["GEXPDAT"].dropna().max()[-4:])  # dd.mm.yyyy
    old_heating = (rated["GUE20"] == "1").mean() * 100
    write_tidy(pd.DataFrame({"year": year, "category": [LABEL[ranges[c]] for c in shares.index],
                             "value": shares.round(1).values, "unit": "% of buildings"}),
               "buildings/co2_class_distribution", [path], __name__,
               notes=f"{len(rated):,} of {len(b):,} residential buildings have an estimate; "
                     f"for {old_heating:.0f}% the heating information is more than 20 years old.")
