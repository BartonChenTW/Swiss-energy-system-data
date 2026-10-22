"""SFOE monthly electricity balance (OGD 35) -> monthly hydropower production and pumping.

Input : data/raw/bfe_electricity_monthly/ogd35_schweizerische_elektrizitaetsbilanz_monatswerte.csv
        Jahr, Monat, Definitiv (0 = provisional), Erzeugung_Laufwerk_GWh, Erzeugung_Speicherwerk_GWh,
        Verbrauch_Speicherpumpen_GWh (monthly from 2000)
Output: electricity/hydro_monthly   (GWh per month: run-of-river, storage plants, storage pumps)

Storage production includes the output of pumped-storage plants; the pumps' consumption is shown
separately, so storage minus pumping approximates the net contribution of storage plants.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_electricity_monthly"
FILE = "ogd35_schweizerische_elektrizitaetsbilanz_monatswerte.csv"
COLUMNS = {
    "Erzeugung_Laufwerk_GWh": "Run-of-river",
    "Erzeugung_Speicherwerk_GWh": "Storage plants",
    "Verbrauch_Speicherpumpen_GWh": "Storage pumps (consumption)",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    d = pd.read_csv(path, na_values="NULL")
    d["period"] = d["Jahr"].astype(str) + "-" + d["Monat"].map("{:02d}".format)
    tidy = d.melt(id_vars="period", value_vars=list(COLUMNS), var_name="category")
    tidy["category"] = tidy["category"].map(COLUMNS)
    tidy["unit"] = "GWh"
    provisional = d.loc[d["Definitiv"] == 0, "period"]
    write_tidy(tidy, "electricity/hydro_monthly", [path], __name__,
               notes=f"Provisional: {provisional.min()} to {provisional.max()}." if len(provisional) else None)
