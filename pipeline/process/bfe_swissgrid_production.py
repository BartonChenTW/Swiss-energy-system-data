"""energiedashboard.ch daily Swissgrid data -> winter and summer electricity balance.

Input : data/raw/bfe_swissgrid_production/ogd104_stromproduktion_swissgrid.csv
        Datum, Energietraeger, Produktion_GWh (daily, from 2015)
        data/raw/bfe_swissgrid_consumption/ogd103_stromverbrauch_swissgrid_lv_und_endv.csv
        Datum, Landesverbrauch_GWh, Endverbrauch_GWh (daily, from 2017)
Output: electricity/winter_balance              (TWh, Oct–Mar: domestic production vs national consumption)
        electricity/summer_balance              (TWh, Apr–Sep)
        electricity/winter_production_by_source (TWh, Oct–Mar)

Winter "2024" = October 2023 to March 2024. Only half-years with data for every day are kept.
Production is gross (it includes output from pumped storage); consumption excludes the
pumps' own use, so the gap approximates net imports minus pumping.
Checked: annual sums of the daily production match the official electricity statistics.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_swissgrid_production"
PROD = RAW_DIR / SOURCE_ID / "ogd104_stromproduktion_swissgrid.csv"
CONS = RAW_DIR / "bfe_swissgrid_consumption" / "ogd103_stromverbrauch_swissgrid_lv_und_endv.csv"

SOURCES = {  # Energietraeger -> label, in stack order
    "Flusskraft": "Run-of-river hydro", "Speicherkraft": "Storage hydro", "Kernkraft": "Nuclear",
    "Thermische": "Thermal", "Photovoltaik": "Solar PV", "Wind": "Wind",
}


def add_season(df: pd.DataFrame) -> pd.DataFrame:
    """Season (Winter = Oct–Mar, Summer = Apr–Sep) and its year (a winter counts in the year of its January)."""
    m = df["Datum"].dt.month
    winter = (m >= 10) | (m <= 3)
    return df.assign(season=winter.map({True: "Winter", False: "Summer"}),
                     syear=df["Datum"].dt.year + (m >= 10).astype(int))


def season_days(season: str, year: int) -> int:
    start, end = (f"{year - 1}-10-01", f"{year}-03-31") if season == "Winter" else (f"{year}-04-01", f"{year}-09-30")
    return len(pd.date_range(start, end))


def complete_seasons(df: pd.DataFrame) -> set:
    days = df.groupby(["season", "syear"])["Datum"].nunique()
    return {k for k, n in days.items() if n == season_days(*k)}


def run() -> None:
    if not PROD.exists() or not CONS.exists():
        print(f"  Swissgrid files not found, run: python -m pipeline.fetch --source {SOURCE_ID} --source bfe_swissgrid_consumption")
        return
    p = add_season(pd.read_csv(PROD, parse_dates=["Datum"]))
    c = add_season(pd.read_csv(CONS, parse_dates=["Datum"]))
    unknown = set(p["Energietraeger"]) - set(SOURCES)
    if unknown:
        raise ValueError(f"Unmapped production sources: {unknown}")

    prod_ok = complete_seasons(p)
    both_ok = prod_ok & complete_seasons(c)
    prod = p.groupby(["season", "syear"])["Produktion_GWh"].sum() / 1000
    cons = c.groupby(["season", "syear"])["Landesverbrauch_GWh"].sum() / 1000

    for season, dataset in (("Winter", "electricity/winter_balance"), ("Summer", "electricity/summer_balance")):
        years = sorted(y for s, y in both_ok if s == season)
        rows = [(y, "Domestic production", prod[(season, y)]) for y in years] + \
               [(y, "National consumption", cons[(season, y)]) for y in years]
        tidy = pd.DataFrame(rows, columns=["year", "category", "value"]).sort_values("year", kind="stable")
        write_tidy(tidy.assign(value=tidy["value"].round(2), unit="TWh"), dataset, [PROD, CONS], __name__,
                   notes=f"{season} half-years {years[0]}–{years[-1]}. Dashboard consumption differs from the "
                         "official annual statistics by up to ~3%.")

    winters = sorted(y for s, y in prod_ok if s == "Winter")
    w = p[(p["season"] == "Winter") & p["syear"].isin(winters)]
    by = (w.assign(category=w["Energietraeger"].map(SOURCES))
          .groupby(["syear", "category"])["Produktion_GWh"].sum().unstack()
          .reindex(columns=list(SOURCES.values()), fill_value=0) / 1000)
    long = by.reset_index().melt(id_vars="syear", var_name="category", value_name="value").sort_values("syear", kind="stable")
    write_tidy(pd.DataFrame({"year": long["syear"], "category": long["category"], "value": long["value"].round(2),
                             "unit": "TWh"}), "electricity/winter_production_by_source", [PROD], __name__)
