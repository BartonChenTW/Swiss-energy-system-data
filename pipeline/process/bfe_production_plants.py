"""SFOE register of electricity production plants -> installed renewable capacity.

Input : data/raw/bfe_production_plants/ch.bfe.elektrizitaetsproduktionsanlagen.zip
        ElectricityProductionPlant.csv (BeginningOfOperation, TotalPower [kW], SubCategory)
        SubCategoryCatalogue.csv (subcat_2 = Photovoltaik, subcat_3 = Windenergie, subcat_4 = Biomasse)
Output: renewables/pv_installed_capacity             (MW, cumulative by commissioning year)
        renewables/wind_biomass_installed_capacity   (MW, cumulative by commissioning year)

Caveat: the register holds plants currently in operation at their current power,
so the series are lower bounds for past years. The current calendar year is
dropped because it is incomplete.
"""
import zipfile
from datetime import date

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_production_plants"
FILE = "ch.bfe.elektrizitaetsproduktionsanlagen.zip"


def cumulative_mw(plants: pd.DataFrame, first_year: int) -> pd.DataFrame:
    """Cumulative MW per label and commissioning year, as tidy rows."""
    last_full_year = date.today().year - 1
    wide = (plants.pivot_table(index="year", columns="label", values="TotalPower", aggfunc="sum")
            .reindex(range(int(plants["year"].min()), last_full_year + 1)).fillna(0)
            .cumsum() / 1000).loc[first_year:]
    long = wide.reset_index().melt(id_vars="year", var_name="category", value_name="value")
    return long.assign(value=long["value"].round(1), unit="MW")


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        cats = pd.read_csv(zf.open("SubCategoryCatalogue.csv"))
        plants = pd.read_csv(zf.open("ElectricityProductionPlant.csv"),
                             usecols=["BeginningOfOperation", "TotalPower", "SubCategory"])

    code = cats.set_index(cats["de"].str.strip())["Catalogue_id"]
    labels = {code["Photovoltaik"]: "Solar PV", code["Windenergie"]: "Wind", code["Biomasse"]: "Biomass"}
    plants = plants.assign(label=plants["SubCategory"].map(labels),
                           year=pd.to_datetime(plants["BeginningOfOperation"], errors="coerce").dt.year)
    plants = plants.dropna(subset=["label", "year"])

    pv = plants[plants["label"] == "Solar PV"]
    write_tidy(cumulative_mw(pv, 2005), "renewables/pv_installed_capacity", [path], __name__,
               notes=f"{len(pv):,} PV plants in the register with a commissioning date.")

    wb = plants[plants["label"].isin(["Wind", "Biomass"])]
    counts = wb["label"].value_counts()
    write_tidy(cumulative_mw(wb, 2000), "renewables/wind_biomass_installed_capacity", [path], __name__,
               notes=f"{counts.get('Wind', 0)} wind and {counts.get('Biomass', 0)} biomass plants in the register.")
