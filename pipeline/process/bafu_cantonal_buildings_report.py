"""Cantonal reporting on buildings (FOEN/SFOE, standard method) -> national building-stock indicators.

Input : data/raw/bafu_cantonal_buildings_report/daten-kantonale-berichterstattung-co2-gebaeude.xlsx
        sheet "Spez. Werte pro Kanton": Kanton, Jahr, kWh/m² EBF, kg CO2/m² EBF (+ per capita); has a CH row
        sheet "Total pro Kanton": Kanton, Energieträger, Jahr, Mt CO2, TWh
Output: buildings/stock_energy_intensity     (kWh per m² energy reference area, CH)
        buildings/stock_co2_intensity        (kg CO2 per m² energy reference area, CH)
        buildings/stock_final_energy_by_carrier  (TWh, sum of cantons)

Scope: households and services, space heating and hot water, weather influence included.
23 cantons use the harmonised standard method, 3 their own.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bafu_cantonal_buildings_report"
FILE = "daten-kantonale-berichterstattung-co2-gebaeude.xlsx"

CARRIERS = {
    "Heizöl": "Heating oil", "Erdgas": "Natural gas",
    "Flüssiggas": "Other fossil (LPG, coal, other)", "Kohle": "Other fossil (LPG, coal, other)",
    "Andere": "Other fossil (LPG, coal, other)",
    "Strom": "Electricity", "Fernwärme": "District heating",
    "Holz/Biomasse": "Biomass (wood, biogas)", "Biogas": "Biomass (wood, biogas)",
    "Solarenergie": "Solar thermal", "Umweltwärme": "Ambient & waste heat", "Abwärme": "Ambient & waste heat",
}


def find_col(df: pd.DataFrame, *words: str) -> str:
    matches = [c for c in df.columns if all(w.lower() in str(c).lower() for w in words)]
    if len(matches) != 1:
        raise ValueError(f"Expected one column containing {words}, found {matches}")
    return matches[0]


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    spec = pd.read_excel(path, sheet_name="Spez. Werte pro Kanton")
    ch = spec[spec["Kanton"].astype(str).str.strip() == "CH"]
    kwh = find_col(spec, "kWh", "m2")
    kg = find_col(spec, "kg CO2", "m2")
    write_tidy(pd.DataFrame({"year": ch["Jahr"], "category": "Switzerland", "value": ch[kwh].round(1),
                             "unit": "kWh/m² ERA"}), "buildings/stock_energy_intensity", [path], __name__)
    write_tidy(pd.DataFrame({"year": ch["Jahr"], "category": "Switzerland", "value": ch[kg].round(2),
                             "unit": "kg CO2/m² ERA"}), "buildings/stock_co2_intensity", [path], __name__)

    tot = pd.read_excel(path, sheet_name="Total pro Kanton")
    tot = tot[tot["Kanton"].astype(str).str.strip() != "CH"]
    unknown = set(tot["Energieträger"].dropna()) - set(CARRIERS)
    if unknown:
        raise ValueError(f"Unmapped carriers: {unknown}")
    twh = find_col(tot, "TWh")
    tot = tot.assign(category=tot["Energieträger"].map(CARRIERS))
    out = tot.groupby(["Jahr", "category"], sort=False)[twh].sum().reset_index()
    order = {c: i for i, c in enumerate(dict.fromkeys(CARRIERS.values()))}
    out = out.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    write_tidy(pd.DataFrame({"year": out["Jahr"], "category": out["category"], "value": out[twh].round(2),
                             "unit": "TWh"}), "buildings/stock_final_energy_by_carrier", [path], __name__,
               notes=f"Sum of {tot['Kanton'].nunique()} cantons.")
