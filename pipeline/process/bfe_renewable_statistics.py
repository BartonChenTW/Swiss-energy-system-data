"""SFOE energy balance of renewables (OGD 123) -> domestic renewable production by source.

Input : data/raw/bfe_renewable_statistics/ogd123_Energiebilanz_erneuerbareEnergien.csv
        columns Jahr, Rubrik (balance item), Energietraeger (carrier), TJ
Output: renewables/production_by_source  (PJ, Rubrik "Inlandproduktion", from 1990)
        heat/renewable_district_heat_by_source  (PJ, Energietraeger "Erneuerbare Fernwärme")

"Sonne" covers both PV and solar thermal; "Umweltwärme" is ambient heat used by heat pumps.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_renewable_statistics"
FILE = "ogd123_Energiebilanz_erneuerbareEnergien.csv"

SOURCES = {  # Energietraeger -> label, in stack order (bottom first)
    "Wasserkraft": "Hydropower",
    "Holzenergie": "Wood",
    "Sonne": "Solar (PV and thermal)",
    "Umweltwärme": "Ambient heat (heat pumps)",
    "Erneuerbarer Müll und Industrieabfälle": "Renewable share of waste",
    "Biogas": "Biogas",
    "flüssige eTS/eBS": "Liquid biofuels",
    "Wind": "Wind",
}
DISTRICT_HEAT = {  # Rubrik producing "Erneuerbare Fernwärme" -> label, in stack order
    "Energieumwandlung - Kehrichtverbrennungsanlagen": "Waste incineration (renewable share)",
    "Energieumwandlung - Automatische Feuerungen mit Holz (Fernwärme-Produktion)": "Wood",
    "Energieumwandlung - Feuerungen mit Holzanteilen (Fernwärme-Produktion)": "Wood",
    "Energieumwandlung - Deponiegasanlagen": "Landfill gas",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    bal = pd.read_csv(path, encoding="utf-8-sig")
    prod = bal[bal["Rubrik"] == "Inlandproduktion"]

    unmapped = set(prod.loc[prod["TJ"].fillna(0) != 0, "Energietraeger"]) - set(SOURCES)
    if unmapped:
        raise ValueError(f"Unmapped carriers with domestic production: {unmapped}")

    prod = prod.assign(category=prod["Energietraeger"].map(SOURCES)).dropna(subset=["category"])
    order = {c: i for i, c in enumerate(SOURCES.values())}
    prod = prod.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    tidy = pd.DataFrame({"year": prod["Jahr"], "category": prod["category"],
                         "value": (prod["TJ"].fillna(0) / 1000).round(3), "unit": "PJ"})
    write_tidy(tidy, "renewables/production_by_source", [path], __name__)

    dh = bal[(bal["Energietraeger"] == "Erneuerbare Fernwärme") & bal["Rubrik"].str.startswith("Energieumwandlung")]
    unmapped = set(dh.loc[dh["TJ"].fillna(0) > 0, "Rubrik"]) - set(DISTRICT_HEAT)
    if unmapped:
        raise ValueError(f"Unmapped plants producing renewable district heat: {unmapped}")
    dh = dh.assign(category=dh["Rubrik"].map(DISTRICT_HEAT)).dropna(subset=["category"])
    dh = dh.groupby(["Jahr", "category"], sort=False)["TJ"].sum().reset_index()
    order = {c: i for i, c in enumerate(dict.fromkeys(DISTRICT_HEAT.values()))}
    dh = dh.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    write_tidy(pd.DataFrame({"year": dh["Jahr"], "category": dh["category"],
                             "value": (dh["TJ"].fillna(0) / 1000).round(3), "unit": "PJ"}),
               "heat/renewable_district_heat_by_source", [path], __name__)
