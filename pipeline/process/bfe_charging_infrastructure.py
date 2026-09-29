"""SFOE key figures on public EV charging (ich-tanke-strom.ch, OGD 57) -> public charging stations.

Input : data/raw/bfe_charging_infrastructure/ich_tanke_strom_Kennzahlen_monatlich.csv
        one row per year and month; stations_CH_count, locations_CH_count (monthly averages)
Output: mobility/public_charging_stations  (December value of each year)

Stations are used rather than charging points: the point count falls in 2025 while stations
keep rising, which looks like a change in how points are reported.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_charging_infrastructure"
FILE = "ich_tanke_strom_Kennzahlen_monatlich.csv"
SERIES = {"stations_CH_count": "Charging stations", "locations_CH_count": "Charging sites"}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    df = pd.read_csv(path, encoding="utf-8-sig")
    december = df[df["month"] == 12].set_index("year")[list(SERIES)].rename(columns=SERIES)
    long = december.rename_axis("year").reset_index().melt(id_vars="year", var_name="category", value_name="value")
    write_tidy(long.assign(value=long["value"].round(0).astype(int), unit="count"),
               "mobility/public_charging_stations", [path], __name__,
               notes=f"December values; latest month in the file: {int(df['year'].max())}-{int(df.loc[df['year'] == df['year'].max(), 'month'].max()):02d}.")
