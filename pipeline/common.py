"""Shared paths, catalog loading/validation, the tidy-data contract and provenance."""
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "catalog"
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
SITE_DATA_DIR = ROOT / "docs" / "data"

TIDY_COLUMNS = ["year", "category", "value", "unit"]
MANIFEST_NAME = "_manifest.json"

# Controlled vocabulary, documented in catalog/README.md
THEMES = {"national", "buildings", "electricity", "renewables", "heat", "mobility",
          "emissions", "prices", "scenarios", "general"}
REFERENCE_TYPES = {"report", "standard", "website", "dashboard", "tool", "model", "portal"}
CHART_TYPES = {"line", "stacked-area", "stacked-bar", "hbar"}
PALETTES = {"sequential"}  # optional; default is the categorical palette
STATUSES = {"official", "sample"}
COVERAGES = {"national", "regional"}  # regional datasets also name their `region`
# Optional `ev_profile` block on references: the EV profile data study on the Mobility page
EV_REGIONS = {"Switzerland", "Europe", "World"}
EV_DATA = {"sessions", "load", "driving", "status", "synthetic"}
EV_ACCESS = {"open", "registration", "restricted"}
EV_FIELDS = {"region", "data", "coverage", "resolution", "access", "licence"}

REQUIRED = {
    "sources": ["id", "name", "publisher", "theme", "url", "terms"],
    "datasets": ["id", "title", "description", "source", "chart", "status", "coverage"],
    "references": ["id", "type", "title", "publisher", "url", "themes", "checked"],
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---------- catalog ----------

def load_yaml(name: str) -> dict:
    with open(CATALOG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def catalog_errors(sources: list, datasets: list, references: list) -> list[str]:
    """Return every schema problem in the catalog (empty list = valid)."""
    errors = []

    def check(kind, entries):
        seen = set()
        for i, e in enumerate(entries):
            label = f"{kind}[{e.get('id', i)}]"
            for field in REQUIRED[kind]:
                if e.get(field) in (None, "", []):
                    errors.append(f"{label}: missing '{field}'")
            if e.get("id") in seen:
                errors.append(f"{label}: duplicate id")
            seen.add(e.get("id"))
        return seen

    source_ids = check("sources", sources)
    check("datasets", datasets)
    check("references", references)

    for s in sources:
        if s.get("theme") not in THEMES:
            errors.append(f"sources[{s['id']}]: unknown theme {s.get('theme')!r}")
        for d in s.get("downloads") or []:
            if not d.get("url") or not d.get("filename"):
                errors.append(f"sources[{s['id']}]: each download needs url and filename")
    for d in datasets:
        if d.get("source") not in source_ids:
            errors.append(f"datasets[{d['id']}]: unknown source {d.get('source')!r}")
        if d.get("chart") not in CHART_TYPES:
            errors.append(f"datasets[{d['id']}]: unknown chart {d.get('chart')!r}")
        if d.get("status") not in STATUSES:
            errors.append(f"datasets[{d['id']}]: unknown status {d.get('status')!r}")
        if d.get("coverage") not in COVERAGES:
            errors.append(f"datasets[{d['id']}]: unknown coverage {d.get('coverage')!r}")
        if (d.get("coverage") == "regional") != bool(d.get("region")):
            errors.append(f"datasets[{d['id']}]: 'region' is required for regional coverage and only then")
        if d.get("palette") not in (None, *PALETTES):
            errors.append(f"datasets[{d['id']}]: unknown palette {d.get('palette')!r}")
        if d.get("id", "").split("/")[0] not in THEMES:
            errors.append(f"datasets[{d['id']}]: id must start with a theme folder")
    for r in references:
        if r.get("type") not in REFERENCE_TYPES:
            errors.append(f"references[{r['id']}]: unknown type {r.get('type')!r}")
        for t in r.get("themes") or []:
            if t not in THEMES:
                errors.append(f"references[{r['id']}]: unknown theme {t!r}")
        for sid in r.get("related_sources") or []:
            if sid not in source_ids:
                errors.append(f"references[{r['id']}]: unknown related source {sid!r}")
        if not isinstance(r.get("checked"), date):
            errors.append(f"references[{r['id']}]: 'checked' must be a YYYY-MM-DD date")
        if "ev_profile" in r:
            ev = r["ev_profile"] or {}
            missing = EV_FIELDS - {k for k, v in ev.items() if v not in (None, "", [])}
            if missing:
                errors.append(f"references[{r['id']}]: ev_profile missing {sorted(missing)}")
            if ev.get("region") not in EV_REGIONS:
                errors.append(f"references[{r['id']}]: unknown ev_profile region {ev.get('region')!r}")
            if ev.get("access") not in EV_ACCESS:
                errors.append(f"references[{r['id']}]: unknown ev_profile access {ev.get('access')!r}")
            for t in ev.get("data") or []:
                if t not in EV_DATA:
                    errors.append(f"references[{r['id']}]: unknown ev_profile data type {t!r}")
    return errors


def load_catalog() -> tuple[dict, list, list]:
    """Return (sources by id, datasets, references); raise if the catalog is invalid."""
    sources = load_yaml("sources.yml")["sources"]
    datasets = load_yaml("datasets.yml")["datasets"]
    references = load_yaml("references.yml")["references"]
    errors = catalog_errors(sources, datasets, references)
    if errors:
        raise ValueError("Invalid catalog:\n  " + "\n  ".join(errors))
    return {s["id"]: s for s in sources}, datasets, references


# ---------- raw files & provenance ----------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(source_dir: Path) -> dict:
    path = source_dir / MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_manifest(source_dir: Path, manifest: dict) -> None:
    (source_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def input_record(path: Path) -> dict:
    """Provenance of one raw input: the fetch manifest entry, or file facts for manual downloads."""
    entry = read_manifest(path.parent).get(path.name)
    if entry:
        return {"file": str(path.relative_to(ROOT).as_posix()), **entry}
    return {
        "file": str(path.relative_to(ROOT).as_posix()),
        "url": None,
        "retrieved": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "sha256": sha256(path),
        "note": "not in fetch manifest (placed manually)",
    }


# ---------- tidy data ----------

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


def write_tidy(df: pd.DataFrame, dataset_id: str, inputs: list[Path], processor: str, notes: str | None = None) -> Path:
    """Validate and write data/processed/<dataset_id>.csv plus its .meta.json provenance record."""
    df = df[TIDY_COLUMNS].reset_index(drop=True)
    df["year"] = df["year"].astype(int)
    validate_tidy(df, dataset_id)
    path = PROCESSED_DIR / f"{dataset_id}.csv"
    meta_path = path.with_suffix(".meta.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_text = df.to_csv(index=False, lineterminator="\n")
    inputs = [input_record(p) for p in inputs]

    # Unchanged output from unchanged inputs: keep the old record so reruns don't create diffs.
    if path.exists() and meta_path.exists() and path.read_text(encoding="utf-8") == csv_text:
        old = json.loads(meta_path.read_text(encoding="utf-8"))
        if [i.get("sha256") for i in old.get("inputs", [])] == [i.get("sha256") for i in inputs]:
            print(f"  unchanged {path.relative_to(ROOT)}")
            return path

    path.write_text(csv_text, encoding="utf-8", newline="\n")
    meta = {
        "dataset": dataset_id,
        "processor": processor,
        "generated": now_utc(),
        "rows": len(df),
        "years": [int(df["year"].min()), int(df["year"].max())],
        "inputs": inputs,
    }
    if notes:
        meta["notes"] = notes
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)} ({len(df)} rows, {meta['years'][0]}â€“{meta['years'][1]})")
    return path
