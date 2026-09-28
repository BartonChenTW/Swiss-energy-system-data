"""<Source name> -> <dataset ids>.

Input : data/raw/<source_id>/<file>   (downloaded <date> from <url>)
Output: <theme>/<dataset_id>

Copy this file to pipeline/process/<source_id>.py, then register the output in
catalog/datasets.yml.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "<source_id>"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / "<file>"
    if not path.exists():
        print(f"  {path.name} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return

    raw = pd.read_csv(path)
    tidy = pd.DataFrame({
        "year": raw["<year column>"].astype(int),
        "category": raw["<category column>"],
        "value": raw["<value column>"],
        "unit": "<unit>",
    })
    write_tidy(tidy, "<theme>/<dataset_id>")
