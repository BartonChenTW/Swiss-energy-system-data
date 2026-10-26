"""FONES stockholding reports -> mandatory stocks of fuels.

Input : data/raw/bwl_pflichtlager/*.pdf   (used only for provenance: the reports have no machine-readable table)
Output: supply/oil_stockholding        (1000 m3, by product, at the report dates 2019, 2023 and 2025)

The values are transcribed from the energy tables of the reports, in m3 and rounded as printed:
  2019  Vorratshaltungsbericht 2019, section 5, "Bestand" as of 30 June 2019
  2023  Vorratshaltungsbericht 2023, section 5, "Bestand" as of 31 May 2023
  2025  Aufsicht Pflichtlagerhaltung 2025, "Effektive Menge" as of 31 December 2025
Since December 2024 most of the heating oil held as natural gas replacement counts as ordinary heating oil,
so that category is not reported for 2025. The 2025 target quantities (Soll) are shown on the Security of supply page.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "bwl_pflichtlager"
FILES = ["Vorratshaltungsbericht_2019_D.pdf", "Vorratshaltungsbericht_2023_DE.pdf", "Vorratshaltung_2025.pdf"]

STOCK_M3 = {
    2019: {"Motor petrol": 1_257_000, "Diesel": 1_107_000, "Jet fuel": 430_000,
           "Heating oil": 1_229_000, "Heating oil as gas replacement": 384_000},
    2023: {"Motor petrol": 1_113_000, "Diesel": 1_187_000, "Jet fuel": 362_000,
           "Heating oil": 1_033_000, "Heating oil as gas replacement": 384_000},
    2025: {"Motor petrol": 1_116_650, "Diesel": 1_238_850, "Jet fuel": 367_670, "Heating oil": 1_234_890},
}


def run() -> None:
    paths = [RAW_DIR / SOURCE_ID / f for f in FILES]
    missing = [p.name for p in paths if not p.exists()]
    if missing:
        print(f"  {missing} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return
    rows = [(year, product, m3 / 1000, "1000 m³") for year, d in STOCK_M3.items() for product, m3 in d.items()]
    tidy = pd.DataFrame(rows, columns=["year", "category", "value", "unit"])
    write_tidy(tidy, "supply/oil_stockholding", paths, __name__,
               notes="Transcribed from the PDF reports; dates are 30 Jun 2019, 31 May 2023 and 31 Dec 2025.")
