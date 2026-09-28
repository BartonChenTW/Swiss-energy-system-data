"""Shared paths, catalog loading and the tidy-data contract."""
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "catalog"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SITE_DATA_DIR = ROOT / "docs" / "data"

TIDY_COLUMNS = ["year", "category", "value", "unit"]


def load_yaml(name: str) -> dict:
    with open(CATALOG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_catalog() -> tuple[dict, list]:
    """Return (sources by id, list of datasets), checking every dataset names a known source."""
    sources = {s["id"]: s for s in load_yaml("sources.yml")["sources"]}
    datasets = load_yaml("datasets.yml")["datasets"]
    for ds in datasets:
        if ds["source"] not in sources:
            raise ValueError(f"Dataset {ds['id']!r} refers to unknown source {ds['source']!r}")
    return sources, datasets


def validate_tidy(df: pd.DataFrame, name: str) -> None:
    missing = set(TIDY_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{name}: missing columns {sorted(missing)}")
    if not pd.api.types.is_integer_dtype(df["year"]):
        raise ValueError(f"{name}: 'year' must be integer")
    if not pd.api.types.is_numeric_dtype(df["value"]):
        raise ValueError(f"{name}: 'value' must be numeric")
    units = df["unit"].dropna().unique()
    if len(units) != 1:
        raise ValueError(f"{name}: expected exactly one unit, found {list(units)}")
    dupes = df.duplicated(["year", "category"])
    if dupes.any():
        raise ValueError(f"{name}: duplicate (year, category) rows:\n{df[dupes]}")


def write_tidy(df: pd.DataFrame, dataset_id: str) -> Path:
    """Validate and write a processed dataset to data/processed/<dataset_id>.csv."""
    df = df[TIDY_COLUMNS].reset_index(drop=True)
    validate_tidy(df, dataset_id)
    path = PROCESSED_DIR / f"{dataset_id}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  wrote {path.relative_to(ROOT)} ({len(df)} rows)")
    return path
