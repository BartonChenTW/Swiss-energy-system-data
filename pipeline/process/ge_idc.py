"""Geneva heat energy index (IDC, OCEN/SITG) -> measured heat demand per m², residential vs other.

Input : data/raw/ge_idc/SCANE_INDICE_MOYENNES_3_ANS-CSV.zip
        SCANE_INDICE_MOYENNES_3_ANS.csv (;-separated): EGID, DESTINATION, ANNEE, SRE (m²), INDICE (MJ/m²·a)
Output: buildings/geneva_heat_index  (kWh/m²·a, floor-area-weighted mean per year)

Weighted mean = sum(INDICE × SRE) / sum(SRE), converted with 3.6 MJ = 1 kWh.
Years with fewer than 80% of the median number of reports (early years, current year) are dropped.
"""
import zipfile

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "ge_idc"
FILE = "SCANE_INDICE_MOYENNES_3_ANS-CSV.zip"
MEMBER = "SCANE_INDICE_MOYENNES_3_ANS.csv"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        d = pd.read_csv(zf.open(MEMBER), sep=";", usecols=["EGID", "DESTINATION", "ANNEE", "SRE", "INDICE"])
    d = d[(d["SRE"] > 0) & (d["INDICE"] > 0)]
    counts = d.groupby("ANNEE").size()
    years = counts[counts >= 0.8 * counts.median()].index
    d = d[d["ANNEE"].isin(years)]
    d["category"] = d["DESTINATION"].fillna("").str.startswith("Hab").map({True: "Residential", False: "Non-residential"})
    d["w"] = d["INDICE"] * d["SRE"]
    g = d.groupby(["ANNEE", "category"])[["w", "SRE"]].sum()
    out = (g["w"] / g["SRE"] / 3.6).round(1).reset_index(name="value")
    out = out.sort_values(["ANNEE", "category"], ascending=[True, False])  # Residential first in legends
    write_tidy(pd.DataFrame({"year": out["ANNEE"], "category": out["category"], "value": out["value"],
                             "unit": "kWh/m²·a"}), "buildings/geneva_heat_index", [path], __name__,
               notes=f"~{int(counts.loc[years].median()):,} buildings report per year.")
