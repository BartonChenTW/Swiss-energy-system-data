"""Das Gebäudeprogramm project records (OGD 128) -> heating replacements and insulated area.

Input : data/raw/bfe_gebaeudeprogramm_projects/ogd128_GebPrograme_rohdaten_Kanton_direktmassnahmen.csv
        one row per subsidised direct measure, 2017 onwards
Output: buildings/gp_heating_replaced_old   (projects per commitment year, by old heating system)
        buildings/gp_heating_replaced_new   (same projects, by new heating system)
        buildings/gp_insulated_area         (thousand m² insulated per commitment year, by element)

A heating replacement is a project whose main heating system after the measure differs
from the one before (after grouping all heat pump types together). The latest
commitment year still contains provisional (PROV) records.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_gebaeudeprogramm_projects"
FILE = "ogd128_GebPrograme_rohdaten_Kanton_direktmassnahmen.csv"

SYSTEMS = {
    "OEL": "Oil", "GAS": "Gas", "EL": "Electric (direct)",
    "WP": "Heat pump", "LW-WP": "Heat pump", "SW-WP": "Heat pump", "WW-WP": "Heat pump",
    "HOLZ": "Wood", "FW": "District heating",
    "SOLAR": "Other", "BIOGAS": "Other", "SONST": "Other",
}
SYSTEM_ORDER = ["Oil", "Gas", "Electric (direct)", "Heat pump", "Wood", "District heating", "Other"]

INSULATION = {
    "Waermegedaemmte_Flaeche_Dach_m2": "Roof",
    "Waermegedaemmte_Flaeche_Fassade_m2": "Facade",
    "Waermegedaemmte_Flaeche_Wand_und_Boden_gegen_Erdreich_m2": "Walls & floors against ground",
}


def counts_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    n = df.groupby(["Jahr_Verpflichtung", col]).size().unstack(fill_value=0)
    n = n.reindex(columns=[c for c in SYSTEM_ORDER if c in n.columns])
    n = n.loc[:, n.sum() > 0]
    long = n.reset_index().melt(id_vars="Jahr_Verpflichtung", var_name="category", value_name="value")
    order = {c: i for i, c in enumerate(SYSTEM_ORDER)}
    long = long.sort_values(["Jahr_Verpflichtung", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    return pd.DataFrame({"year": long["Jahr_Verpflichtung"], "category": long["category"],
                         "value": long["value"], "unit": "projects"})


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    cols = ["Status", "Jahr_Verpflichtung", "Heizsystem_vor_Massnahme", "Heizsystem_nach_Massnahme", *INSULATION]
    p = pd.read_csv(path, encoding="utf-8-sig", usecols=cols, low_memory=False)

    unknown = (set(p["Heizsystem_vor_Massnahme"].dropna()) | set(p["Heizsystem_nach_Massnahme"].dropna())) - set(SYSTEMS)
    if unknown:
        raise ValueError(f"Unmapped heating system codes: {unknown}")
    p["old"] = p["Heizsystem_vor_Massnahme"].map(SYSTEMS)
    p["new"] = p["Heizsystem_nach_Massnahme"].map(SYSTEMS)
    swaps = p.dropna(subset=["old", "new"])
    swaps = swaps[swaps["old"] != swaps["new"]]

    last = int(p["Jahr_Verpflichtung"].max())
    prov = int((p.loc[p["Jahr_Verpflichtung"] == last, "Status"] == "PROV").sum())
    note = f"{len(swaps):,} subsidised heating replacements {int(p['Jahr_Verpflichtung'].min())}–{last}; {prov:,} records in {last} are provisional."
    write_tidy(counts_by(swaps, "old"), "buildings/gp_heating_replaced_old", [path], __name__, notes=note)
    write_tidy(counts_by(swaps, "new"), "buildings/gp_heating_replaced_new", [path], __name__, notes=note)

    area = p.groupby("Jahr_Verpflichtung")[list(INSULATION)].sum().rename(columns=INSULATION) / 1000
    long = area.reset_index().melt(id_vars="Jahr_Verpflichtung", var_name="category", value_name="value")
    order = {c: i for i, c in enumerate(INSULATION.values())}
    long = long.sort_values(["Jahr_Verpflichtung", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    write_tidy(pd.DataFrame({"year": long["Jahr_Verpflichtung"], "category": long["category"],
                             "value": long["value"].round(1), "unit": "thousand m²"}),
               "buildings/gp_insulated_area", [path], __name__,
               notes=f"{last} includes provisional records.")
