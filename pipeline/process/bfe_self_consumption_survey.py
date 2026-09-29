"""SFOE survey of grid operators on self-consumption (ES2050 monitoring) -> PV by self-consumption type.

Input : data/raw/bfe_self_consumption_survey/bfe_eigenverbrauch_datenblaetter.xlsx
        one sheet per year; row labels in column 0, then count at 31 Dec, AC power (MW), surplus (MWh)
Output: electricity/pv_installations_by_self_consumption  (number of PV installations)
        electricity/pv_capacity_by_self_consumption       (MW AC)

Some sheets store numbers as text with apostrophes as thousands separators ("202'536").
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_self_consumption_survey"
FILE = "bfe_eigenverbrauch_datenblaetter.xlsx"

ROWS = {  # row label -> category, in stack order (bottom first)
    "PV-Anlagen mit Eigenverbrauch (ohne ZEV)": "Self-consumption, single site",
    "PV-Anlagen in ZEV": "In a ZEV (self-consumption community)",
    "PV-Anlagen ohne Eigenverbrauch": "No self-consumption (full feed-in)",
}


def number(v) -> float:
    return float(str(v).replace("'", "").replace("’", "").strip())


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    rows = []
    for sheet, df in pd.read_excel(path, sheet_name=None, header=None).items():
        if not sheet.strip().isdigit():
            continue
        df = df.set_index(df[0].astype(str).str.strip())
        missing = set(ROWS) - set(df.index)
        if missing:
            raise ValueError(f"sheet {sheet}: rows not found {missing}")
        for label, category in ROWS.items():
            rows.append({"year": int(sheet), "category": category,
                         "count": number(df.at[label, 1]), "mw": number(df.at[label, 2])})
    tidy = pd.DataFrame(rows)
    order = {c: i for i, c in enumerate(ROWS.values())}
    tidy = tidy.sort_values(["year", "category"], key=lambda s: s.map(order) if s.name == "category" else s)

    write_tidy(tidy.assign(value=tidy["count"].astype(int), unit="installations"),
               "electricity/pv_installations_by_self_consumption", [path], __name__)
    write_tidy(tidy.assign(value=tidy["mw"].round(0), unit="MW"),
               "electricity/pv_capacity_by_self_consumption", [path], __name__)
