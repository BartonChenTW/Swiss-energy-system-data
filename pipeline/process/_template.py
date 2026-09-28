"""<Source name> -> <dataset ids>.

Input : data/raw/<source_id>/<file>   (describe the columns you use)
Output: <theme>/<dataset_id>

Copy this file to pipeline/process/<source_id>.py (module name == source id),
then register each output in catalog/datasets.yml.
"""
import pandas as pd

from ..common import RAW_DIR, write_tidy

SOURCE_ID = "<source_id>"
FILE = "<file>"


def run() -> None:
    path = RAW_DIR / SOURCE_ID / FILE
    if not path.exists():
        print(f"  {FILE} not found, run: python -m pipeline.fetch --source {SOURCE_ID}")
        return

    raw = pd.read_csv(path)
    tidy = pd.DataFrame({
        "year": raw["<year column>"],
        "category": raw["<category column>"],
        "value": raw["<value column>"],
        "unit": "<unit>",
    })
    # `inputs` feeds the provenance record; `notes` is optional free text for it.
    write_tidy(tidy, "<theme>/<dataset_id>", inputs=[path], processor=__name__)
