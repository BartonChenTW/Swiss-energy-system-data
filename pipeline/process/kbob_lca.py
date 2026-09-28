"""KBOB/ecobau/IPB LCA data for construction (v9.0) -> embodied GHG of common materials.

Input : data/raw/kbob_lca/Oekobilanzdaten_im_Baubereich_V9.0.xlsx
        sheet "Baumaterialien Matériaux": col 0 ID, col 2 name, col 6 reference unit,
        col 25 GHG emissions total (kg CO2-eq per reference unit, manufacture + disposal)
Output: buildings/lca_ghg_structural_materials  (kg CO2-eq per kg)
        buildings/lca_ghg_insulation_materials  (kg CO2-eq per kg)

Only generic entries (IDs like 01.002, not product-specific 01.002.05) are used.
Per-kg values are not a like-for-like comparison of building elements: an element also
depends on how much material it needs (density, thickness, U-value). Biogenic carbon
stored in wood is reported separately by KBOB and not subtracted here.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "kbob_lca"
FILE = "Oekobilanzdaten_im_Baubereich_V9.0.xlsx"
SHEET = "Baumaterialien Matériaux"
COL_ID, COL_NAME, COL_UNIT, COL_GHG = 0, 2, 6, 25
YEAR = 2026  # publication year of v9.0

STRUCTURAL = {  # KBOB ID -> label
    "01.002": "Concrete for buildings (unreinforced)",
    "01.042": "Precast concrete element",
    "06.003": "Reinforcing steel",
    "06.012": "Steel section",
    "02.001": "Clay brick",
    "02.002": "Calcium silicate brick",
    "07.023": "Structural solid timber (KVH)",
    "07.003": "Glued laminated timber",
    "07.020": "Cross-laminated timber",
    "03.008": "Gypsum plasterboard",
    "03.006": "Flat glass (uncoated)",
    "06.002": "Aluminium section",
}
INSULATION = {
    "10.015": "Straw bale",
    "10.010": "Cellulose fibre",
    "10.009": "Wood fibre board",
    "10.008": "Stone wool",
    "10.001": "Glass wool",
    "10.002": "Cork board",
    "10.007": "Cellular glass",
    "10.004": "Expanded polystyrene (EPS)",
    "10.006": "Polyurethane (PUR/PIR)",
    "10.005": "Extruded polystyrene (XPS)",
}


def select(sheet: pd.DataFrame, ids: dict) -> pd.DataFrame:
    rows = sheet[sheet[COL_ID].astype(str).isin(ids)].drop_duplicates(COL_ID)
    missing = set(ids) - set(rows[COL_ID].astype(str))
    if missing:
        raise ValueError(f"KBOB IDs not found: {missing}")
    wrong_unit = rows[rows[COL_UNIT] != "kg"]
    if len(wrong_unit):
        raise ValueError(f"Not per kg: {wrong_unit[[COL_ID, COL_NAME, COL_UNIT]].values.tolist()}")
    rows = rows.assign(category=rows[COL_ID].astype(str).map(ids), value=pd.to_numeric(rows[COL_GHG]))
    rows = rows.sort_values("value", ascending=False)
    return pd.DataFrame({"year": YEAR, "category": rows["category"], "value": rows["value"].round(3),
                         "unit": "kg CO2-eq/kg"})


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    sheet = pd.read_excel(path, sheet_name=SHEET, header=None)
    header = str(sheet.iloc[3, COL_GHG]) + " " + str(sheet.iloc[8, COL_GHG])
    if "Treibhausgas" not in header or "CO2" not in header:
        raise ValueError(f"Column {COL_GHG} is no longer GHG emissions: {header!r}")
    write_tidy(select(sheet, STRUCTURAL), "buildings/lca_ghg_structural_materials", [path], __name__)
    write_tidy(select(sheet, INSULATION), "buildings/lca_ghg_insulation_materials", [path], __name__)
