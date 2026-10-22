"""SFOE weekly fill level of storage lakes (OGD 17) -> energy stored in Swiss reservoirs.

Input : data/raw/bfe_reservoirs/ogd17_fuellungsgrad_speicherseen.csv
        Datum (Mondays, weekly from 2000), <region>_speicherinhalt_gwh and <region>_max_speicherinhalt_gwh
        for Wallis, Graubuenden, Tessin, UebrigCH and TotalCH
Output: electricity/reservoir_storage           (TWh, weekly: stored energy by region)
        electricity/reservoir_fill_by_week      (%, by week of the year: recent years vs the 2000–last-full-year range)
        electricity/reservoir_storage_extremes  (TWh, yearly: spring low, autumn high, and capacity)

Stored energy is the electricity the water in the lakes could generate. Capacity grew from 8.5 TWh
(2000) to 8.9 TWh as dams were raised, so the fill level is stored energy over that week's capacity.
Weeks are ISO weeks of the reporting date.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfe_reservoirs"
FILE = "ogd17_fuellungsgrad_speicherseen.csv"
REGIONS = {"Wallis": "Valais", "Graubuenden": "Graubünden", "Tessin": "Ticino", "UebrigCH": "Rest of Switzerland"}
RECENT_YEARS = 5  # years shown as their own line in the week-by-week chart


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    d = pd.read_csv(path, parse_dates=["Datum"])
    regions_sum = d[[f"{r}_speicherinhalt_gwh" for r in REGIONS]].sum(axis=1)
    off = (regions_sum - d["TotalCH_speicherinhalt_gwh"]).abs().max()
    if off > 5:
        raise ValueError(f"Regions do not add up to the Swiss total (off by {off} GWh)")

    tidy = d.melt(id_vars="Datum", value_vars=[f"{r}_speicherinhalt_gwh" for r in REGIONS], var_name="category")
    tidy["period"] = tidy["Datum"].dt.strftime("%Y-%m-%d")
    tidy["category"] = tidy["category"].str.replace("_speicherinhalt_gwh", "").map(REGIONS)
    tidy["value"] = (tidy["value"] / 1000).round(3)
    tidy["unit"] = "TWh"
    last = d.iloc[-1]
    write_tidy(tidy, "electricity/reservoir_storage", [path], __name__,
               notes=f"Week of {last['Datum']:%d %b %Y}: {last['TotalCH_speicherinhalt_gwh'] / 1000:.2f} TWh stored, "
                     f"{last['TotalCH_speicherinhalt_gwh'] / last['TotalCH_max_speicherinhalt_gwh']:.0%} of "
                     f"{last['TotalCH_max_speicherinhalt_gwh'] / 1000:.2f} TWh capacity.")

    d["fill"] = 100 * d["TotalCH_speicherinhalt_gwh"] / d["TotalCH_max_speicherinhalt_gwh"]
    iso = d["Datum"].dt.isocalendar()
    d["year"], d["week"] = iso["year"].astype(int), "W" + iso["week"].astype(int).map("{:02d}".format)
    current = int(d["year"].max())
    ref = d[d["year"] < current]  # complete years only
    ref_label = f"{int(ref['year'].min())}–{current - 1}"
    stats = ref.groupby("week")["fill"].agg(["min", "mean", "max"])
    frames = [pd.DataFrame({"period": g["week"], "category": str(y), "value": g["fill"]})
              for y, g in d[d["year"] > current - RECENT_YEARS].groupby("year", sort=False)]
    frames = frames[::-1]  # newest year first in the legend
    for col, label in (("mean", "Mean"), ("min", "Lowest"), ("max", "Highest")):
        frames.append(pd.DataFrame({"period": stats.index, "category": f"{label} {ref_label}", "value": stats[col].values}))
    tidy = pd.concat(frames)
    tidy["value"] = tidy["value"].round(1)
    tidy["unit"] = "%"
    write_tidy(tidy, "electricity/reservoir_fill_by_week", [path], __name__)

    d["cal_year"] = d["Datum"].dt.year
    full = d[d["cal_year"] < d["cal_year"].max()] if d["Datum"].max().month < 12 else d  # complete years only
    by_year = full.groupby("cal_year").agg(low=("TotalCH_speicherinhalt_gwh", "min"),
                                          high=("TotalCH_speicherinhalt_gwh", "max"),
                                          capacity=("TotalCH_max_speicherinhalt_gwh", "max"))
    labels = {"capacity": "Storage capacity", "high": "Autumn high (yearly maximum)", "low": "Spring low (yearly minimum)"}
    tidy = (by_year[list(labels)] / 1000).round(3).reset_index().melt(id_vars="cal_year", var_name="category")
    tidy = tidy.rename(columns={"cal_year": "year"})
    tidy["category"] = tidy["category"].map(labels)
    tidy["unit"] = "TWh"
    write_tidy(tidy, "electricity/reservoir_storage_extremes", [path], __name__,
               notes=f"Lowest spring level: {by_year['low'].min() / 1000:.2f} TWh ({by_year['low'].idxmin()}).")
