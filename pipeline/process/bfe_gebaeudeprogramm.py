"""Das Gebäudeprogramm (annual statistics, OGD 18) -> subsidy payouts and ongoing savings.

Input : data/raw/bfe_gebaeudeprogramm/ogd18_gebaeudeprogramm_{auszahlungen,energiewirkung,co2wirkung}.csv
Output: buildings/gp_payouts_by_area   (million CHF paid out per year, Switzerland = sum of cantons)
        buildings/gp_energy_savings    (GWh/yr, ongoing annual savings of all measures since 2010)
        buildings/gp_co2_savings       (kt CO2/yr, same basis)

"Anhaltende Wirkung" = the annual effect in that year of all measures funded since the
programme started (calculated with the harmonised funding model HFM 2015).
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_gebaeudeprogramm"

AREAS = {  # Massnahmenbereich -> label, in stack order
    "Waermedaemmung": "Insulation of the envelope",
    "Haustechnik": "Heating & building services",
    "Systemsanierung": "Whole-building renovation",
    "Neubau": "New buildings (high standard)",
    "Zentrale_Waermeversorgung": "Central heating plants & networks",
    "Indirekte_Massnahmen": "Indirect measures (advice, training)",
}


def tidy(df: pd.DataFrame, value_col: str, scale: float, unit: str, region: str | None = None) -> pd.DataFrame:
    if region:
        df = df[df["Region"] == region]
    out = df.assign(category=df["Massnahmenbereich"].map(AREAS))
    unknown = set(df.loc[out["category"].isna(), "Massnahmenbereich"])
    if unknown:
        raise ValueError(f"Unmapped Massnahmenbereich: {unknown}")
    out = out.groupby(["Jahr", "category"], sort=False)[value_col].sum().reset_index()
    out = out[out.groupby("category")[value_col].transform("sum") != 0]  # drop areas that are always zero
    order = {c: i for i, c in enumerate(AREAS.values())}
    out = out.sort_values(["Jahr", "category"], key=lambda s: s.map(order) if s.name == "category" else s)
    return pd.DataFrame({"year": out["Jahr"], "category": out["category"],
                         "value": (out[value_col] / scale).round(2), "unit": unit})


def run() -> None:
    folder = RAW_DIR / SOURCE_ID
    files = {k: folder / f"ogd18_gebaeudeprogramm_{k}.csv" for k in ("auszahlungen", "energiewirkung", "co2wirkung")}
    missing = [p.name for p in files.values() if not p.exists()]
    if missing:
        print(f"  {missing} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    pay, energy, co2 = (pd.read_csv(p, encoding="utf-8-sig") for p in files.values())

    write_tidy(tidy(pay, "Auszahlungen_CHF", 1e6, "million CHF"), "buildings/gp_payouts_by_area",
               [files["auszahlungen"]], __name__, notes="Switzerland = sum of the 26 cantons.")
    write_tidy(tidy(energy, "Energiewirkung_GWh_Jahr", 1, "GWh/yr", "CH"), "buildings/gp_energy_savings",
               [files["energiewirkung"]], __name__)
    write_tidy(tidy(co2, "CO2_Wirkung_Tonnen_CO2_Jahr", 1000, "kt CO2/yr", "CH"), "buildings/gp_co2_savings",
               [files["co2wirkung"]], __name__)
