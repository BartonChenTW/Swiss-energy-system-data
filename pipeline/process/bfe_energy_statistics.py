"""SFOE overall energy statistics (energy balance, OGD 115) -> national energy balance indicators.

Input : data/raw/bfe_energy_statistics/ogd115_gest_bilanz.csv
        columns Jahr, Rubrik (balance item), Energietraeger (carrier), TJ
Output: national/final_energy_by_carrier
        national/final_energy_by_sector
        heat/district_heat_by_sector    (final consumption of district heat, Energietraeger "Fernwärme")
        national/gross_energy_by_source       (PJ, "Bruttoverbrauch"; electricity = net trade)
        national/supply_domestic_vs_imports   (PJ, domestic production + net imports = gross consumption)
        national/import_dependency            (% of gross consumption covered by net imports)

Check: Bruttoverbrauch = Inlandproduktion + Import + Export + Lagerveränderung (exports negative).
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
GROSS_SOURCES = {  # Energietraeger -> label for gross energy consumption, in stack order
    "Erdölprodukte": "Oil (crude and products)",
    "Rohöl": "Oil (crude and products)",
    "Kernbrennstoffe": "Nuclear fuel",
    "Wasserkraft": "Hydropower",
    "Gas": "Natural gas",
    "Holzenergie": "Wood",
    "Müll und Industrieabfälle": "Waste",
    "Uebrige erneuerbare Energien": "Other renewables",
    "Kohle": "Coal",
    "Elektrizität": "Electricity trade balance",
    "Fernwärme": "District heating",
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

    gross = bal[bal["Rubrik"] == "Bruttoverbrauch"]
    unmapped = set(gross.loc[gross["TJ"].fillna(0) != 0, "Energietraeger"]) - set(GROSS_SOURCES)
    if unmapped:
        raise ValueError(f"Unmapped carriers in gross consumption: {unmapped}")
    g = to_pj(gross.fillna({"TJ": 0}), "Energietraeger", GROSS_SOURCES)
    g = g[g.groupby("category")["value"].transform(lambda s: s.abs().sum()) > 0]  # drop always-zero carriers
    write_tidy(g, "national/gross_energy_by_source", [path], __name__)

    t = bal.fillna({"TJ": 0}).pivot_table(index="Jahr", columns="Rubrik", values="TJ", aggfunc="sum")
    gap = t["Bruttoverbrauch"] - (t["Inlandproduktion"] + t["Import"] + t["Export"] + t["Lagerveränderung"])
    if gap.abs().max() > 1:
        raise ValueError(f"Energy balance no longer closes (TJ):\n{gap[gap.abs() > 1]}")
    net_imports = t["Bruttoverbrauch"] - t["Inlandproduktion"]  # imports - exports ± stock changes
    supply = pd.DataFrame({"Domestic production": t["Inlandproduktion"], "Net imports": net_imports}) / 1000
    long = supply.reset_index().melt(id_vars="Jahr", var_name="category", value_name="value").sort_values("Jahr", kind="stable")
    write_tidy(pd.DataFrame({"year": long["Jahr"], "category": long["category"], "value": long["value"].round(2),
                             "unit": "PJ"}), "national/supply_domestic_vs_imports", [path], __name__)

    share = (net_imports / t["Bruttoverbrauch"] * 100).round(1)
    write_tidy(pd.DataFrame({"year": share.index, "category": "Net imports", "value": share.values,
                             "unit": "% of gross consumption"}), "national/import_dependency", [path], __name__)
