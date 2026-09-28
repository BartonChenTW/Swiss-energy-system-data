"""SFOE register of electricity production plants -> installed PV capacity.

Input : data/raw/bfe_production_plants/ch.bfe.elektrizitaetsproduktionsanlagen.zip
        ElectricityProductionPlant.csv (BeginningOfOperation, TotalPower [kW], SubCategory)
        SubCategoryCatalogue.csv (subcat_2 = Photovoltaik)
Output: renewables/pv_installed_capacity  (MW, cumulative by commissioning year)

Caveat: the register holds plants currently in operation at their current power,
so the series is a lower bound for past years. The current calendar year is
dropped because it is incomplete.
"""
import zipfile
from datetime import date

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_production_plants"
FILE = "ch.bfe.elektrizitaetsproduktionsanlagen.zip"
FIRST_YEAR = 2005


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        cats = pd.read_csv(zf.open("SubCategoryCatalogue.csv"))
        plants = pd.read_csv(zf.open("ElectricityProductionPlant.csv"),
                             usecols=["BeginningOfOperation", "TotalPower", "SubCategory"])

    pv_code = cats.loc[cats["de"].str.strip() == "Photovoltaik", "Catalogue_id"].item()
    pv = plants[plants["SubCategory"] == pv_code].copy()
    pv["year"] = pd.to_datetime(pv["BeginningOfOperation"], errors="coerce").dt.year

    last_full_year = date.today().year - 1
    by_year = pv.groupby("year")["TotalPower"].sum().sort_index().cumsum() / 1000  # kW -> MW
    by_year = by_year.loc[FIRST_YEAR:last_full_year]
    tidy = pd.DataFrame({"year": by_year.index.astype(int), "category": "Solar PV",
                         "value": by_year.values.round(1), "unit": "MW"})
    write_tidy(tidy, "renewables/pv_installed_capacity", [path], __name__,
               notes=f"{len(pv):,} PV plants in register; {pv['year'].isna().sum()} without commissioning date excluded.")
