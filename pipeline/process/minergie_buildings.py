"""Minergie buildings per municipality (OGD 91) -> Minergie-certified buildings per 1,000 buildings, by canton.

Input : data/raw/minergie_buildings/ogd91_minergiegebaeude_pro_gemeinde.csv
        BfsNumber + counts per label (Minergie, -Eco, -A, -A-Eco, -P, -P-Eco)
        data/raw/bfs_gwr/ch.zip  (municipality -> canton, and existing buildings per canton)
Output: buildings/minergie_per_1000_buildings  (snapshot, by canton)

Municipality numbers not found in the current GWR (e.g. after mergers) are reported in the notes.
"""
import zipfile

import pandas as pd

from ..common import RAW_DIR, input_record, write_tidy

SOURCE_ID = "minergie_buildings"
FILE = "ogd91_minergiegebaeude_pro_gemeinde.csv"
GWR = RAW_DIR / "bfs_gwr" / "ch.zip"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists() or not GWR.exists():
        print(f"  {FILE} or GWR not found, run: python -m pipeline.fetch --source {SOURCE_ID} --source bfs_gwr")
        return
    m = pd.read_csv(path, encoding="utf-8-sig")
    labels = [c for c in m.columns if c.startswith("Minergie")]
    m["n"] = m[labels].sum(axis=1)

    with zipfile.ZipFile(GWR) as zf:
        b = pd.read_csv(zf.open("gebaeude_batiment_edificio.csv"), sep="\t", dtype=str,
                        usecols=["GGDENR", "GDEKT", "GSTAT"])
    existing = b[b["GSTAT"] == "1004"]
    canton_of = existing.drop_duplicates("GGDENR").set_index("GGDENR")["GDEKT"]
    m["canton"] = m["BfsNumber"].astype(str).map(canton_of)
    unmatched = m[m["canton"].isna()]

    per = (m.groupby("canton")["n"].sum() / existing.groupby("GDEKT").size() * 1000).dropna().sort_values(ascending=False)
    year = int(input_record(path)["retrieved"][:4])  # snapshot: the year it was retrieved
    write_tidy(pd.DataFrame({"year": year, "category": per.index, "value": per.round(1).values,
                             "unit": "per 1,000 buildings"}), "buildings/minergie_per_1000_buildings",
               [path, GWR], __name__,
               notes=f"{int(m['n'].sum()):,} Minergie buildings in the dataset "
                     f"({int(unmatched['n'].sum()):,} in {len(unmatched)} municipality numbers not in the current GWR). "
                     f"Minergie itself reports ~60,500 certified buildings, so the dataset is incomplete.")
