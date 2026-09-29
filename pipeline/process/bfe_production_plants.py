"""SFOE register of electricity production plants -> installed renewable capacity.

Input : data/raw/bfe_production_plants/ch.bfe.elektrizitaetsproduktionsanlagen.zip
        ElectricityProductionPlant.csv (BeginningOfOperation, TotalPower [kW], SubCategory,
                                        Municipality, Canton, _x/_y in LV95)
        SubCategoryCatalogue.csv (subcat_2 = Photovoltaik, subcat_3 = Windenergie, subcat_4 = Biomasse)
Output: renewables/pv_installed_capacity             (MW, cumulative by commissioning year)
        renewables/wind_biomass_installed_capacity   (MW, cumulative by commissioning year)
        renewables/wind_farms                        (MW per wind farm, current register)

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
SITE_RADIUS_M = 3000  # turbines closer than this form one wind farm (LV95 metres)
SITE_MIN_MW = 0.5     # smaller sites are summed into one bar


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
                             usecols=["BeginningOfOperation", "TotalPower", "SubCategory", "Municipality", "Canton", "_x", "_y"])

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

    turbines = plants[plants["label"] == "Wind"]
    sites = wind_sites(turbines)
    small = sites["mw"] < SITE_MIN_MW
    label = sites["name"] + " · " + sites["turbines"].map(lambda n: f"{n} turbine{'s' * (n > 1)}") + " · " + sites["years"]
    rows = pd.concat([
        pd.DataFrame({"category": label[~small], "value": sites.loc[~small, "mw"]}),
        pd.DataFrame({"category": [f"{small.sum()} small sites under {SITE_MIN_MW:g} MW"], "value": [sites.loc[small, "mw"].sum()]}),
    ])
    write_tidy(rows.assign(year=date.today().year, value=rows["value"].round(2), unit="MW"),
               "renewables/wind_farms", [path], __name__,
               notes=f"{len(turbines)} wind plants grouped into {len(sites)} sites (turbines within {SITE_RADIUS_M / 1000:g} km).")


def wind_sites(turbines: pd.DataFrame) -> pd.DataFrame:
    """Group turbines into sites: within SITE_RADIUS_M of each other, or same municipality if unlocated.

    The register has no wind farm names, so a site is named after its most common
    municipality. Returns one row per site, largest first.
    """
    t = turbines.reset_index(drop=True)
    parent = list(range(len(t)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    located = t["_x"].notna() & t["_y"].notna()
    for i in range(len(t)):
        for j in range(i):
            if located[i] and located[j]:
                near = ((t.at[i, "_x"] - t.at[j, "_x"]) ** 2 + (t.at[i, "_y"] - t.at[j, "_y"]) ** 2) ** 0.5 < SITE_RADIUS_M
            else:
                near = t.at[i, "Municipality"] == t.at[j, "Municipality"]
            if near:
                parent[root(i)] = root(j)

    t = t.assign(site=[root(i) for i in range(len(t))])
    sites = t.groupby("site").agg(
        mw=("TotalPower", lambda s: s.sum() / 1000),
        turbines=("TotalPower", "size"),
        first=("year", "min"),
        last=("year", "max"),
        municipality=("Municipality", lambda s: s.mode().iloc[0]),
        canton=("Canton", lambda s: s.mode().iloc[0]),
    ).sort_values("mw", ascending=False)
    sites["name"] = sites["municipality"] + " (" + sites["canton"] + ")"
    sites["years"] = [f"{a:.0f}" if a == b else f"{a:.0f}–{b:.0f}" for a, b in zip(sites["first"], sites["last"])]
    return sites
