"""SFOE energy dashboard gas storage levels (OGD 102) -> supply/gas_storage_fill.

Input : data/raw/bfe_gas_storage_eu/ogd102_fuellstand_gasspeicher.csv
        (Datum daily, Speicherregion, Speicherstand_TWh, Lagerkapazitaet_prozent)
Output: supply/gas_storage_fill    (% of capacity, weekly on Mondays, EU and the countries around Switzerland)
        supply/gas_storage_level   (TWh stored, same points)

Switzerland has no large gas storage, so the filling of the storage in its neighbours is what matters for winter.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_gas_storage_eu"
FILE = "ogd102_fuellstand_gasspeicher.csv"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    d = pd.read_csv(path, parse_dates=["Datum"]).dropna(subset=["Lagerkapazitaet_prozent"])
    d = d[d["Datum"].dt.dayofweek == 0]  # weekly points keep the file small
    notes = f"Last Monday in the file: {d['Datum'].max():%d %b %Y}."
    for dataset_id, column, unit in [
        ("supply/gas_storage_fill", "Lagerkapazitaet_prozent", "% of capacity"),
        ("supply/gas_storage_level", "Speicherstand_TWh", "TWh"),
    ]:
        tidy = pd.DataFrame({
            "period": d["Datum"].dt.strftime("%Y-%m-%d"),
            "category": d["Speicherregion"],
            "value": d[column].round(1),
            "unit": unit,
        })
        write_tidy(tidy, dataset_id, [path], __name__, notes=notes)
