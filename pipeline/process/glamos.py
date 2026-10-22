"""GLAMOS glacier mass balance and length change -> glacier charts.

Input : data/raw/glamos/massbalance_fixdate.csv
        glacier name, end date of observation, annual mass balance (mm w.e., hydrological year Oct–Sep)
        data/raw/glamos/lengthchange.csv
        glacier name, end date of observation, length change (m, between two surveys)
Output: renewables/glacier_mass_balance   (m w.e.: cumulative mass balance since 1915 of the two complete century-long series)
        renewables/glacier_length_change  (km: cumulative length change since 1880 of four large glaciers)

Both files start with a licence header and three header rows (names, codes, units); the last
column (observer) contains unquoted commas, so only the leading columns are read.
Years are those in which the hydrological year or survey interval ends. Length changes are
summed over consecutive survey intervals; a year without a survey is left empty.
"""
import csv

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "glamos"
MASS = RAW_DIR / SOURCE_ID / "massbalance_fixdate.csv"
LENGTH = RAW_DIR / SOURCE_ID / "lengthchange.csv"

MASS_GLACIERS = {  # GLAMOS name -> label; every year since 1915 (Claridenfirn lacks 1994–1995)
    "Grosser Aletschgletscher": "Great Aletsch", "Silvrettagletscher": "Silvretta",
}
MASS_START = 1915
LENGTH_GLACIERS = {  # the largest glaciers with surveys since about 1880
    "Grosser Aletschgletscher": "Great Aletsch", "Vadret da Morteratsch": "Morteratsch",
    "Rhonegletscher": "Rhone", "Glacier du Trient": "Trient",
}


def read_glamos(path, columns: int) -> pd.DataFrame:
    """The table below the licence header, with the first `columns` fields of each row."""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head = next(i for i, r in enumerate(rows) if r and r[0] == "glacier name")
    data = [r[:columns] for r in rows[head + 3:] if len(r) >= columns]
    df = pd.DataFrame(data, columns=rows[head][:columns])
    df["year"] = df["end date of observation"].str[:4].astype(int)
    return df


def run() -> None:
    if not MASS.exists() or not LENGTH.exists():
        print(f"  GLAMOS files not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return

    mb = read_glamos(MASS, 13)
    mb = mb[mb["glacier name"].isin(MASS_GLACIERS) & (mb["year"] >= MASS_START)]
    mb["value"] = pd.to_numeric(mb["annual mass balance"]) / 1000
    years = range(MASS_START, int(mb["year"].max()) + 1)
    wide = mb.pivot(index="year", columns="glacier name", values="value").reindex(index=years, columns=list(MASS_GLACIERS))
    if wide.isna().any().any():
        raise ValueError(f"Gaps in the mass balance series:\n{wide[wide.isna().any(axis=1)]}")
    cum = wide.cumsum().round(2).rename(columns=MASS_GLACIERS)
    tidy = cum.reset_index().melt(id_vars="year", var_name="category", value_name="value")
    tidy["unit"] = "m w.e."
    write_tidy(tidy, "renewables/glacier_mass_balance", [MASS], __name__,
               notes=f"Cumulative {MASS_START}–{max(years)}: " + ", ".join(f"{k} {v:.1f} m w.e." for k, v in cum.iloc[-1].items()))

    lc = read_glamos(LENGTH, 9)
    lc = lc[lc["glacier name"].isin(LENGTH_GLACIERS)]
    lc["dL"] = pd.to_numeric(lc["length change"], errors="coerce")
    frames = []
    for name, g in lc.dropna(subset=["dL"]).sort_values("year").groupby("glacier name"):
        g = g.groupby("year")["dL"].sum()  # several surveys ending in the same year
        frames.append(pd.DataFrame({"year": g.index, "category": LENGTH_GLACIERS[name],
                                    "value": (g.cumsum() / 1000).round(3).values}))
    tidy = pd.concat(frames)
    tidy["category"] = pd.Categorical(tidy["category"], list(LENGTH_GLACIERS.values()), ordered=True)
    tidy = tidy.sort_values(["category", "year"])
    tidy["category"] = tidy["category"].astype(str)
    tidy["unit"] = "km"
    last = tidy.groupby("category").last()
    write_tidy(tidy, "renewables/glacier_length_change", [LENGTH], __name__,
               notes="Cumulative to the latest survey: " + ", ".join(f"{k} {v.value:.2f} km ({v.year})" for k, v in last.iterrows()))
