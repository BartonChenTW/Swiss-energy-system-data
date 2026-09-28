"""Convert processed tidy CSVs into the JSON files the site reads.

    python -m pipeline.build_site

Writes docs/data/<dataset id>.json for every dataset in catalog/datasets.yml,
plus docs/data/catalog.json listing all sources and datasets.
"""
import json

import pandas as pd

from .common import PROCESSED_DIR, ROOT, SITE_DATA_DIR, load_catalog, validate_tidy


def to_series(df: pd.DataFrame) -> tuple[list[int], list[dict]]:
    """Pivot tidy rows to one value list per category, aligned to sorted years."""
    years = sorted(int(y) for y in df["year"].unique())
    categories = list(dict.fromkeys(df["category"]))  # keep CSV order for legends
    wide = df.pivot(index="year", columns="category", values="value").reindex(index=years, columns=categories)
    series = [
        {"name": c, "values": [None if pd.isna(v) else float(v) for v in wide[c]]}
        for c in categories
    ]
    return years, series


def write_json(obj, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    sources, datasets = load_catalog()
    built = []
    for ds in datasets:
        csv = PROCESSED_DIR / f"{ds['id']}.csv"
        if not csv.exists():
            print(f"  skip {ds['id']}: {csv.relative_to(ROOT)} not found")
            continue
        df = pd.read_csv(csv)
        validate_tidy(df, ds["id"])
        years, series = to_series(df)
        src = sources[ds["source"]]
        write_json({
            **ds,
            "unit": df["unit"].iloc[0],
            "source": {k: src[k] for k in ("id", "name", "publisher", "url")},
            "years": years,
            "series": series,
        }, SITE_DATA_DIR / f"{ds['id']}.json")
        built.append(ds["id"])
        print(f"  built {ds['id']}")

    write_json({
        "sources": [{k: v for k, v in s.items() if k != "downloads"} for s in sources.values()],
        "datasets": [ds for ds in datasets if ds["id"] in built],
    }, SITE_DATA_DIR / "catalog.json")
    print(f"{len(built)} datasets -> {SITE_DATA_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
