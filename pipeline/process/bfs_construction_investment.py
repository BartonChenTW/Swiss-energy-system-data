"""FSO construction investment (PXWeb px-x-0904010000_205) -> residential new build vs Umbau.

Input : data/raw/bfs_construction_investment/px-x-0904010000_205_wohnen_ch.csv
        PXWeb CSV: one row per Art der Arbeiten, one column per year, values in 1000 CHF
Output: buildings/residential_construction_investment  (billion CHF, current prices)

"Umbau" covers conversion, extension, renovation, refurbishment and demolition; energy
retrofits are part of it but cannot be separated.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfs_construction_investment"
FILE = "px-x-0904010000_205_wohnen_ch.csv"
WORKS = {"Umbau": "Conversion & renovation (Umbau)", "Neubau": "New construction"}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    wide = pd.read_csv(path, encoding="utf-8-sig", encoding_errors="replace")
    wide = wide.set_index("Art der Arbeiten")[[c for c in wide.columns if c.isdigit()]]
    missing = set(WORKS) - set(wide.index)
    if missing:
        raise ValueError(f"Missing rows in PXWeb response: {missing}")
    long = wide.loc[list(WORKS)].T.stack().reset_index()
    long.columns = ["year", "works", "kCHF"]
    long["year"] = long["year"].astype(int)
    tidy = pd.DataFrame({"year": long["year"], "category": long["works"].map(WORKS),
                         "value": (pd.to_numeric(long["kCHF"]) / 1e6).round(3), "unit": "billion CHF"})
    write_tidy(tidy.sort_values(["year"], kind="stable"), "buildings/residential_construction_investment", [path], __name__)
