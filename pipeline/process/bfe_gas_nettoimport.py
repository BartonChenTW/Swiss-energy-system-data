"""SFOE / VSG monthly net imports of natural gas (OGD 111) -> supply/gas_net_imports_monthly.

Input : data/raw/bfe_gas_nettoimport/ogd111_gas_nettoimport.csv   (Jahr, Monat, Importierte_Energie_GWh)
Output: supply/gas_net_imports_monthly   (TWh per month)
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_gas_nettoimport"
FILE = "ogd111_gas_nettoimport.csv"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    d = pd.read_csv(path).dropna(subset=["Importierte_Energie_GWh"])
    tidy = pd.DataFrame({
        "period": d["Jahr"].astype(int).astype(str) + "-" + d["Monat"].astype(int).map("{:02d}".format),
        "category": "Net imports",
        "value": (d["Importierte_Energie_GWh"] / 1000).round(3),
        "unit": "TWh",
    })
    write_tidy(tidy, "supply/gas_net_imports_monthly", [path], __name__)
