"""FSO passenger cars by fuel (stats.swiss SDMX) -> electric cars in the stock and new registrations.

Input : data/raw/bfs_vehicles/DF_MFZ_1_TECH_stock_by_fuel.csv   (stock on 30 September)
        data/raw/bfs_vehicles/DF_IVS_1_TECH_new_by_fuel.csv      (new vehicles, registration type N)
        columns TIME_PERIOD, UV_RV_FUEL (code, _T = total), OBS_VALUE (cars)
Output: mobility/new_cars_by_fuel      (cars per year, by propulsion)
        mobility/electric_car_stock    (battery-electric and plug-in hybrid cars in the stock)
        mobility/plug_in_share         (% of new cars and of the stock that plug in)

A fuel with no cars in a year has no row; those are filled with 0. The fuels must add up to _T.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bfs_vehicles"
STOCK = "DF_MFZ_1_TECH_stock_by_fuel.csv"
NEW = "DF_IVS_1_TECH_new_by_fuel.csv"

FUELS = {  # UV_RV_FUEL -> label, in stack order (bottom first)
    "EL": "Battery-electric", "HP": "Plug-in hybrid", "HD": "Plug-in hybrid",
    "PH": "Hybrid (not plug-in)", "DH": "Hybrid (not plug-in)",
    "PC": "Petrol", "DC": "Diesel",
    "GA": "Other (gas, hydrogen, other)", "FC": "Other (gas, hydrogen, other)", "_O": "Other (gas, hydrogen, other)",
}
PLUG_IN = ["Battery-electric", "Plug-in hybrid"]


def by_fuel(path) -> pd.DataFrame:
    """Wide table: one row per year, one column per label, plus 'total'."""
    raw = pd.read_csv(path, usecols=["TIME_PERIOD", "UV_RV_FUEL", "OBS_VALUE"])
    total = raw[raw["UV_RV_FUEL"] == "_T"].set_index("TIME_PERIOD")["OBS_VALUE"]
    parts = raw[raw["UV_RV_FUEL"] != "_T"]
    unmapped = set(parts["UV_RV_FUEL"]) - set(FUELS)
    if unmapped:
        raise ValueError(f"{path.name}: unmapped fuel codes {unmapped}")
    wide = (parts.assign(label=parts["UV_RV_FUEL"].map(FUELS))
            .pivot_table(index="TIME_PERIOD", columns="label", values="OBS_VALUE", aggfunc="sum")
            .reindex(index=total.index, columns=list(dict.fromkeys(FUELS.values()))).fillna(0))
    gap = (wide.sum(axis=1) - total).abs()
    if gap.max() > 0:
        raise ValueError(f"{path.name}: fuels don't add up to the total:\n{gap[gap > 0]}")
    return wide.assign(total=total)


def tidy(wide: pd.DataFrame, columns: list[str], unit: str) -> pd.DataFrame:
    long = wide[columns].rename_axis("year").reset_index().melt(id_vars="year", var_name="category", value_name="value")
    return long.assign(unit=unit)


def run() -> None:
    paths = [RAW_DIR / SOURCE_ID / f for f in (STOCK, NEW)]
    if not all(p.exists() for p in paths):
        print(f"  input files not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    stock, new = (by_fuel(p) for p in paths)
    labels = list(dict.fromkeys(FUELS.values()))

    write_tidy(tidy(new, labels, "cars").astype({"value": int}), "mobility/new_cars_by_fuel", [paths[1]], __name__)
    write_tidy(tidy(stock, PLUG_IN, "cars").astype({"value": int}), "mobility/electric_car_stock", [paths[0]], __name__)

    share = pd.DataFrame({
        "New cars": new[PLUG_IN].sum(axis=1) / new["total"] * 100,
        "Stock": stock[PLUG_IN].sum(axis=1) / stock["total"] * 100,
    }).round(2)
    write_tidy(tidy(share, list(share.columns), "%"), "mobility/plug_in_share", paths, __name__)
