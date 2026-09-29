"""SFOE register of thermal networks (district heating and cooling) -> networks by energy source.

Input : data/raw/bfe_thermal_networks/ch.bfe.thermische-netze.zip
        ch.bfe.thermische-netze.csv (BeginningOfOperation, Power [MW], EnergySource1 = main source)
        EnergySourceCatalogue.csv   (Catalogue_id -> EnergySource__en)
Output: heat/thermal_networks_power_by_source   (MW by main energy source, current register)
        heat/thermal_networks_by_commissioning  (cumulative number of networks by year, by source group)

Caveat: operators report voluntarily; power is missing for about a sixth of the networks
and the commissioning year for about a quarter. Networks that have closed are not listed.
"""
import zipfile
from datetime import date

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_thermal_networks"
FILE = "ch.bfe.thermische-netze.zip"
FIRST_YEAR = 1980

GROUPS = {  # EnergySource catalogue id -> group, in stack order (bottom first)
    16: "Waste incineration",
    4: "Wood", 5: "Wood", 6: "Wood",
    10: "Heat pumps (lake, ground, air, wastewater)", 11: "Heat pumps (lake, ground, air, wastewater)",
    12: "Heat pumps (lake, ground, air, wastewater)", 13: "Heat pumps (lake, ground, air, wastewater)",
    15: "Heat pumps (lake, ground, air, wastewater)",
    14: "Other waste heat (industry, nuclear, tunnel)", 17: "Other waste heat (industry, nuclear, tunnel)",
    18: "Other waste heat (industry, nuclear, tunnel)",
    7: "Biogas & solar thermal", 8: "Biogas & solar thermal", 20: "Biogas & solar thermal",
    1: "Oil & natural gas", 2: "Oil & natural gas", 3: "Oil & natural gas",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        cats = pd.read_csv(zf.open("EnergySourceCatalogue.csv"), encoding="utf-8-sig")
        nets = pd.read_csv(zf.open("ch.bfe.thermische-netze.csv"), encoding="utf-8-sig",
                           usecols=["Xtf_id", "BeginningOfOperation", "Power", "EnergySource1"])

    unmapped = set(nets["EnergySource1"]) - set(GROUPS)
    if unmapped:
        raise ValueError(f"Energy sources without a group: {unmapped}")
    labels = cats.set_index("Catalogue_id")["EnergySource__en"].str.strip()
    this_year = date.today().year

    power = (nets.dropna(subset=["Power"]).groupby("EnergySource1")["Power"].sum()
             .rename(index=labels).sort_values(ascending=False))
    write_tidy(pd.DataFrame({"year": this_year, "category": power.index, "value": power.round(1).values, "unit": "MW"}),
               "heat/thermal_networks_power_by_source", [path], __name__,
               notes=f"{nets['Power'].notna().sum()} of {len(nets)} networks report their power.")

    dated = nets[nets["BeginningOfOperation"].between(1900, this_year - 1)]
    dated = dated.assign(year=dated["BeginningOfOperation"].astype(int), group=dated["EnergySource1"].map(GROUPS))
    order = list(dict.fromkeys(GROUPS.values()))
    wide = (dated.pivot_table(index="year", columns="group", values="Xtf_id", aggfunc="count")
            .reindex(index=range(dated["year"].min(), this_year), columns=order).fillna(0)
            .cumsum().loc[FIRST_YEAR:])
    long = wide.reset_index().melt(id_vars="year", var_name="category", value_name="value")
    write_tidy(long.assign(value=long["value"].astype(int), unit="networks"),
               "heat/thermal_networks_by_commissioning", [path], __name__,
               notes=f"{len(dated)} of {len(nets)} networks report a commissioning year.")
