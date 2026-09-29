"""FOEN greenhouse gas inventory (LINDAS cube ubd000502) -> national emissions by sector and by gas.

Input : data/raw/foen_ghg_inventory/ghg_inventory_ubd000502_v8.csv
        columns sector, gas (vocabulary URIs; the last path segment is the code), year, value (Mt CO2-eq)
Output: emissions/ghg_by_sector   (sectors of the CO2 Ordinance, all greenhouse gases)
        emissions/ghg_by_gas      (national total by gas)

Sector 1 is the national total. International aviation (2) and the land-use balance (3) are
reported outside it and left out here. The sectors must add up to the total.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "foen_ghg_inventory"
FILE = "ghg_inventory_ubd000502_v8.csv"
TOTAL_SECTOR, ALL_GASES = "1", "test1"

SECTORS = {  # sector code -> label, in stack order (bottom first)
    "11": "Buildings",
    "12": "Transport",
    "13": "Industry (incl. waste incineration)",
    "141": "Agriculture",
    "142": "Waste",
    "143": "Synthetic gases",
}
GASES = {"pol9": "Carbon dioxide (CO2)", "pol11": "Methane (CH4)", "pol12": "Nitrous oxide (N2O)", "polgroup2": "Synthetic gases"}


def ordered(df: pd.DataFrame, key: str, labels: dict) -> pd.DataFrame:
    df = df[df[key].isin(labels)].assign(category=lambda d: d[key].map(labels))
    order = {c: i for i, c in enumerate(labels.values())}
    df = df.sort_values(["year", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    return pd.DataFrame({"year": df["year"], "category": df["category"], "value": df["value"].round(3), "unit": "Mt CO2-eq"})


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    raw = pd.read_csv(path)
    raw["sector"] = raw["sector"].str.rsplit("/", n=1).str[-1]
    raw["gas"] = raw["gas"].str.rsplit("/", n=1).str[-1]

    all_gases = raw[raw["gas"] == ALL_GASES]
    total = all_gases[all_gases["sector"] == TOTAL_SECTOR].set_index("year")["value"]
    sectors = all_gases[all_gases["sector"].isin(SECTORS)]
    gap = (sectors.groupby("year")["value"].sum() - total).abs()
    if gap.max() > 0.01:
        raise ValueError(f"Sectors don't add up to the national total:\n{gap[gap > 0.01]}")
    write_tidy(ordered(sectors, "sector", SECTORS), "emissions/ghg_by_sector", [path], __name__)

    national = raw[raw["sector"] == TOTAL_SECTOR]
    gap = (national[national["gas"].isin(GASES)].groupby("year")["value"].sum() - total).abs()
    if gap.max() > 0.01:
        raise ValueError(f"Gases don't add up to the national total:\n{gap[gap > 0.01]}")
    write_tidy(ordered(national, "gas", GASES), "emissions/ghg_by_gas", [path], __name__)
