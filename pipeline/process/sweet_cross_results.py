"""SWEET CROSS scenario results v2022-09 -> 2050 results of nine Swiss models, side by side.

Input : data/raw/sweet_cross_results/results-cross-scenarios-2024-12-05.zip
        CROSS-v2022-09-results-2024-12-05.csv: scenario, model, type, variable, unit,
        timeResolution, timestep, value (long format, 2050 only)
Output: scenarios/cross_solar_2050        (TWh, solar electricity by model)
        scenarios/cross_wind_2050         (TWh, wind electricity by model)
        scenarios/cross_net_imports_2050  (TWh, net electricity imports by model)

All three use the scenario every model ran: CO2 offsetting abroad, electricity market
integrated with the EU ("abroad-together"). Models that do not report a variable are left out.
"""
import zipfile

import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "sweet_cross_results"
FILE = "results-cross-scenarios-2024-12-05.zip"
SCENARIO = "abroad-together"
MODEL_LABELS = {"EP2050": "EP2050+ (SFOE)", "VSE": "VSE / Empa"}
OUTPUTS = {  # variable -> dataset
    "Electricity-supply|Solar": "scenarios/cross_solar_2050",
    "Electricity-supply|Wind": "scenarios/cross_wind_2050",
    "Electricity-supply|Net-imports": "scenarios/cross_net_imports_2050",
}


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    with zipfile.ZipFile(path) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        d = pd.read_csv(zf.open(name))
    d = d[(d["scenario"] == SCENARIO) & (d["timeResolution"] == "Annual")]
    for variable, dataset in OUTPUTS.items():
        v = d[d["variable"] == variable].dropna(subset=["value"])
        if v.empty or set(v["unit"]) != {"TWh"}:
            raise ValueError(f"{variable}: expected TWh values for {SCENARIO}, found units {set(v['unit'])}")
        v = v.sort_values("value", ascending=False)
        write_tidy(pd.DataFrame({"year": v["timestep"].astype(int), "category": v["model"].replace(MODEL_LABELS),
                                 "value": v["value"].round(1), "unit": "TWh"}), dataset, [path], __name__,
                   notes=f"{len(v)} of {d['model'].nunique()} models report this variable for scenario {SCENARIO}.")
