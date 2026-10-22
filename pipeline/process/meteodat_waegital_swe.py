"""Meteodat snow water equivalent of the Wägital catchment on 1 April -> snow water reserves.

Input : data/raw/meteodat_waegital_swe/Waegital_1943-2026.txt
        text header, then a fixed-width table: year, 900m-1500m, 1500m-2300m, total (million m³)
Output: renewables/waegital_snow_water_equivalent   (million m³ on 1 April, by elevation zone)

The file name carries the last year and changes with each yearly Zenodo version.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "meteodat_waegital_swe"
FILE = "Waegital_1943-2026.txt"
ZONES = {"900m-1500m": "900–1500 m", "1500m-2300m": "1500–2300 m"}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    head = next(i for i, line in enumerate(lines) if line.startswith("year"))
    rows = [line.split() for line in lines[head + 2:] if line.strip()]
    raw = pd.DataFrame(rows, columns=lines[head].split()).astype(float)
    off = (raw[list(ZONES)].sum(axis=1) - raw["total"]).abs().max()
    if off > 0.15:  # zones are rounded to 0.1
        raise ValueError(f"Elevation zones do not add up to the total (off by {off:.1f})")
    tidy = raw.melt(id_vars="year", value_vars=list(ZONES), var_name="category")
    tidy["category"] = tidy["category"].map(ZONES)
    tidy["unit"] = "million m³"
    mean = raw.set_index("year")["total"]
    write_tidy(tidy, "renewables/waegital_snow_water_equivalent", [path], __name__,
               notes=f"Mean total {mean.mean():.1f} million m³ ({int(mean.index.min())}–{int(mean.index.max())}); "
                     f"{mean.idxmax():.0f} highest ({mean.max():.1f}), {mean.idxmin():.0f} lowest ({mean.min():.1f}).")
