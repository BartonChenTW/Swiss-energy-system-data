"""Validate the catalog and processed data; optionally check that every URL still resolves.

    python -m pipeline.check            # schema, cross-references, processed files
    python -m pipeline.check --links    # also request every url in the catalog

Exits non-zero on any error, so it can gate CI.
"""
import argparse
import sys

import pandas as pd
import requests

from .changelog import site_version
from .common import PROCESSED_DIR, ROOT, load_catalog, validate_tidy


def check_processed(datasets: list) -> list[str]:
    errors = []
    registered = {d["id"] for d in datasets}
    for d in datasets:
        csv = PROCESSED_DIR / f"{d['id']}.csv"
        if not csv.exists():
            errors.append(f"{d['id']}: {csv.relative_to(ROOT)} missing")
            continue
        try:
            validate_tidy(pd.read_csv(csv), d["id"])
        except ValueError as e:
            errors.append(str(e))
        if d["status"] == "official" and not csv.with_suffix(".meta.json").exists():
            errors.append(f"{d['id']}: status official but no provenance (.meta.json); re-run its processor")
    for csv in PROCESSED_DIR.rglob("*.csv"):
        dataset_id = csv.relative_to(PROCESSED_DIR).with_suffix("").as_posix()
        if dataset_id not in registered:
            errors.append(f"{dataset_id}: CSV exists but is not registered in catalog/datasets.yml")
    return errors


def check_links(sources: dict, references: list) -> list[str]:
    urls = {}
    for s in sources.values():
        urls[s["url"]] = f"sources[{s['id']}]"
        for d in s.get("downloads") or []:
            urls[d["url"]] = f"sources[{s['id']}].downloads"
    for r in references:
        urls[r["url"]] = f"references[{r['id']}]"

    errors = []
    headers = {  # some sites (e.g. empa.ch) reject non-browser user agents
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "en",
    }
    for url, where in urls.items():
        try:
            r = requests.head(url, timeout=30, allow_redirects=True, headers=headers)
            if r.status_code >= 400:  # some servers reject HEAD
                r = requests.get(url, timeout=30, allow_redirects=True, headers=headers, stream=True)
            status = r.status_code
        except requests.RequestException as e:
            status = type(e).__name__
        ok = isinstance(status, int) and status < 400
        print(f"  {'ok ' if ok else 'ERR'} {status} {url}")
        if not ok:
            errors.append(f"{where}: {url} -> {status}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--links", action="store_true", help="also check that every URL resolves")
    args = parser.parse_args()

    try:
        sources, datasets, references = load_catalog()
    except ValueError as e:
        sys.exit(str(e))
    print(f"catalog ok: {len(sources)} sources, {len(datasets)} datasets, {len(references)} references")

    errors = check_processed(datasets)
    try:
        print(f"changelog ok: version {site_version('')['version']}")
    except ValueError as e:
        errors.append(str(e))
    if args.links:
        errors += check_links(sources, references)
    if errors:
        sys.exit("Errors:\n  " + "\n  ".join(errors))
    print("all checks passed")


if __name__ == "__main__":
    main()
