"""HP-CatCH (ETH Zurich) natural inflows into Swiss storage reservoirs -> inflow time series.

Input : data/raw/hp_catch/hp_catch_update1.zip, read in place (no extraction):
        hp_catch/data/hydropower_inflows/ds_prevah_obs_reservoir_inflows_updated.zarr
        inflows_direct (reservoir x time, m³/s), time (hourly steps from 1991-01-01, 1991–2022)
Output: renewables/reservoir_inflows_monthly    (million m³ per month, 1991–2022)
        renewables/reservoir_inflows_by_season  (billion m³ per year: April–September vs the other months)

"Direct contributors" inflows count only the sub-basins draining into a reservoir or its water
intakes, not those of reservoirs upstream, so they are natural inflows and add up across the
107 reservoirs without double counting (Haddad et al., ESSD preprint, section 2.3.1). Runoff is
PREVAH daily output repeated for each hour; 29 February is missing in leap years. Inflows into
run-of-river plants are not summed: plants on the same river share their water.
"""
import numpy as np
import pandas as pd
import zarr

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "hp_catch"
FILE = "hp_catch_update1.zip"
INFLOWS = "hp_catch/data/hydropower_inflows/ds_prevah_obs_reservoir_inflows_updated.zarr"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    store = zarr.ZipStore(str(path), mode="r")
    try:
        g = zarr.open_group(store, path=INFLOWS, mode="r")
        time = pd.to_datetime(g["time"][:], unit="s", origin="1991-01-01")
        flow = np.nansum(g["inflows_direct"][:], axis=0)  # m³/s, summed over reservoirs
        n_reservoirs = g["inflows_direct"].shape[0]
    finally:
        store.close()
    if not (pd.Series(time).diff().dropna() <= pd.Timedelta(days=1, hours=1)).all():
        raise ValueError("Unexpected gaps in the HP-CatCH time axis")
    volume = pd.Series(flow * 3600, index=time)  # m³ per hourly step

    monthly = volume.resample("MS").sum() / 1e6
    write_tidy(pd.DataFrame({"period": monthly.index.strftime("%Y-%m"), "category": f"{n_reservoirs} storage reservoirs",
                             "value": monthly.round(1).values, "unit": "million m³"}),
               "renewables/reservoir_inflows_monthly", [path], __name__)

    summer = volume.index.month.isin(range(4, 10))
    by_year = pd.DataFrame({"April–September": volume[summer].groupby(volume[summer].index.year).sum(),
                            "October–March months": volume[~summer].groupby(volume[~summer].index.year).sum()}) / 1e9
    tidy = by_year.round(3).reset_index(names="year").melt(id_vars="year", var_name="category")
    tidy["unit"] = "billion m³"
    total = by_year.sum(axis=1)
    write_tidy(tidy, "renewables/reservoir_inflows_by_season", [path], __name__,
               notes=f"Mean {total.mean():.1f} billion m³ a year, {by_year['April–September'].sum() / total.sum():.0%} of it "
                     f"from April to September; lowest {total.min():.1f} ({total.idxmin()}), highest {total.max():.1f} ({total.idxmax()}).")
