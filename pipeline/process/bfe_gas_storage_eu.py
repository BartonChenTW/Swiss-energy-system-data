"""SFOE energy dashboard gas storage levels (OGD 102) -> supply/gas_storage_fill.

Input : data/raw/bfe_gas_storage_eu/ogd102_fuellstand_gasspeicher.csv
        (Datum daily, Speicherregion, Speicherstand_TWh, Lagerkapazitaet_prozent)
Output: supply/gas_storage_fill   (% of capacity, weekly on Mondays, EU and the countries around Switzerland)

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
    tidy = pd.DataFrame({
        "period": d["Datum"].dt.strftime("%Y-%m-%d"),
        "category": d["Speicherregion"],
        "value": d["Lagerkapazitaet_prozent"].round(1),
        "unit": "% of capacity",
    })
    last = d["Datum"].max()
    write_tidy(tidy, "supply/gas_storage_fill", [path], __name__, notes=f"Last Monday in the file: {last:%d %b %Y}.")
