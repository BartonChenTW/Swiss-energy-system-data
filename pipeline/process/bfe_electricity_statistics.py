"""SFOE electricity statistics (annual electricity balance, OGD 32) -> production by technology.

Input : data/raw/bfe_electricity_statistics/ogd32_elektrizitaetbilanz_jahreswerte.csv
        one row per year, columns in GWh
Output: electricity/production_by_technology  (TWh, from 1990 when the full breakdown starts)

Check: the production columns minus Verbrauch_speicherpumpen_GWh equal
Erzeugung_netto_GWh (Erzeugung_andere_total = fossil + waste; wood and biogas are separate).
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_electricity_statistics"
FILE = "ogd32_elektrizitaetbilanz_jahreswerte.csv"
FIRST_YEAR = 1990

TECHNOLOGIES = {  # column -> label, in stack order (bottom first)
    "Erzeugung_laufwerk_GWh": "Run-of-river hydro",
    "Erzeugung_speicherwerk_GWh": "Storage hydro",
    "Erzeugung_kernkraftwerk_GWh": "Nuclear",
    "Erzeugung_andere_fossil_GWh": "Fossil thermal",
    "Erzeugung_andere_erneuerbare_abfaelle_GWh": "Waste (renewable share)",
    "Erzeugung_holz_GWh": "Wood & biogas",
    "Erzeugung_biogas_GWh": "Wood & biogas",
    "Erzeugung_photovoltaik_GWh": "Solar PV",
    "Erzeugung_wind_GWh": "Wind",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    bal = pd.read_csv(path, encoding="utf-8-sig")
    bal = bal[bal["Jahr"] >= FIRST_YEAR].set_index("Jahr")

    gap = bal[list(TECHNOLOGIES)].sum(axis=1) - bal["Verbrauch_speicherpumpen_GWh"] - bal["Erzeugung_netto_GWh"]
    if gap.abs().max() > 5:
        raise ValueError(f"Production columns no longer add up to net production:\n{gap[gap.abs() > 5]}")

    long = (bal[list(TECHNOLOGIES)].rename(columns=TECHNOLOGIES)
            .T.groupby(level=0, sort=False).sum().T
            .reset_index().melt(id_vars="Jahr", var_name="category", value_name="GWh"))
    order = {c: i for i, c in enumerate(dict.fromkeys(TECHNOLOGIES.values()))}
    long = long.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    tidy = pd.DataFrame({"year": long["Jahr"], "category": long["category"],
                         "value": (long["GWh"] / 1000).round(3), "unit": "TWh"})
    write_tidy(tidy, "electricity/production_by_technology", [path], __name__)
