"""Lucerne public GEAK certificates -> envelope efficiency class of existing buildings by year issued.

Input : data/raw/lu_geak/geak_luzern.json  (ArcGIS REST query result, one feature per certificate)
        BEW_HUELLE = envelope class A–G (99 = unknown), GEAK_TYP (3 = GEAK for new buildings),
        DATEOFCREA = issue date (epoch ms)
Output: buildings/luzern_geak_envelope_class  (certificates per year, by envelope class)

Certificates for new buildings are excluded so the chart describes the existing stock.
The current calendar year is dropped because it is incomplete.
"""
import json
from datetime import date

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "lu_geak"
FILE = "geak_luzern.json"
NEW_BUILDING = 3
CLASSES = list("ABCDEFG")


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    res = json.loads(path.read_text(encoding="utf-8"))
    if res.get("exceededTransferLimit"):
        raise ValueError("ArcGIS query hit the record limit; add paging to the download")
    g = pd.DataFrame([f["attributes"] for f in res["features"]])
    g["year"] = pd.to_datetime(g["DATEOFCREA"], unit="ms").dt.year
    existing = g[(g["GEAK_TYP"] != NEW_BUILDING) & g["BEW_HUELLE"].isin(CLASSES) & (g["year"] < date.today().year)]

    n = existing.groupby(["year", "BEW_HUELLE"]).size().unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
    long = n.reset_index().melt(id_vars="year", var_name="cls", value_name="value").sort_values(["year", "cls"])
    write_tidy(pd.DataFrame({"year": long["year"], "category": "Class " + long["cls"], "value": long["value"],
                             "unit": "certificates"}), "buildings/luzern_geak_envelope_class", [path], __name__,
               notes=f"{len(existing):,} certificates for existing buildings; "
                     f"{(g['GEAK_TYP'] == NEW_BUILDING).sum():,} new-building certificates excluded.")
