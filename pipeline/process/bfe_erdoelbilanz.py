"""SFOE oil balance (OGD 124) -> yearly change of oil stocks.

Input : data/raw/bfe_erdoelbilanz/ogd124_erdoelbilanz.csv   (Jahr, Rubrik, Energietraeger, Tonnen)
Output: supply/oil_stock_change   (kt, yearly: stock change at wholesalers and at consumers, all products)

The balance has no stock level, only the change: positive when stocks grew. Wholesale stocks include the
mandatory stocks. Tonnes are summed over all products, crude oil included.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_erdoelbilanz"
FILE = "ogd124_erdoelbilanz.csv"
RUBRIKS = {"Lagerveränderung Grosshandel": "Wholesale stocks", "Lagerveränderung Konsumenten": "Consumer stocks"}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    d = pd.read_csv(path, encoding="utf-8", na_values=["NA"])
    d = d[d["Rubrik"].isin(RUBRIKS)]
    if d.empty:
        raise ValueError("No stock change rows found: did the Rubrik names change?")
    tidy = d.groupby(["Jahr", "Rubrik"], as_index=False)["Tonnen"].sum()
    tidy["category"] = tidy["Rubrik"].map(RUBRIKS)
    tidy["value"] = (tidy["Tonnen"] / 1000).round(1)
    tidy = tidy.rename(columns={"Jahr": "year"})
    tidy["unit"] = "kt"
    write_tidy(tidy, "supply/oil_stock_change", [path], __name__,
               notes="Positive = stocks grew. Stock levels are not part of the SFOE oil balance.")
