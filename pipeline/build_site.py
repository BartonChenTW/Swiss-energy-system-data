"""Convert processed tidy CSVs into the JSON files the site reads.

    python -m pipeline.build_site

Writes docs/data/<dataset id>.json for every dataset in catalog/datasets.yml
(values + catalog metadata + provenance), plus docs/data/catalog.json with all
sources, datasets and references for the Sources and Library pages, and
docs/data/version.json (version from CHANGELOG.md, build date, commit).
"""
import json
from datetime import date

import pandas as pd

from .changelog import site_version
from .common import PROCESSED_DIR, ROOT, SITE_DATA_DIR, load_catalog, load_gaps, validate_tidy, x_column


def to_series(df: pd.DataFrame) -> tuple[list[int | str], list[dict]]:
    """Pivot tidy rows to one value list per category, aligned to sorted years (or periods)."""
    x = x_column(df)
    periods = sorted(int(y) for y in df[x].unique()) if x == "year" else sorted(str(p) for p in df[x].unique())
    categories = list(dict.fromkeys(df["category"]))  # keep CSV order for legends
    wide = df.pivot(index=x, columns="category", values="value").reindex(index=periods, columns=categories)
    series = [
        {"name": c, "values": [None if pd.isna(v) else float(v) for v in wide[c]]}
        for c in categories
    ]
    return periods, series


def provenance(csv) -> dict | None:
    meta = csv.with_suffix(".meta.json")
    if not meta.exists():
        return None
    m = json.loads(meta.read_text(encoding="utf-8"))
    retrieved = [i.get("retrieved") for i in m.get("inputs", []) if i.get("retrieved")]
    return {
        "generated": m.get("generated"),
        "retrieved": min(retrieved) if retrieved else None,
        "inputs": [{k: i.get(k) for k in ("url", "retrieved", "last_modified")} for i in m.get("inputs", [])],
        "notes": m.get("notes"),
    }


def input_sources(csv) -> list[str]:
    """Ids of all sources whose raw files a dataset was built from (data/raw/<source id>/...)."""
    meta = csv.with_suffix(".meta.json")
    if not meta.exists():
        return []
    files = [i.get("file", "") for i in json.loads(meta.read_text(encoding="utf-8")).get("inputs", [])]
    return list(dict.fromkeys(f.split("/")[2] for f in files if f.startswith("data/raw/")))


def write_json(obj, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), default=str)


def main() -> None:
    sources, datasets, references = load_catalog()
    built = {}  # dataset id -> ids of all its input sources
    for ds in datasets:
        csv = PROCESSED_DIR / f"{ds['id']}.csv"
        if not csv.exists():
            print(f"  skip {ds['id']}: {csv.relative_to(ROOT)} not found")
            continue
        df = pd.read_csv(csv, dtype={"period": str})
        validate_tidy(df, ds["id"])
        if ds["chart"] == "map":  # one marker per row
            values = {"rows": df.rename(columns={"category": "name"}).drop(columns=["unit"]).to_dict("records")}
        else:
            periods, series = to_series(df)
            values = {"periods": periods, "series": series}
        src = sources[ds["source"]]
        write_json({
            **ds,
            "unit": df["unit"].iloc[0],
            "source": {k: src.get(k) for k in ("id", "name", "publisher", "url", "terms")},
            "provenance": provenance(csv),
            **values,
        }, SITE_DATA_DIR / f"{ds['id']}.json")
        built[ds["id"]] = input_sources(csv)
        print(f"  built {ds['id']}")

    built_on = date.today().isoformat()
    version = site_version(built_on)
    write_json(version, SITE_DATA_DIR / "version.json")
    print(f"version {version['version']} ({(version['commit'] or 'no commit')[:7]})")

    write_json({
        "built": built_on,
        "sources": [{k: v for k, v in s.items() if k != "downloads"} for s in sources.values()],
        "datasets": [{**ds, "inputs": built[ds["id"]]} for ds in datasets if ds["id"] in built],
        "references": references,
        "gaps": load_gaps(sources, references),
    }, SITE_DATA_DIR / "catalog.json")
    print(f"{len(built)} datasets -> {SITE_DATA_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
