"""SFOE overall energy statistics (energy balance, OGD 115) -> final energy consumption.

Input : data/raw/bfe_energy_statistics/ogd115_gest_bilanz.csv
        columns Jahr, Rubrik (balance item), Energietraeger (carrier), TJ
Output: national/final_energy_by_carrier
        national/final_energy_by_sector
        heat/district_heat_by_sector    (final consumption of district heat, Energietraeger "Fernwärme")
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_energy_statistics"
FILE = "ogd115_gest_bilanz.csv"

CARRIERS = {  # Energietraeger -> label, in legend order
    "Erdölprodukte": "Oil products",
    "Elektrizität": "Electricity",
    "Gas": "Natural gas",
    "Holzenergie": "Wood",
    "Fernwärme": "District heating",
    "Uebrige erneuerbare Energien": "Other renewables",
    "Kohle": "Coal & waste",
    "Müll und Industrieabfälle": "Coal & waste",
}
SECTORS = {  # Rubrik -> label
    "Endverbrauch - Haushalte": "Households",
    "Endverbrauch - Dienstleistungen": "Services",
    "Endverbrauch - Industrie": "Industry",
    "Endverbrauch - Verkehr": "Transport",
    "Endverbrauch - Statistische Differenz inkl. Landwirtschaft": "Agriculture & statistical difference",
}


def to_pj(df: pd.DataFrame, key: str, labels: dict) -> pd.DataFrame:
    df = df.assign(category=df[key].map(labels)).dropna(subset=["category"])
    out = df.groupby(["Jahr", "category"], sort=False)["TJ"].sum().reset_index()
    order = {c: i for i, c in enumerate(dict.fromkeys(labels.values()))}
    out = out.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    return pd.DataFrame({"year": out["Jahr"], "category": out["category"], "value": (out["TJ"] / 1000).round(2), "unit": "PJ"})


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    bal = pd.read_csv(path, encoding="utf-8-sig")

    total = bal[bal["Rubrik"] == "Endverbrauch - Total"]
    unmapped = set(total.loc[total["TJ"].fillna(0) != 0, "Energietraeger"]) - set(CARRIERS)
    if unmapped:
        raise ValueError(f"Unmapped carriers with final consumption: {unmapped}")
    write_tidy(to_pj(total, "Energietraeger", CARRIERS), "national/final_energy_by_carrier", [path], __name__)

    sectors = bal[bal["Rubrik"].isin(SECTORS)]
    write_tidy(to_pj(sectors, "Rubrik", SECTORS), "national/final_energy_by_sector", [path], __name__)

    district_heat = sectors[sectors["Energietraeger"] == "Fernwärme"]
    by_sector = to_pj(district_heat, "Rubrik", SECTORS)
    by_sector = by_sector[by_sector.groupby("category")["value"].transform("sum") > 0]  # no district heat in transport
    write_tidy(by_sector, "heat/district_heat_by_sector", [path], __name__)
