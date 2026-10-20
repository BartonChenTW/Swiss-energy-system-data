"""SFOE solar potential of Swiss municipalities (OGD 52) -> solar potential of buildings.

Input : data/raw/bfe_solar_potential/Solarenergiepotenziale_Gemeinden_Daecher_und_Fassaden.csv
        one row per municipality, potentials in GWh/a for four scenarios (+ monthly values)
        data/raw/bfe_electricity_statistics/ogd32_elektrizitaetbilanz_jahreswerte.csv  (PV production, for comparison)
Output: renewables/solar_potential_buildings   (TWh/a: potential by scenario vs PV production of the latest year)
        renewables/solar_potential_by_canton   (TWh/a: PV potential of roofs, by canton)

Scenarios 1 and 3 use all roofs (and facades) for PV; 2 and 4 use the best roof section of each
building for solar heat and the rest for PV. Liechtenstein's municipalities are excluded.
"""
import pandas as pd

from ..common import RAW_DIR, input_record, write_tidy

SOURCE_ID = "bfe_solar_potential"
FILE = "Solarenergiepotenziale_Gemeinden_Daecher_und_Fassaden.csv"
ELEC = RAW_DIR / "bfe_electricity_statistics" / "ogd32_elektrizitaetbilanz_jahreswerte.csv"

CANTONS = {
    "Zürich": "ZH", "Bern": "BE", "Luzern": "LU", "Uri": "UR", "Schwyz": "SZ", "Obwalden": "OW",
    "Nidwalden": "NW", "Glarus": "GL", "Zug": "ZG", "Fribourg": "FR", "Solothurn": "SO",
    "Basel-Stadt": "BS", "Basel-Landschaft": "BL", "Schaffhausen": "SH", "Appenzell Ausserrhoden": "AR",
    "Appenzell Innerrhoden": "AI", "St. Gallen": "SG", "Graubünden": "GR", "Aargau": "AG", "Thurgau": "TG",
    "Ticino": "TI", "Vaud": "VD", "Valais": "VS", "Neuchâtel": "NE", "Genève": "GE", "Jura": "JU",
}
SCENARIOS = {  # column -> label, in bar order
    "Scenario3_RoofsFacades_PotentialSolarElectricity_GWh": "Roofs and facades, all PV",
    "Scenario1_RoofsOnly_PotentialSolarElectricity_GWh": "Roofs, all PV",
    "Scenario2_RoofsOnly_PotentialSolarElectricity_GWh": "Roofs, PV next to solar heat",
    "Scenario2_RoofsOnly_PotentialSolarHeat_GWh": "Roofs, solar heat on the best section",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists() or not ELEC.exists():
        print(f"  {FILE} or electricity statistics not found, run: python -m pipeline.fetch --source {SOURCE_ID} --source bfe_electricity_statistics")
        return
    d = pd.read_csv(path, encoding="utf-8-sig")
    ch = d[d["Country"] == "CH"]
    unknown = set(ch["Canton"].dropna()) - set(CANTONS)
    if unknown or ch["Canton"].isna().any():
        raise ValueError(f"Unmapped or missing cantons: {unknown or 'missing values'}")
    year = int(input_record(path)["retrieved"][:4])  # snapshot: the year it was retrieved

    elec = pd.read_csv(ELEC, encoding="utf-8-sig").set_index("Jahr")
    last = int(elec.index.max())
    totals = {label: ch[col].sum() / 1000 for col, label in SCENARIOS.items()}
    totals[f"Solar PV production in {last}"] = elec.loc[last, "Erzeugung_photovoltaik_GWh"] / 1000
    winter = [f"Scenario1_RoofsOnly_PotentialSolarElectricity_Month{m:02d}_GWh" for m in (10, 11, 12, 1, 2, 3)]
    winter_share = ch[winter].sum().sum() / ch["Scenario1_RoofsOnly_PotentialSolarElectricity_GWh"].sum()
    write_tidy(pd.DataFrame({"year": year, "category": list(totals), "value": [round(v, 1) for v in totals.values()],
                             "unit": "TWh/a"}), "renewables/solar_potential_buildings", [path, ELEC], __name__,
               notes=f"October–March gives {winter_share:.0%} of the annual roof PV potential.")

    by = (ch.groupby(ch["Canton"].map(CANTONS))["Scenario1_RoofsOnly_PotentialSolarElectricity_GWh"].sum() / 1000)
    by = by.sort_values(ascending=False)
    write_tidy(pd.DataFrame({"year": year, "category": by.index, "value": by.round(2).values, "unit": "TWh/a"}),
               "renewables/solar_potential_by_canton", [path], __name__,
               notes=f"Switzerland: {by.sum():.1f} TWh/a from {len(ch):,} municipalities.")
