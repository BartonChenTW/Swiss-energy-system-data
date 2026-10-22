"""MeteoSwiss manual stations (ogd-nime), yearly values -> days with snow cover.

Input : data/raw/meteoswiss_snow/ogd-nime_<station>_y.csv
        station_abbr; reference_timestamp (01.01.YYYY 00:00); hnd000l0 = days with measurable snow
        cover, summed August–July (stamped with the year the snow year ends)
Output: renewables/snow_cover_days   (days per snow year, four stations from 911 to 2691 m)

Checked: hnd000l0 of year Y equals the sum of the monthly values from August Y-1 to July Y.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "meteoswiss_snow"
STATIONS = {  # abbreviation -> label, highest first
    "wfj": "Weissfluhjoch (2691 m)", "sae": "Säntis (2501 m)",
    "sia": "Segl-Maria (1804 m)", "ein": "Einsiedeln (911 m)",
}


def run() -> None:
    paths = [RAW_DIR / SOURCE_ID / f"ogd-nime_{s}_y.csv" for s in STATIONS]
    if not all(p.exists() for p in paths):
        print(f"  station files not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    frames = []
    for (station, label), path in zip(STATIONS.items(), paths):
        d = pd.read_csv(path, sep=";", encoding="latin-1")
        frames.append(pd.DataFrame({"year": d["reference_timestamp"].str[6:10].astype(int),
                                    "category": label, "value": d["hnd000l0"]}))
    tidy = pd.concat(frames).dropna(subset=["value"])
    # Keep only complete snow years: before August, the current year's value is still a partial sum.
    now = pd.Timestamp.now()
    tidy = tidy[tidy["year"] <= now.year - (now.month < 8)]
    tidy["unit"] = "days"
    write_tidy(tidy, "renewables/snow_cover_days", paths, __name__)
